# TM1 CubeMap — Claude Code Project Brief

**Last updated:** May 2026
**Status:** CubeMap ✅
**Environment:** Ubuntu 24.04 · TM1 V12 on-prem + V11 on-prem

---

## Commands

```bash
# Daily startup
cd ~/apps/tm1_cubemap && ./venv/bin/python app.py

# Production (Gunicorn)
gunicorn -w 4 -b 0.0.0.0:8083 app:app

# TI linting
python3 ti_lint.py <path/to/process.ti>
```

---

## Architecture

```text
Browser (http://localhost:8083)
    └── Flask app.py
            ├── core/tm1_connect.py       → raw requests.Session (V12 cookie auth / V11 basic auth)
            ├── core/tm1py_connect.py     → TM1Service (monkey-patched for V12 on-prem)
            ├── core/servers.json         → TM1 instance + database registry
            ├── extract_tm1_model.py      → writes cube_map/tm1_model.json (cache)
            └── cube_map/static/tm1_cube_lineage.html → single-page frontend (Cytoscape.js)
```

**Two connection methods — this is intentional:**

- `tm1_connect` (raw requests) → lightweight Flask endpoints, fast, minimal deps
- `tm1py_connect` (TM1Service) → heavy extraction only (rules, attributes, DB() scanning)

---

## Project Structure

```text
~/apps/tm1_cubemap/
├── app.py                        # Flask server — all routes
├── core/
│   ├── tm1_connect.py            # Raw TM1 session (multi-server)
│   ├── tm1py_connect.py          # TM1py + V12 monkey-patches
│   ├── paw_connect.py            # PAW Authentik PKCE auth (unused by CubeMap)
│   ├── groups.json               # Role definitions
│   └── report_store.py           # Report store helpers
├── cube_map/
│   ├── extract_tm1_model.py      # Full model extraction → JSON
│   ├── tm1_model.json            # Generated cache (includes _tags)
│   ├── tags.json                 # Legacy tag store (deprecated, kept for migration)
│   ├── servers.json              # TM1 instance registry (gitignored)
│   ├── servers.json.example      # Template for servers.json
│   ├── python_sources.json       # Manually maintained Python ETL script registry
│   ├── scan_python_edges.py      # Scans Python scripts for cube refs
│   ├── scan_ti_edges.py          # Scans TI processes for cube refs
│   ├── layouts/                  # Saved node position layouts
│   ├── static/
│   │   └── tm1_cube_lineage.html # Frontend (Cytoscape.js, single file, 6.5k lines)
│   └── TEMP/                     # Temporary extraction artifacts
├── .env                          # PORT setting (gitignored)
├── .env.example                  # Template for .env
├── servers.json                  # Active server config (gitignored)
├── active_server.json            # Currently selected server (auto-generated)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Flask Routes

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/` | CubeMap HTML frontend |
| GET | `/api/model` | Cached model JSON (cubes + _tags) |
| POST | `/api/refresh` | Background TM1 extraction (lock + 409 guard) |
| GET | `/api/status` | Server info, last refresh status |
| GET | `/api/servers` | List configured TM1 instances + databases |
| POST | `/api/servers/active` | Switch active instance/database |
| GET | `/api/tags` | Get tags (reads from model _tags / tags.json) |
| POST | `/api/tags` | Save tags (writes to both model file + tags.json) |
| GET | `/api/layouts` | List saved layout names |
| GET | `/api/layouts/<name>` | Get layout positions |
| POST | `/api/layouts/<name>` | Save layout positions |
| DELETE | `/api/layouts/<name>` | Delete layout |
| GET/POST | `/api/tm1/performance-monitor` | V11 Performance Monitor toggle |
| GET | `/api/tm1/cubes` | Live cube list from TM1 |
| GET | `/api/tm1/views` | Live views per cube |
| GET | `/api/tm1/dimensions` | Live dimensions per cube |
| GET | `/api/tm1/subsets` | Live subsets per dimension |
| GET | `/api/tm1/subset_info` | Subset metadata |
| GET | `/api/tm1/views_with_subset` | Views with subset details |
| GET | `/api/tm1/mdx` | MDX expression execution |
| GET | `/api/config` | Client-safe config (currently empty) |
| GET | `/api/groups` | Role definitions from groups.json |
| GET/POST/DELETE | `/api/specs/<path:obj_id>` | AI-generated object descriptions |
| GET | `/api/specs/prompt/<path:obj_id>` | AI prompt for generating specs |
| GET | `/api/script/python` | Python ETL script source |
| GET | `/api/script/ti` | TI process script source |
| GET | `/api/module/prompt` | Generate AI module prompt from tagged objects |

---

## Key Conventions

- **TM1 objects:** Ignore anything starting with `}` — these are system objects.
- **Credentials:** All in `.env` (PORT only) + `servers.json` — never hardcode, never log.
- **Non-system filter:** `not name.startswith('}')` — applied everywhere.
- **Tags:** Stored inside `tm1_model.json` as `_tags` to survive refresh. `tags.json` is deprecated but preserved as fallback.
- **Server switching:** `POST /api/servers/active` changes the active profile in `active_server.json`. Tags are cleared in memory (server-specific) then reloaded from the model.
- **Architecture Score:** Removed from UI — scoring logic kept in extractor for future use.

---

## Critical Gotchas

- **TM1py V12 patches** — `tm1py_connect.py` uses a context manager (`_v12_patches`) that applies monkey-patches before every `TM1Service` construction and restores originals afterward. Without these patches, TM1py fails on V12 on-prem. Do not remove.
- **Session auth** — `tm1_connect.py` manages per-server credential caches. V12 uses `TM1SessionId` cookie (OAuth2 client_id/client_secret). V11 uses Basic auth with self-signed certs (`verify=False`).
- **Per-server session cache** — Sessions are cached by `(address, port, db_name)` tuple with 10-minute TTL. `invalidate_session()` clears only the active server's cache.
- **Background refresh thread** — uses a lock + `already_running` 409 guard. Do not make the refresh endpoint synchronous.
- **Python ETL nodes** — `cube_map/python_sources.json` is a manually maintained registry. Refresh re-scans whatever is listed — it does NOT auto-detect retired scripts. Remove entries manually when scripts are retired.
- **TI edges** — `scan_ti_edges.py` is called during refresh to extract cube read/write edges from TI processes.
- **Tags persist via model file** — `POST /api/tags` writes to both `tags.json` AND injects `_tags` into `tm1_model.json`. On refresh, `do_refresh()` preserves `_tags` from `tags.json`. When loading, `/api/model` injects `_tags` from `tags.json` if not embedded yet. This triple-redundancy ensures tags never get lost.
- **TDZ in frontend** — All `let`/`const` declarations referenced by functions called during script init must be declared before those calls. The `_sidebarSelectedTag` variable is declared before `buildSidebar()` to avoid temporal dead zone crashes.
- **Frontend is a single file** — `cube_map/static/tm1_cube_lineage.html` (~6.5k lines) contains all HTML, CSS, JS (including embedded Cytoscape.js and Dagre). The first two `<script>` blocks are the minified libraries; the third `<script>` (line ~4738) is the application code.

---

## TODO

### High Priority

- [ ] Cache TM1 sessions (5–10 min TTL) — biggest performance win (partially done: per-server cache exists)

### Medium Priority

- [ ] Add `.claude/settings.json` with deny rules for `.env`, `servers.json`
- [ ] Health Monitor backend (DuckDB + APScheduler) — in stub state
- [ ] Move `.env` loading to app startup, inject into `app.config`
- [ ] Add rate-limiting on `/api/refresh`
- [ ] Add static cache headers (`flask-compress` already added)

### Nice to Have

- [ ] Move `groups.json` to annotations-only; build `core/groups.py` live resolver
- [ ] Gunicorn + nginx for shared deployments
- [ ] Prometheus `/metrics` endpoint
- [ ] Structured JSON logging option
- [ ] Cloud (IBM PAaaS) auth support — new `auth` type in servers.json

---

## Roadmap

### CubeMap — Edge Classification

- [x] Split rules text at `FEEDERS;` — only scan calc section for DB() edges; feeder section DB() = performance hints
- [x] Classify edges: `rule_calc` (before FEEDERS;) vs `rule_feeder` (after FEEDERS;)
- [ ] Classify by measure type: value = flow, rate/driver = lookup
- [x] UI toggle: show/hide feeder edges independently from calc edges
- [x] Save/load named diagram layouts

### CubeMap — Enriched Extraction

- [ ] Extract measure dimension elements → surface in node detail panel
- [ ] TI process edges: which TIs write to each cube → data lineage
- [ ] Chore connections: which chores schedule TIs that touch each cube

### CubeMap — Calculation Trace

- [ ] **Phase 1 — Static trace**: Parse rules text already in model JSON. Extract `DB('SourceCube', ...)` chains. Walk back recursively, max 4–5 levels. Render as collapsible tree.
- [ ] **Phase 2 — AI explanation**: Pass formula tree to Claude API → plain English description. Cache in `rules_analysis/`.

### CubeMap — Inherited Model Support

- [ ] Reverse engineer extractor: pull all metadata from live server → YAML
- [ ] Git baseline on day one for inherited servers
- [ ] AI-assisted analysis: explain rules, find missing feeders, circular refs
