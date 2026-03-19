"""
cleanup_cst_model.py
Deletes all CST module dimensions and cubes before a clean rebuild.
Does NOT touch GBL dimensions — those are managed by cleanup_gbl_model.py.

Run this before running build_cst_model.py on an existing environment.
"""

import sys
sys.path.insert(0, '/home/jdlove/tm1-governance')
from tm1py_connect import get_tm1_service

tm1 = get_tm1_service()

CUBES_TO_DELETE = [
    'CST GL Input',
    'CST Pool Driver',
    'CST Activity Driver',
    'CST Cost Pool Allocation',
    'CST Activity Allocation',
    'CST Service Line Cost',
    'CST Profit and Loss Report',
    'CST Allocation Reconciliation',
    'CST Allocation Config',
]

DIMENSIONS_TO_DELETE = [
    'CST Allocation Stage',
    'CST Cost Pool',
    'CST Activity',
    'CST Service Line',
    'CST Reconciliation Check',
    'CST Config Item',
    'CST GL Input Measure',
    'CST Pool Driver Measure',
    'CST Activity Driver Measure',
    'CST Cost Pool Allocation Measure',
    'CST Activity Allocation Measure',
    'CST Service Line Cost Measure',
    'CST Profit and Loss Report Measure',
    'CST Allocation Reconciliation Measure',
    'CST Allocation Config Measure',
]

print(f"\n{'═'*60}")
print("  Cleanup — CST Module")
print(f"{'═'*60}")

# Delete cubes first
print(f"\n{'─'*60}")
print("  Deleting cubes...")
print(f"{'─'*60}")
for name in CUBES_TO_DELETE:
    if tm1.cubes.exists(name):
        tm1.cubes.delete(name)
        print(f"  ✓ {name}")
    else:
        print(f"  - (not found) {name}")

# Delete dimensions
print(f"\n{'─'*60}")
print("  Deleting dimensions...")
print(f"{'─'*60}")
for name in DIMENSIONS_TO_DELETE:
    if tm1.dimensions.exists(name):
        tm1.dimensions.delete(name)
        print(f"  ✓ {name}")
    else:
        print(f"  - (not found) {name}")

tm1.logout()

print(f"\n{'═'*60}")
print("  CST cleanup complete.")
print("  Ready to run build_cst_model.py.")
print(f"{'═'*60}")
