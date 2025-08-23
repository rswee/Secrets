# Secrets

# 🔐 Config Injector – JSON / YAML / Token Replacement

## 📖 Overview

This project provides a **Python-based injector** for GitHub Actions that replaces placeholders in JSON, YAML, and text files with **secrets** and **variables** from your repository or organization.  

It works at the **org level**: every repo can reuse the same injector, only customizing its own mapping file (`mapping.json`) and templates.

---

## ✨ Features
- 🔑 Inject secrets/vars into JSON and YAML files (nested keys supported)  
- 🔄 Replace `${VAR}` tokens in any text file (`.py`, `.md`, `.env`, etc.)  
- 🛠 Supports:  
  - `env:VAR` → use environment variable  
  - `default:VAR:VALUE` → use env if available, otherwise default value  
  - `literal:VALUE` → inject a fixed value  
- 🔒 Logs show masked output (no secret leaks)  
- ✅ Includes a self-test app to verify injections inside CI  

---

## 📂 Repository Layout
```
├─ app/
│  ├─ app.py                 # contains ${API_TOKEN} placeholder
│  └─ main.py                # self-test 
├─ tools/
│  └─ config/
│     ├─ mapping.json      # injection rules
│
scripts
└─ inject_secrets.py   # injector sc
├─ config.template.json
├─ settings.template.yaml
└─ .github/workflows/inject-and-test.yml
```
---

## 📝 Mapping File 
(`tools/config/mapping.json`)
```json
{
  "structured": {
    "config.json": {
      "api.key": "env:API_TOKEN",
      "api.endpoint": "default:API_ENDPOINT:https://example.com"
    },
    "settings.yaml": {
      "service.api.key": "env:API_TOKEN",
      "service.public_url": "default:PUBLIC_URL:https://site.example"
    }
  },
  "tokens": {
    "app/app.py": ["API_TOKEN"]
  },
  "templates": {
    "config.json": "config.template.json",
    "settings.yaml": "settings.template.yaml"
  }
}
```

•	structured → update nested JSON/YAML keys
	•	tokens → replace ${API_TOKEN} in files (e.g. app.py)
	•	templates → use a template if the file doesn’t exist

⸻

📄 Templates

config.template.json
```json
{ "api": { "key": "", "endpoint": "" } }
```

settings.template.yaml
```yml
service:
  api:
    key: ""
  public_url: ""
```


