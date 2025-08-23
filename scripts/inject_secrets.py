#!/usr/bin/env python3
import argparse, json, os, pathlib

def set_path(obj, dotted, value):
    keys = dotted.split(".")
    cur = obj
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="config.json")
    # Repeatable: --set database.password=env:DB_PASSWORD
    ap.add_argument("--set", action="append", default=[], help="path=env:VAR or path=literal:VALUE")
    args = ap.parse_args()

    p = pathlib.Path(args.file)
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    for item in args.__dict__["_get_kwargs"]() if False else args.set:  # keep mypy happy in some setups
        path, spec = item.split("=", 1)
        mode, val = spec.split(":", 1)
        if mode == "env":
            value = os.environ.get(val, "")
        elif mode == "literal":
            value = val
        else:
            raise SystemExit(f"Unknown mode {mode}; use env: or literal:")
        set_path(data, path, value)

    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
