# TM1 Governance Suite — Claude Code Project Brief

## What This Project Is

A Python/Flask web application running on an Ubuntu 24.04 host that provides governance,
visibility, and model-build tooling for an IBM Planning Analytics (TM1 V12) environment.

The suite has four distinct tools:

| Tool | Status | Entry Point |
|---|---|---|
| **Model Builder** | WIP | `model_builder/` |
| **CubeMap** (cube lineage diagram) | Working | `cube_map/` |
| **PAW Tree** (workbook explorer) | Working | `paw_tree/` |
| **Health Monitor** (ops dashboard) | In progress | `health_monitor/` |

All tools share a single Flask server (`app.py`) and common connection helpers in `core/`.

---

## Infrastructure — Read This First

### Host Machine (Ubuntu 24.04)
- Runs this Python app, Flask server, and Authentik (SSO used only for PAW login)
- IP: `192.168.1.171` (Authentik listens on port 9000)
- All development happens here

### VM1 — RHEL (bridged, fixed IP: `192.168.1.223`)
- Runs IBM Planning Analytics Workspace (PAW)
- PAW listens on port 80 (HTTP)
- Auth: Authentik OAuth2 PKCE flow

### VM2 — Windows (bridged, fixed IP: `192.168.1.178`)
- Runs TM1 Server V12 (IBM Planning Analytics on-prem)
- TM1 REST API on port 4444
- Database name: `TM1 Governance`

All three communicate over a bridged local network. No internet routing required.

---

## Authentication Patterns

### TM1 Server (`core/tm1_connect.py`)
OAuth2 client credentials flow against TM1's own auth endpoint:
```
POST http://192.168.1.178:4444/tm1/auth/v1/session
  auth=(client_id, client_secret)
  body={User: 'akadmin'}
→ returns TM1SessionId cookie
```
Session object has a `.base_url` attribute set to the database API root.

### PAW (`core/paw_connect.py`)
Full Authentik OAuth2 PKCE flow — 6 steps:
1. GET PAW `/login` → redirects to Authentik with code_challenge
2. POST Authentik username to flow executor
3. POST Authentik password to flow executor
4. GET Authentik authorize endpoint (prompt=login stripped)
5. GET consent flow → returns redirect with OAuth code
6. GET PAW `/login?code=...` → sets `paSession` + `ba-sso-csrf` cookies

All subsequent PAW API calls need:
- Cookie: `paSession` (automatic via session)
- Header: `ba-sso-authenticity: <value of ba-sso-csrf cookie>`

PAW Content Services base URL: `http://192.168.1.223/pacontent/v1/`

---

## Project Structure

```
tm1-governance/
├── core/                          # Shared connection helpers
│   ├── __init__.py
│   ├── tm1_connect.py             # TM1 REST session (raw requests)
│   ├── tm1py_connect.py           # TM1py session (higher-level)
│   ├── paw_connect.py             # PAW Authentik PKCE auth
│   ├── groups.py                  # Live group/permission resolver (TODO)
│   └── groups.json                # Group display annotations (colour, tm1_access)
│
├── model_builder/                 # Tool 1: Build/rebuild TM1 model (WIP)
│   ├── build_gbl_model.py         # Master runner — GBL layer
│   ├── build_cst_model.py         # Master runner — CST layer
│   ├── cleanup_gbl_model.py
│   ├── cleanup_cst_model.py
│   ├── ti_lint.py                 # TI code linter/formatter
│   ├── pro_to_json.py             # Convert .pro files to JSON
│   ├── gbl/                       # create_gbl_*.py scripts
│   ├── cst/                       # create_cst_*.py scripts
│   ├── ti/                        # TI JSON definitions + deploy scripts
│   └── pro_files/                 # Bedrock .pro files
│
├── cube_map/                      # Tool 2: Cube lineage visualiser
│   ├── extract_tm1_model.py       # Pulls metadata from TM1 → JSON cache
│   ├── tm1_model.json             # Generated cache — do not edit manually
│   └── static/
│       └── tm1_cube_lineage.html  # Self-contained Cytoscape diagram
│
├── paw_tree/                      # Tool 3: PAW workbook tree explorer
│   ├── paw_governance_explorer.jsx  # React prototype — not yet integrated
│   └── static/
│       └── tm1_paw_tree.html
│
├── health_monitor/                # Tool 4: Ops health dashboard
│   ├── backend.py                 # Flask routes, APScheduler, DuckDB (TODO)
│   └── static/
│       └── tm1_health_monitor.html
│
├── app.py                         # Flask entry point — mounts all tools
├── requirements.txt
├── CLAUDE.md                      # This file
├── .env                           # Connection secrets — NOT in git
├── .env.example                   # Placeholder template — safe to commit
│
├── docs/                          # Reference documents
│   ├── TM1_Governance_Suite_Design.docx
│   ├── TM1_Build_Script_Reference.docx
│   ├── tm1_health_monitor_requirements.docx
│   └── PAW_Field_Reference.docx
│
└── archive/                       # Legacy/backup files — ignore
```

---

## Flask Routes (app.py)

| Method | Path | Description |
|---|---|---|
| GET | `/` | Serve CubeMap HTML |
| GET | `/workbook-tree` | Serve PAW Tree HTML |
| GET | `/health-monitor` | Serve Health Monitor HTML |
| GET | `/api/model` | Return cached `cube_map/tm1_model.json` |
| POST | `/api/refresh` | Re-extract model from TM1, update cache |
| GET | `/api/status` | Server + last-refresh info |
| GET | `/api/groups` | Return resolved groups (reads `core/groups.json`) |
| GET | `/api/paw/tree` | Walk PAW folder tree, return JSON |

---

## Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Web server | Flask 3.1 | Serves all tools, exposes REST API |
| TM1 connection | TM1py 2.2.4 | Higher-level API wrapper |
| TM1 raw REST | requests 2.32 | Used for TI deploy, auth token |
| PAW auth | requests + PKCE | 6-step Authentik OAuth2 flow |
| Config | python-dotenv 1.1 | Loads `.env` at startup |
| Diagrams (frontend) | Cytoscape.js 3.33.1 + Dagre | CubeMap graph rendering |
| Frontend | Vanilla HTML/CSS/JS | No framework — self-contained files |
| Health monitor DB | DuckDB | Session history, user activity |
| Scheduling | APScheduler | 60-second auto-refresh |
| Analytics (planned) | pandas + numpy | Governance reports |
| Dashboard (planned) | Streamlit | Governance dashboard UI |

---

## Model Builder — Layer Dependency Order

**Build order (fresh environment):**
1. `model_builder/ti/create_json_ti_meta_data_gbl_period.py` → generates TI JSON
2. `model_builder/ti/create_ti_meta_data_gbl_period.py` → deploys and runs Period TI
3. `model_builder/build_gbl_model.py` → builds all GBL dimensions/cubes
4. `model_builder/build_cst_model.py` → builds all CST dimensions/cubes

**Cleanup order (reverse dependency — CST first, then GBL):**
1. `model_builder/cleanup_cst_model.py`
2. `model_builder/cleanup_gbl_model.py`

GBL = Global shared infrastructure (Account, Version, Department, Currency, Assumptions).
CST = Costing module — depends on GBL. Never delete GBL while CST cubes exist.

---

## Groups & Security

`core/groups.json` stores display annotations only (colour, tm1_access level).
Live group membership and folder permissions are resolved at runtime via:
- **PAW Content Services API** — source of truth for groups, members, folder permissions, book ownership, and user display names
- **TM1 REST API** — source of truth for active sessions and connected client list

`core/groups.py` merges both sources with the annotations in `groups.json` (not yet built).

### Identity Provider Independence

**The governance suite must not depend on any specific identity provider.**
Authentik (or any future SSO system — Azure AD, Okta, etc.) is used **only** to obtain an
authenticated PAW session. Once the session is established, all user data comes exclusively
from PAW Content Services and the TM1 REST API:

| Data | Source |
|---|---|
| User display names | PAW `system_properties.created_user_pretty_name` etc. |
| Book ownership | PAW asset `system_properties` |
| Last opened by / date | PAW `used_user_pretty_name` / `used_date` |
| Folder permissions | PAW Content Services API |
| Active sessions / clients | TM1 REST API |
| Historical snapshots | DuckDB (written by Health Monitor) |

Never call the Authentik API to resolve user identity, group membership, or display names.
If the SSO provider changes, only `core/paw_connect.py` should need to change.

---

## Key Conventions

- **Config lives in `.env`** — never hardcode IPs or credentials in source files
- **`.env.example`** is the safe-to-commit template — keep it up to date when adding new vars
- **`tm1_connect.py`** — use for raw REST calls (TI deploy, auth)
- **`tm1py_connect.py`** — use for all dimension/cube build operations
- **HTML tools are self-contained** — they can run standalone with embedded sample data; the Flask backend adds live data
- **`cube_map/tm1_model.json`** is a generated cache — never edit manually, always regenerate via `/api/refresh`
- **Python 3.12** — ships with Ubuntu 24.04, all scripts target this version
- **Virtual environment** at `venv/` — always activate before running scripts
- **All scripts** use `sys.path.insert(0, str(Path(__file__).resolve().parent...))` (dynamic, relative to `__file__`) and import from `core.*`

---

## Running the App

```bash
cd ~/apps/tm1_governance
./run.sh
```

Then open:
- http://localhost:8080 — CubeMap
- http://localhost:8080/workbook-tree — PAW Tree
- http://localhost:8080/health-monitor — Health Monitor

---

## Current WIP / Known Issues

- Model Builder CST scripts not yet complete
- Health Monitor backend (`health_monitor/backend.py`) not yet built — HTML renders with sample data
- `core/groups.py` live resolver not yet built — `api/groups` currently reads static `core/groups.json`
- `paw_tree/paw_governance_explorer.jsx` is a React prototype — not integrated into Flask yet

---

## Documents (in `docs/`)

| File | Contents |
|---|---|
| `TM1_Governance_Suite_Design.docx` | Full technical design, architecture, component specs |
| `TM1_Build_Script_Reference.docx` | Every build script described, build/rebuild sequences |
| `tm1_health_monitor_requirements.docx` | Health Monitor tab-by-tab requirements spec |
| `PAW_Field_Reference.docx` | PAW Content Services API field reference |

---

## TODO

- [ ] Complete CST Model Builder scripts
- [ ] Build `core/groups.py` live PAW + TM1 group resolver (no Authentik dependency)
- [ ] Build Health Monitor backend (Flask + DuckDB + APScheduler)
- [ ] Move `core/groups.json` to annotations only (strip any live data)
- [ ] Connect `paw_tree/paw_governance_explorer.jsx` into Flask
- [ ] Add GitHub remote backup
- [ ] Set up gunicorn for production
- [ ] Add second monitor to dev setup
