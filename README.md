# TM1 CubeMap

Interactive data lineage diagram for IBM TM1 / Planning Analytics (V11 and V12 on-prem).

Visualises cubes, rules, TI processes, and Python ETL scripts as a navigable graph. Click any node to inspect rules, script code, dimensions, measures, and data flow. Switch between TM1 instances and databases from the toolbar without restarting.

---

## Quick Start (Docker)

**Prerequisites:** Docker and a TM1 V11 or V12 on-prem server.

```bash
git clone https://github.com/falconbi/tm1_cubemap.git
cd tm1_cubemap
cp servers.json.example servers.json
# edit servers.json with your TM1 instances
cp .env.example .env
docker compose up --build
```

Open **[http://localhost:8083](http://localhost:8083)** and click **Refresh** to extract your model.

---

## Manual Install (Python)

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp servers.json.example servers.json   # fill in your TM1 instances
cp .env.example .env
python3 app.py
```

---

## Configuration

### servers.json — TM1 instance registry

Supports multiple TM1 instances with V12 OAuth2 and V11 Basic auth:

| Field | Description |
|---|---|
| `name` | Display name shown in the instance dropdown |
| `address` | TM1 server IP or hostname |
| `auth` | `"v12"` for OAuth2 client credentials, `"v11"` for Basic auth |
| `client_id` / `client_secret` | V12 only — from your TM1 OAuth2 client |
| `user` / `password` | V11: admin credentials / V12: username for session |
| `databases[].name` | TM1 database (cube) name |
| `databases[].port` | TM1 REST API port |

### .env

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8083` | Flask server port |

---

## Requirements

- TM1 / Planning Analytics **on-prem** — V11 or V12
- V12: OAuth2 client credentials (`client_id` / `client_secret`)
- V11: admin username and password

No SSO, no PAW, no Authentik required.

### Compatibility

| Environment | Status | Notes |
|---|---|---|
| On-prem V12 + OAuth2 | Supported | `auth: "v12"` in servers.json |
| On-prem V11 + Basic auth | Supported | `auth: "v11"` in servers.json |
| Cloud (IBM PAaaS / SaaS) | Not yet supported | TM1py supports PAoC — new auth type needed |

---

## What it shows

- **Cubes** — all non-system cubes with dimensions, measures, and RAM usage
- **Rules** — DB() references extracted as directed edges between cubes
- **TI Processes** — cube read/write edges, click to view script
- **Python ETL** — registered scripts scanned for cube reads/writes (see `cube_map/python_sources.json`)
- **Tags** — tag any object, generate AI module documentation from tagged sets
- **Server switching** — switch TM1 instance + database from the toolbar
- **Layouts** — save/load named node position layouts
- **Tags persist** — embedded in the model file, survive refresh

---

## Architecture

```text
Browser → Flask (app.py)
            ├── core/tm1_connect.py       → TM1 REST API (fast, raw requests)
            ├── core/tm1py_connect.py     → TM1py (deep extraction — rules, attributes)
            ├── cube_map/extract_tm1_model.py → writes cube_map/tm1_model.json
            └── cube_map/static/tm1_cube_lineage.html → single-page frontend
```

Tags are stored inside `tm1_model.json` as `_tags`, ensuring they survive model re-extraction. Layouts are stored as individual JSON files in `cube_map/layouts/`.
