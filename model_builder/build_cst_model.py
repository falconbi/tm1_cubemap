"""
build_cst_model.py
Builds all CST module dimensions, cubes and configuration.

Prerequisites: GBL infrastructure must already exist.
Run build_gbl_model.py first if setting up a new environment.

Execution order:
  1. CST dimensions         — GBL Department + all CST dims + measure dims
  2. CST cubes              — all 8 CST cubes
  3. CST Allocation Config  — version-aware model settings
  4. Subsets and views      — default subsets and RPT Default views
"""

import sys
import runpy
import time
from pathlib import Path

sys.path.insert(0, '/home/jdlove/tm1-governance')
BASE = Path(__file__).parent


# ── Preflight — verify GBL dependencies exist ─────────────────────────────────
def check_gbl_dependencies():
    from core.tm1py_connect import get_tm1_service

    print("Checking GBL dependencies...")
    tm1 = get_tm1_service()

    required_dims  = ['GBL Account', 'GBL Version', 'GBL Period', 'GBL Department']
    required_cubes = ['GBL Assumptions']
    required_ti    = ['META DATA GBL Version']

    missing = []

    for dim in required_dims:
        if tm1.dimensions.exists(dim):
            print(f"  ✓ {dim}")
        else:
            print(f"  ✗ {dim} — MISSING")
            missing.append(dim)

    for cube in required_cubes:
        if tm1.cubes.exists(cube):
            print(f"  ✓ {cube}")
        else:
            print(f"  ✗ {cube} — MISSING")
            missing.append(cube)

    for ti in required_ti:
        if tm1.processes.exists(ti):
            print(f"  ✓ {ti}")
        else:
            print(f"  ✗ {ti} — MISSING")
            missing.append(ti)

    tm1.logout()

    if missing:
        print(f"\n❌  {len(missing)} GBL dependencies missing:")
        for m in missing:
            print(f"      {m}")
        print("\n    Run build_gbl_model.py first then retry.")
        sys.exit(1)

    print("  All GBL dependencies present — proceeding with CST build.\n")


check_gbl_dependencies()


# ── Build scripts ──────────────────────────────────────────────────────────────
SCRIPTS = [
    ('cst/create_cst_dimensions',        'All CST dimensions (GBL Department, CST + Measure dims)'),
    ('cst/create_cst_cubes',             'All 8 CST cubes'),
    ('cst/create_cst_allocation_config', 'CST Allocation Config cube — version-aware settings'),
    ('cst/create_cst_subsets_and_views', 'Default subsets and RPT Default views'),
]

print("=" * 60)
print("Healthcare Model — CST Module Build")
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
print("✅  CST module build complete.")
print("=" * 60)
print("""
Dimensions created:
  GBL Department
  CST: Cost Pool, Activity, Service Line, Reconciliation Check
  Measures: 8 cube-specific measure dimensions + CST Config dims

Cubes created:
  CST GL Input
  CST Pool Driver
  CST Activity Driver
  CST Cost Pool Allocation
  CST Activity Allocation
  CST Service Line Cost
  CST Profit and Loss Report
  CST Allocation Reconciliation
  CST Allocation Config

Next steps:
  1. Run META DATA GBL Version from PAW for each version
  2. Load source data via DATA IMPORT TI processes
  3. Run ADMIN Run CST ABC Allocation chore
""")
