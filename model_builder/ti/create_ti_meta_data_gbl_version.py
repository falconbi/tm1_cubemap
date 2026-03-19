"""
create_ti_meta_data_gbl_version.py
Deploys the META DATA GBL Version TI process to TM1.

This script deploys only — it does NOT execute the process.
Execution is done manually from PAW with the appropriate parameters
for each version before running the allocation.

Typical usage sequence:
  1. Run this script once to deploy the process to TM1
  2. In PAW, run META DATA GBL Version for each version:
       Actual:   pVersion=Actual, pStartPeriod=2025-04, pEndPeriod=2025-06,
                 pLastActualPeriod=2025-06, pIsSnapshot=N, pUpdatePeriodFlags=Y
       Budget:   pVersion=Budget, pStartPeriod=2025-04, pEndPeriod=2026-03,
                 pIsSnapshot=N, pUpdatePeriodFlags=Y (once at budget load)
       Forecast: pVersion=Forecast, pStartPeriod=2025-05, pEndPeriod=2026-03,
                 pIsSnapshot=N, pUpdatePeriodFlags=Y (updated each month)
"""

import sys
import os
import json
import time
sys.path.insert(0, '/home/jdlove/tm1-governance')
from tm1_connect import get_session

session      = get_session()
base         = session.base_url
PROCESS_NAME = 'META DATA GBL Version'

def process_exists(name):
    safe = name.replace("'", "''")
    r = session.get(f"{base}/Processes('{safe}')")
    return r.status_code == 200

def deploy_process(process_data):
    name = process_data['Name']
    if process_exists(name):
        print(f"  Process exists — updating (PATCH): {name}")
        safe = name.replace("'", "''")
        r = session.patch(f"{base}/Processes('{safe}')", json=process_data)
    else:
        print(f"  Process not found — creating (POST): {name}")
        r = session.post(f"{base}/Processes", json=process_data)
    if r.status_code in (200, 201, 204):
        print(f"  Deploy OK [{r.status_code}]")
        return True
    else:
        print(f"  Deploy FAILED [{r.status_code}]: {r.text[:300]}")
        return False

print(f"\n{'═'*60}")
print(f"  META DATA GBL Version — Deploy")
print(f"{'═'*60}")

script_dir = os.path.dirname(os.path.abspath(__file__))
json_path  = os.path.join(script_dir, 'json_files', 'ti_meta_data_gbl_version.json')

print(f"\n  Loading: {json_path}")
try:
    with open(json_path, 'r', encoding='utf-8') as f:
        process_data = json.load(f)
except FileNotFoundError:
    print(f"  ERROR: ti_meta_data_gbl_version.json not found.")
    print(f"  Run create_json_ti_meta_data_gbl_version.py first.")
    sys.exit(1)

print(f"  Process : {process_data['Name']}")
print(f"  Params  : {len(process_data.get('Parameters', []))}")

if not deploy_process(process_data):
    sys.exit(1)

print(f"\n{'═'*60}")
print(f"  META DATA GBL Version deployed successfully.")
print(f"{'═'*60}")
print("""
Run this process from PAW for each version before running allocations:

  Actual each month:
    pVersion           = Actual
    pStartPeriod       = YYYY-PP  (first month of current period)
    pEndPeriod         = YYYY-PP  (current closed month)
    pLastActualPeriod  = YYYY-PP  (same as pEndPeriod)
    pIsSnapshot        = N
    pUpdatePeriodFlags = Y

  Forecast each month (roll start forward):
    pVersion           = Forecast
    pStartPeriod       = YYYY-PP  (next open month)
    pEndPeriod         = YYYY-PP  (end of FY)
    pIsSnapshot        = N
    pUpdatePeriodFlags = Y

  Budget (once at budget load, N for subsequent runs):
    pVersion           = Budget
    pStartPeriod       = YYYY-PP  (start of budget year)
    pEndPeriod         = YYYY-PP  (end of budget year)
    pIsSnapshot        = N
    pUpdatePeriodFlags = Y  (use N if budget periods already set)
""")
