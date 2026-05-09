import time
import threading
import requests
import contextlib
import urllib3
from TM1py import TM1Service
from TM1py.Services.RestService import RestService

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Save original RestService methods before any V12 patching
_orig_set_version    = RestService.set_version
_orig_construct_root = RestService._construct_service_and_auth_root


# ── V12 monkey-patches ────────────────────────────────────────────────────────
# Required for TM1py to work with V12 on-prem (see TM1py_V12_Onprem_Bug_Report.txt)

def _patched_set_version(self):
    self._version = "12.5.5"


@contextlib.contextmanager
def _v12_patches(profile):
    """Apply V12 patches around TM1Service construction, then restore originals."""
    def _patched_construct_root(self):
        base = (f"http://{profile['address']}:{profile['port']}"
                f"/tm1/api/v1/Databases('{profile['db_name']}')")
        return (base, f"{base}/Configuration/ProductVersion/$value")

    RestService.set_version = _patched_set_version
    RestService._construct_service_and_auth_root = _patched_construct_root
    try:
        yield
    finally:
        RestService.set_version    = _orig_set_version
        RestService._construct_service_and_auth_root = _orig_construct_root


# ── V12 token cache ───────────────────────────────────────────────────────────

_token_lock  = threading.Lock()
_token_cache = {}  # (address, port, db_name) -> (token, expiry)
TOKEN_TTL    = 600


def _get_v12_token(profile: dict) -> str:
    key = (profile['address'], profile['port'], profile['db_name'])
    with _token_lock:
        cached = _token_cache.get(key)
        if cached and time.time() < cached[1]:
            return cached[0]
        r = requests.post(
            f"http://{profile['address']}:{profile['port']}/tm1/auth/v1/session",
            auth=(profile['client_id'], profile['client_secret']),
            headers={'Content-Type': 'application/json'},
            json={'User': profile['user']},
        )
        r.raise_for_status()
        token = r.cookies.get('TM1SessionId')
        if not token:
            raise ConnectionError(f"No TM1SessionId in response — status {r.status_code}")
        _token_cache[key] = (token, time.time() + TOKEN_TTL)
        return token


def invalidate_token():
    with _token_lock:
        _token_cache.clear()


# ── Connection ────────────────────────────────────────────────────────────────

def get_tm1_service() -> TM1Service:
    from core.tm1_connect import get_active_profile
    profile = get_active_profile()

    try:
        if profile['auth'] == 'v12':
            token = _get_v12_token(profile)
            with _v12_patches(profile):
                service = TM1Service(
                    base_url=(f"http://{profile['address']}:{profile['port']}"
                              f"/tm1/api/v1/Databases('{profile['db_name']}')"),
                    session_id=token,
                    ssl=False,
                    verify=False,
                    timeout=10,
                )
            return service

        # V11 — native TM1py Basic auth over HTTPS
        return TM1Service(
            address=profile['address'],
            port=profile['port'],
            user=profile['user'],
            password=profile['password'],
            ssl=True,
            verify=False,
            timeout=10,
        )
    except Exception as e:
        msg = str(e)
        if 'timed out' in msg.lower() or 'connect' in msg.lower():
            raise ConnectionError(
                f"Cannot reach {profile['instance_name']} / {profile['db_name']} "
                f"({profile['address']}:{profile['port']}) — is the TM1 service running?"
            ) from e
        raise


def get_config() -> dict:
    """Return active profile info for display/metadata use."""
    from core.tm1_connect import get_active_profile
    p = get_active_profile()
    return {
        'address':  p['address'],
        'port':     p['port'],
        'database': p['db_name'],
    }


# Backward-compat shim for extract_tm1_model.py
class _ConfigProxy(dict):
    def __getitem__(self, key):
        return get_config()[key]

TM1_CONFIG = _ConfigProxy()


if __name__ == '__main__':
    cfg = get_config()
    print(f"Connecting to TM1 — {cfg['address']}:{cfg['port']}")
    print(f"Database: {cfg['database']}\n")
    with get_tm1_service() as tm1:
        print("Connected ✅")
        dims  = tm1.dimensions.get_all_names()
        cubes = tm1.cubes.get_all_names()
        print(f"Dimensions: {len(dims)}  Cubes: {len(cubes)}")
