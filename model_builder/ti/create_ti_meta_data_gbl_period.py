"""
create_ti_meta_data_gbl_period.py
Deploys the META DATA GBL Period TI process to TM1 and executes it
to build the GBL Period dimension.

The TI process JSON (ti_meta_data_gbl_period.json) is loaded from the
same directory as this script. The JSON is deployed exactly as-is —
no modifications to the process code. Only the execution parameters
are overridden at run time:

    pPeriodDimName   = GBL Period     (dimension name — overridden from default 'Period')
    pStartYear       = 2011           (as per JSON default)
    pEndYear         = 2040           (as per JSON default)
    pStartMonth      = Apr            (Healthcare model — Australian FY, April start)
    pDeleteAndRebuild = N             (safe — only adds missing elements)
    pIncludeDriverElement = N
    pIncludeInputElement  = N
    pDebug           = N

GBL Period structure produced by the TI:
    Period Consolidations
      ├── Reporting
      │     ├── All FY
      │     │     └── FY YYYY → YYYY-01 through YYYY-12
      │     ├── All QTR
      │     │     └── FY YYYY-QTR → Q1/Q2/Q3/Q4
      │     ├── All YTD
      │     │     └── FY YYYY-YTD → FY YYYY-01-YTD … FY YYYY-13-YTD
      │     ├── All YTG
      │     │     └── FY YYYY-YTG → FY YYYY-01-YTG … FY YYYY-11-YTG
      │     └── All LTD
      │           └── FY YYYY-LTD → FY YYYY-01-LTD … FY YYYY-13-LTD
      └── System
            └── No GBL Period

Leaf elements: YYYY-00 (Opening Balance), YYYY-01 through YYYY-12, YYYY-13 (P13)

Attributes set per leaf period:
    Caption, Long Name, Next Period, Previous Period, Next Year,
    Previous Year, Last Period, First Period, Month Contains Actuals,
    Year Name, Fin Year, Month, Days in Period, Leap Year,
    Calendar Month Number, Calendar Year,
    Period Start Serial, Period End Serial
"""

import sys
import os
import json
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.tm1_connect import get_session

session  = get_session()
base     = session.base_url
PROCESS_NAME = 'META DATA GBL Period'
DIM_NAME     = 'GBL Period'

# ── Execution parameters ──────────────────────────────────────────────────────
# These are passed at runtime — the JSON process definition is unchanged.
# Adjust pStartYear / pEndYear / pStartMonth to suit the deployment environment.
EXEC_PARAMS = {
    'pStartYear':            '2025',
    'pEndYear':              '2028',
    'pStartMonth':           'Apr',    # April — Australian healthcare FY start
    'pPeriodDimName':        DIM_NAME, # GBL Period — overrides default 'Period'
    'pDeleteAndRebuild':     'Y',
    'pIncludeDriverElement': 'N',
    'pIncludeInputElement':  'N',
    'pDebug':                'N',
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def process_exists(name):
    safe = name.replace("'", "''")
    r = session.get(f"{base}/Processes('{safe}')")
    return r.status_code == 200


def deploy_process(process_data):
    """POST (create) or PATCH (update) the TI process. Returns True on success."""
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
        print(f"  Deploy FAILED [{r.status_code}]")
        print(f"  Detail: {r.text[:400]}")
        return False


def execute_process(name, params):
    """Execute a TI process with the given parameters dict."""
    safe = name.replace("'", "''")
    url  = f"{base}/Processes('{safe}')/tm1.Execute"

    # Build the Parameters payload as a list of Name/Value pairs
    payload = {
        'Parameters': [
            {'Name': k, 'Value': v}
            for k, v in params.items()
        ]
    }

    print(f"\n  Executing: {name}")
    for k, v in params.items():
        print(f"    {k} = {v}")

    r = session.post(url, json=payload)

    if r.status_code in (200, 201, 204):
        print(f"\n  Execute OK [{r.status_code}]")
        return True
    else:
        print(f"\n  Execute FAILED [{r.status_code}]")
        print(f"  Detail: {r.text[:600]}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

print(f"\n{'═'*60}")
print(f"  GBL Period — Deploy and Execute")
print(f"{'═'*60}")

# Load the JSON from the same directory as this script
script_dir = os.path.dirname(os.path.abspath(__file__))
json_path  = os.path.join(script_dir, 'json_files', 'ti_meta_data_gbl_period.json')

print(f"\n  Loading process JSON: {json_path}")
try:
    with open(json_path, 'r', encoding='utf-8') as f:
        process_data = json.load(f)
except FileNotFoundError:
    print(f"  ERROR: json_files/ti_meta_data_gbl_period.json not found at {json_path}")
    print(f"  Ensure ti_meta_data_gbl_period.json is in the json_files/ subdirectory.")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"  ERROR: Invalid JSON — {e}")
    sys.exit(1)

# Confirm the process name matches expectation
if process_data.get('Name') != PROCESS_NAME:
    print(f"  WARNING: JSON Name is '{process_data.get('Name')}', expected '{PROCESS_NAME}'")

print(f"  Process name : {process_data['Name']}")
print(f"  Parameters   : {len(process_data.get('Parameters', []))} defined in JSON")

# Step 1 — Deploy
print(f"\n{'─'*60}")
print("  STEP 1 — Deploy TI process to TM1")
print(f"{'─'*60}")
if not deploy_process(process_data):
    print("\n  Aborting — process deployment failed.")
    sys.exit(1)

# Brief pause to let TM1 register the process
time.sleep(2)

# Step 2 — Execute
print(f"\n{'─'*60}")
print("  STEP 2 — Execute to build GBL Period")
print(f"{'─'*60}")
if not execute_process(PROCESS_NAME, EXEC_PARAMS):
    print("\n  Aborting — process execution failed.")
    sys.exit(1)

print(f"\n{'═'*60}")
print(f"  GBL Period built successfully.")
print(f"{'═'*60}")
print(f"""
  Dimension : {DIM_NAME}
  FY range  : {EXEC_PARAMS['pStartYear']} — {EXEC_PARAMS['pEndYear']}
  FY start  : {EXEC_PARAMS['pStartMonth']} (April — Australian healthcare year)
  Elements  : YYYY-00 through YYYY-13 per year, with QTR/YTD/YTG/LTD hierarchies
  Attributes: Caption, Long Name, Next/Prev Period, Days in Period,
              Period Start/End Serial, Calendar Month/Year, and more.

  To rebuild or extend the year range, re-run this script after
  adjusting EXEC_PARAMS above, or run META DATA GBL Period directly
  in PAW with the desired parameters.
""")
