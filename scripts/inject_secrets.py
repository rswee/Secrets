#!/usr/bin/env python3
import argparse, json, os, pathlib, sys

def set_path(obj, dotted, value):
    cur = obj
    parts = dotted.split(".")
    for k in parts[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[parts[-1]] = value

def load_json(path: pathlib.Path) -> dict:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    ap = argparse.ArgumentParser(description="Inject env values into JSON using a mapping file.")
    ap.add_argument("--file", default="config.json")
    ap.add_argument("--template", default="config.template.json")
    ap.add_argument("--map", required=True, help="JSON file: { 'json.path': 'ENV_VAR', ... }")
    args = ap.parse_args()

    target = pathlib.Path(args.file)
    template = pathlib.Path(args.template)
    mapping = pathlib.Path(args.map)

    if not mapping.exists():
        sys.stderr.write(f"Mapping not found: {mapping}\n")
        sys.exit(2)

    map_data = json.loads(mapping.read_text(encoding="utf-8"))
    data = load_json(target) or load_json(template) or {}

    for jpath, envname in map_data.items():
        val = os.environ.get(envname)
        if val is not None:
            set_path(data, jpath, val)

    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
