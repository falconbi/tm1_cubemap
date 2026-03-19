"""
cleanup_gbl_model.py
Deletes all GBL shared infrastructure before a clean rebuild.

WARNING: This will delete GBL dimensions and cubes shared across
all modules. Only run this if you intend to rebuild everything
from scratch. Run cleanup_cst_model.py first to remove dependent
CST objects before running this script.

Does NOT touch GBL Period — managed independently via TI.
"""

import sys
sys.path.insert(0, '/home/jdlove/tm1-governance')
from tm1py_connect import get_tm1_service

tm1 = get_tm1_service()

CUBES_TO_DELETE = [
    'GBL Assumptions',
]

DIMENSIONS_TO_DELETE = [
    'GBL Account',
    'GBL Version',
    'GBL Assumptions Measure',
    'GBL Department',
    'GBL Currency From',
    'GBL Currency To',
]

TI_TO_DELETE = [
    'META DATA GBL Version',
]

print(f"\n{'═'*60}")
print("  Cleanup — GBL Infrastructure")
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

# Delete TI processes
print(f"\n{'─'*60}")
print("  Deleting TI processes...")
print(f"{'─'*60}")
for name in TI_TO_DELETE:
    if tm1.processes.exists(name):
        tm1.processes.delete(name)
        print(f"  ✓ {name}")
    else:
        print(f"  - (not found) {name}")

tm1.logout()

print(f"\n{'═'*60}")
print("  GBL cleanup complete.")
print("  Ready to run build_gbl_model.py.")
print(f"{'═'*60}")
