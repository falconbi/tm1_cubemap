"""
build_gbl_model.py
Builds all GBL shared infrastructure dimensions and cubes.
These objects are global — shared across all modules (CST, FIN, HR etc).

Prerequisites: GBL Period must already exist.
Run create_json_ti_meta_data_gbl_period.py then
    create_ti_meta_data_gbl_period.py first.

Execution order:
  1. GBL Account           — chart of accounts dimension
  2. GBL Version           — version dimension + operational attributes
  3. GBL Assumptions       — central control cube + measure dimension
  4. Generate TI JSON      — META DATA GBL Version process JSON
  5. Deploy TI             — META DATA GBL Version process to TM1
"""

import sys
import runpy
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
BASE = Path(__file__).parent


# ── Preflight — verify GBL Period exists ──────────────────────────────────────
def check_period_dependency():
    from core.tm1py_connect import get_tm1_service

    print("Checking GBL Period dependency...")
    tm1 = get_tm1_service()

    if tm1.dimensions.exists('GBL Period'):
        print("  ✓ GBL Period")
        tm1.logout()
        print("  GBL Period present — proceeding with GBL build.\n")
    else:
        print("  ✗ GBL Period — MISSING")
        tm1.logout()
        print("\n❌  GBL Period not found.")
        print("    Run create_json_ti_meta_data_gbl_period.py then")
        print("    create_ti_meta_data_gbl_period.py first.")
        sys.exit(1)


check_period_dependency()


# ── Build scripts ──────────────────────────────────────────────────────────────
SCRIPTS = [
    ('gbl/create_gbl_account',                   'GBL Account dimension + Code & Desc aliases'),
    ('gbl/create_gbl_department',                'GBL Department dimension + Code & Desc aliases'),
    ('gbl/create_gbl_currency_from',             'GBL Currency From dimension'),
    ('gbl/create_gbl_currency_to',               'GBL Currency To dimension'),
    ('gbl/create_gbl_version',                   'GBL Version dimension + operational attributes'),
    ('gbl/create_gbl_assumptions',               'GBL Assumptions cube + measure dimension'),
    ('ti/create_json_ti_meta_data_gbl_version',  'Generate META DATA GBL Version TI JSON'),
    ('ti/create_ti_meta_data_gbl_version',       'Deploy META DATA GBL Version TI to TM1'),
]

print("=" * 60)
print("Healthcare Model — GBL Infrastructure Build")
print("=" * 60)

for script, description in SCRIPTS:
    print(f"\n{'=' * 60}")
    print(f"STEP: {description}")
    print(f"{'=' * 60}")
    try:
        runpy.run_path(str(BASE / f'{script}.py'), run_name="__main__")
    except SystemExit:
        pass
    except Exception as e:
        print(f"\n❌  Error in {script}.py: {e}")
        sys.exit(1)
    time.sleep(1)

print("\n" + "=" * 60)
print("✅  GBL infrastructure build complete.")
print("=" * 60)
print("""
Objects created:
  Dimensions: GBL Account, GBL Version, GBL Assumptions Measure,
              GBL Department, GBL Currency From, GBL Currency To
  Cubes:      GBL Assumptions
  TI Process: META DATA GBL Version (deployed, not executed)

Next steps:
  1. Run META DATA GBL Version from PAW for each version
  2. Run build_cst_model.py to build the CST module
""")
