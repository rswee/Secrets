
#!/usr/bin/env python3
import argparse, json, os, pathlib, re, sys

# YAML is optional; only import if we need it
def load_yaml_mod():
    try:
        import yaml
        return yaml
    except Exception:
        sys.exit("PyYAML not installed. Add a step: `pip install pyyaml`.")

def read_text(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""

def write_text(p: pathlib.Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def load_json(p: pathlib.Path):
    return json.loads(read_text(p)) if p.exists() and p.stat().st_size else {}

def dump_json(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"

def load_yaml(p: pathlib.Path):
    yaml = load_yaml_mod()
    txt = read_text(p)
    return yaml.safe_load(txt) if txt.strip() else {}

def dump_yaml(obj) -> str:
    yaml = load_yaml_mod()
    return yaml.safe_dump(obj, sort_keys=False)

def set_path(obj, dotted, value):
    parts = dotted.split(".")
    cur = obj
    for k in parts[:-1]:
        if not isinstance(cur, dict) or k not in cur or not isinstance(cur[k], dict):
            if isinstance(cur, dict):
                cur[k] = {}
            else:
                raise ValueError(f"Parent for '{dotted}' is not a mapping")
        cur = cur[k]
    if not isinstance(cur, dict):
        raise ValueError(f"Parent for '{dotted}' is not a mapping")
    cur[parts[-1]] = value

def expand(spec: str) -> str:
    # Accept "env:NAME" or just "NAME" (env var name)
    if spec.startswith("env:"):
        return os.environ.get(spec[4:], "")
    if spec.startswith("literal:"):
        return spec[len("literal:"):]
    if spec.startswith("default:"):
        _, var, default = spec.split(":", 2)
        return os.environ.get(var, default)
    return os.environ.get(spec, "")

def main():
    ap = argparse.ArgumentParser(description="Inject env values into files (tokens + JSON/YAML).")
    ap.add_argument("--mapping", required=True, help="mapping.json path")
    ap.add_argument("--require-all", action="store_true", help="fail if any referenced env var is missing")
    args = ap.parse_args()

    m = json.loads(pathlib.Path(args.mapping).read_text(encoding="utf-8"))
    env = dict(os.environ)

    # --- Structured (JSON/YAML) ---
    missing = set()
    for relpath, path_map in (m.get("structured") or {}).items():
        p = pathlib.Path(relpath)
        # Optional template fallback
        template = (m.get("templates") or {}).get(relpath)
        if not p.exists() and template:
            t = pathlib.Path(template)
            if t.exists():
                write_text(p, read_text(t))

        suffix = p.suffix.lower()
        if suffix == ".json":
            data = load_json(p)
        elif suffix in (".yml", ".yaml"):
            data = load_yaml(p)
        else:
            sys.exit(f"Structured only supports JSON/YAML; got {relpath}")

        for dotted, spec in path_map.items():
            val = expand(spec)
            if val == "" and spec.startswith("env:"):
                missing.add(spec.split(":",1)[1])
            set_path(data, dotted, val)

        if suffix == ".json":
            write_text(p, dump_json(data))
        else:
            write_text(p, dump_yaml(data))

    # --- Token replacement in arbitrary text files ---
    for relpath, vars_list in (m.get("tokens") or {}).items():
        p = pathlib.Path(relpath)
        if not p.exists():
            continue
        content = read_text(p)
        for var in vars_list:
            val = env.get(var)
            if val is None and args.require_all:
                missing.add(var)
            content = re.sub(rf"\$\{{{re.escape(var)}\}}", val or "", content)
        write_text(p, content)

    if args.require_all and missing:
        sys.stderr.write("Missing required env(s): " + ", ".join(sorted(missing)) + "\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
