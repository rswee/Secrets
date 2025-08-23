# app/main.py
import json, os, sys, pathlib, runpy

# YAML optional: only needed if you use settings.yaml
try:
    import yaml  # pip install pyyaml
except Exception:
    yaml = None

ROOT = pathlib.Path(__file__).resolve().parents[1]

def load_json(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() and p.stat().st_size else {}

def load_yaml(p: pathlib.Path):
    if yaml is None:
        raise SystemExit("PyYAML not installed (needed to read settings.yaml).")
    text = p.read_text(encoding="utf-8") if p.exists() else ""
    return yaml.safe_load(text) if text.strip() else {}

def mask(s: str, keep_last=4) -> str:
    if not s: return ""
    return ("*" * max(0, len(s) - keep_last)) + s[-keep_last:]

def assert_non_empty(val, msg):
    if not val: raise AssertionError(msg)

def main() -> int:
    problems = []

    # 1) config.json (structured injection)
    cfg_path = ROOT / "config.json"
    cfg = load_json(cfg_path)
    try:
        api_key = cfg.get("api", {}).get("key")
        api_ep  = cfg.get("api", {}).get("endpoint")
        assert_non_empty(api_key, "config.json: api.key missing/empty")
        assert_non_empty(api_ep,  "config.json: api.endpoint missing/empty")
    except AssertionError as e:
        problems.append(str(e))

    # 2) settings.yaml (structured injection)
    settings_path = ROOT / "settings.yaml"
    if settings_path.exists():
        try:
            st = load_yaml(settings_path)
            s_key = (((st.get("service") or {}).get("api") or {}).get("key"))
            s_url = ((st.get("service") or {}).get("public_url"))
            assert_non_empty(s_key, "settings.yaml: service.api.key missing/empty")
            assert_non_empty(s_url, "settings.yaml: service.public_url missing/empty")
        except AssertionError as e:
            problems.append(str(e))
        except SystemExit as e:
            problems.append(str(e))

    # 3) Token replacement in app/app.py (no package needed)
    try:
        ns = runpy.run_path(str(ROOT / "app" / "app.py"))
        api_token = ns.get("API_TOKEN", "")
        assert_non_empty(api_token, "app/app.py: API_TOKEN placeholder not replaced")
    except Exception as e:
        problems.append(f"app/app.py load failed: {e}")

    # 4) ENV fall-back check
    env_token = os.getenv("API_TOKEN")
    if not env_token:
        problems.append("ENV: API_TOKEN not present (consider passing in job env)")

    if problems:
        print("Secret wiring check FAILED:")
        for p in problems: print(" -", p)
        return 1

    print("Secret wiring OK")
    print("config.json → api.key:", mask(api_key))
    print("config.json → api.endpoint:", api_ep)
    if settings_path.exists():
        print("settings.yaml → service.api.key:", mask(s_key))
        print("settings.yaml → service.public_url:", s_url)
    print("app/app.py → API_TOKEN:", mask(api_token))
    print("ENV → API_TOKEN:", mask(env_token))
    return 0

if __name__ == "__main__":
    sys.exit(main())
