import os
import json
import time
import threading
import requests
import urllib3
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SERVERS_FILE = Path(__file__).parent.parent / "servers.json"
ACTIVE_FILE = Path(__file__).parent.parent / "active_server.json"

SESSION_TTL = 600  # 10 minutes

_state_lock = threading.Lock()
_cache_lock = threading.Lock()
_session_cache = {}  # (address, port, database) -> (session, expiry)


def _load_active_state() -> tuple[int, int]:
    try:
        if ACTIVE_FILE.exists():
            d = json.loads(ACTIVE_FILE.read_text())
            return int(d.get("instance", 0)), int(d.get("db", 0))
    except Exception:
        pass
    return 0, 0


def _save_active_state(instance_idx: int, db_idx: int):
    try:
        ACTIVE_FILE.write_text(json.dumps({"instance": instance_idx, "db": db_idx}))
    except Exception:
        pass


_active_instance_idx, _active_db_idx = _load_active_state()


# ── Server registry ───────────────────────────────────────────────────────────


def load_servers():
    if not SERVERS_FILE.is_file():
        raise RuntimeError(
            "servers.json not found — use the setup form at / or copy servers.json.example and configure"
        )
    return json.loads(SERVERS_FILE.read_text(encoding="utf-8"))


def get_active_profile():
    with _state_lock:
        inst_idx = _active_instance_idx
        db_idx = _active_db_idx
    servers = load_servers()
    inst = servers[inst_idx]
    db = inst["databases"][db_idx]
    return {
        "instance_name": inst["name"],
        "db_name": db["name"],
        "address": inst["address"],
        "port": db["port"],
        "auth": inst.get("auth", "v12"),
        "client_id": inst.get("client_id", ""),
        "client_secret": inst.get("client_secret", ""),
        "user": inst.get("user", "admin"),
        "password": inst.get("password", ""),
    }


def set_active_profile(instance_idx: int, db_idx: int):
    global _active_instance_idx, _active_db_idx
    with _state_lock:
        _active_instance_idx = instance_idx
        _active_db_idx = db_idx
    _save_active_state(instance_idx, db_idx)


# ── Session auth ──────────────────────────────────────────────────────────────


def _new_session(profile: dict) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})

    if profile["auth"] == "v12":
        base = f"http://{profile['address']}:{profile['port']}/tm1"
        r = requests.post(
            f"{base}/auth/v1/session",
            auth=(profile["client_id"], profile["client_secret"]),
            headers={"Content-Type": "application/json"},
            json={"User": profile["user"]},
        )
        r.raise_for_status()
        session.cookies.set("TM1SessionId", r.cookies.get("TM1SessionId"))
        session.base_url = f"{base}/api/v1/Databases('{profile['db_name']}')"

    elif profile["auth"] == "v11":
        base = f"https://{profile['address']}:{profile['port']}"
        session.auth = (profile["user"], profile["password"])
        session.verify = False  # V11 uses self-signed cert
        session.base_url = f"{base}/api/v1"

    else:
        raise ValueError(f"Unknown auth type: {profile['auth']}")

    return session


def get_session() -> requests.Session:
    profile = get_active_profile()
    key = (profile["address"], profile["port"], profile["db_name"])

    with _cache_lock:
        cached = _session_cache.get(key)
        if cached and time.time() < cached[1]:
            return cached[0]
        session = _new_session(profile)
        _session_cache[key] = (session, time.time() + SESSION_TTL)
        return session


def invalidate_session():
    profile = get_active_profile()
    key = (profile["address"], profile["port"], profile["db_name"])
    with _cache_lock:
        _session_cache.pop(key, None)


if __name__ == "__main__":
    session = get_session()
    response = session.get(f"{session.base_url}/Cubes")
    cubes = response.json()["value"]
    p = get_active_profile()
    print(f"Connected to: {p['instance_name']} / {p['db_name']}")
    print(f"Cubes found: {len(cubes)}")
    for cube in cubes:
        print(f"  {cube['Name']}")
