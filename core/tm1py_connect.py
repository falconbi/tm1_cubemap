import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from TM1py import TM1Service
from TM1py.Services.RestService import RestService

load_dotenv(Path(__file__).parent.parent / '.env')

# -----------------------------------------------------------------------
# TM1 V12 On-Prem Configuration
# -----------------------------------------------------------------------
TM1_CONFIG = {
    'address':       os.environ['TM1_ADDRESS'],
    'port':          int(os.environ['TM1_PORT']),
    'database':      os.environ['TM1_DATABASE'],
    'client_id':     os.environ['TM1_CLIENT_ID'],
    'client_secret': os.environ['TM1_CLIENT_SECRET'],
    'user':          os.environ['TM1_USER'],
}

# -----------------------------------------------------------------------
# Monkey-patches required for TM1py to work with V12 on-prem
# See: TM1py_V12_Onprem_Bug_Report.txt for full details
# -----------------------------------------------------------------------
def _patched_set_version(self):
    self._version = "12.5.5"

def _patched_construct_root(self):
    cfg = TM1_CONFIG
    base = f"http://{cfg['address']}:{cfg['port']}/tm1/api/v1/Databases('{cfg['database']}')"
    return (base, f"{base}/Configuration/ProductVersion/$value")

RestService.set_version = _patched_set_version
RestService._construct_service_and_auth_root = _patched_construct_root

# -----------------------------------------------------------------------
# Connection functions
# -----------------------------------------------------------------------
def get_token():
    cfg = TM1_CONFIG
    auth = requests.post(
        f"http://{cfg['address']}:{cfg['port']}/tm1/auth/v1/session",
        auth=(cfg['client_id'], cfg['client_secret']),
        headers={'Content-Type': 'application/json'},
        json={'User': cfg['user']}
    )
    token = auth.cookies.get('TM1SessionId')
    if not token:
        raise ConnectionError(f"Failed to get TM1SessionId — auth status: {auth.status_code}")
    return token


def get_tm1_service() -> TM1Service:
    cfg = TM1_CONFIG
    token = get_token()
    return TM1Service(
        base_url=f"http://{cfg['address']}:{cfg['port']}/tm1/api/v1/Databases('{cfg['database']}')",
        session_id=token,
        ssl=False,
        verify=False,
    )


# -----------------------------------------------------------------------
# Test connection when run directly
# -----------------------------------------------------------------------
if __name__ == '__main__':
    print("Connecting to TM1...")
    with get_tm1_service() as tm1:
        print(f"Connected ✅")
        print(f"Database  : {TM1_CONFIG['database']}")
        print(f"Version   : {tm1.server.get_product_version()}")

        dims = tm1.dimensions.get_all_names()
        print(f"\nDimensions: {len(dims)} found")
        for d in [d for d in dims if not d.startswith('}')]:
            print(f"  {d}")

        cubes = tm1.cubes.get_all_names()
        print(f"\nCubes     : {len(cubes)} found")
        for c in [c for c in cubes if not c.startswith('}')]:
            print(f"  {c}")
