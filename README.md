# TM1 CubeMap

Interactive data lineage diagram for TM1 / Planning Analytics **on-prem** (V11 recommended, V12 also supported).

Visualises cubes, rules, TI processes, and Python ETL scripts as a navigable graph. Click any node to inspect rules, script code, dimensions, measures, and data flow. Switch between TM1 instances and databases from the toolbar without restarting.

---

## Quick Start (Docker)

**Prerequisites:** Docker and a TM1 V11 or V12 on-prem server.

```bash
mkdir tm1-cubemap && cd tm1-cubemap
curl -sSLO https://raw.githubusercontent.com/falconbi/tm1_cubemap/main/docker-compose.yml
docker compose up -d
```

Open **[http://localhost:8084](http://localhost:8084)**. The first-run setup form walks you through adding your TM1 servers. No files to edit manually.

Or if you cloned the repo:

```bash
cd tm1-cubemap
docker compose up -d
```

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

Each entry is a TM1 server with one or more databases. **V11 on-prem** is the primary target; V12 also works.

See [`servers.json.example`](./servers.json.example) for a complete template.

| Field | Required | Description |
|---|---|---|
| `name` | yes | Display name in the instance dropdown |
| `address` | yes | TM1 server IP or hostname |
| `auth` | yes | `"v11"` (Basic auth) or `"v12"` (OAuth2 client credentials) |
| `user` | yes | Admin username |
| `password` | V11 only | Admin password |
| `client_id` / `client_secret` | V12 only | From your TM1 OAuth2 client registration |
| `databases[]` | yes | One or more databases on this server |
| `databases[].name` | yes | TM1 database (cube) name |
| `databases[].port` | yes | TM1 REST API port (typically 8000–8015 for V11, 4444 for V12) |

**V11 example:**
```json
{"name": "Prod", "address": "10.0.0.50", "auth": "v11",
 "user": "admin", "password": "apple",
 "databases": [{"name": "Finance", "port": 8000}]}
```

**V12 example:**
```json
{"name": "Prod V12", "address": "10.0.0.51", "auth": "v12",
 "client_id": "abc", "client_secret": "xyz", "user": "admin",
 "databases": [{"name": "Finance", "port": 4444}]}
```

> **Cloud (IBM Planning Analytics / PAaaS / SAP Analytics Cloud):** Not supported. If you need cloud support, the `auth` field would need a new type (e.g. `"paoc"` or `"cloud"`) with appropriate token-based authentication. Contributions welcome — see `core/tm1_connect.py` for the auth dispatch point.

### .env

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8083` | Flask server port (inside container; Docker exposes on 8084) |

---

## Requirements

- TM1 / Planning Analytics **on-prem** — V11 recommended, V12 also supported
- V11: admin username and password (Basic auth)
- V12: OAuth2 client credentials (`client_id` / `client_secret`) + admin username
- REST API must be enabled on the TM1 server

No SSO, no PAW, no Authentik, no cloud required.

### Compatibility

| Environment | Status | Notes |
|---|---|---|
| **On-prem V11 + Basic auth** | **✅ Supported (primary)** | `auth: "v11"` in servers.json |
| On-prem V12 + OAuth2 | ✅ Supported | `auth: "v12"` in servers.json |
| Cloud (IBM PAaaS / SAP AC) | ❌ Not supported | See servers.json docs for guidance |

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
