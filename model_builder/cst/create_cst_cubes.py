"""
create_cst_cubes.py  (v2 — TM1py)
Builds all 8 cubes for the Healthcare ABC model using TM1py.

Cubes created:
  1. CST GL Input
  2. CST Pool Driver
  3. CST Activity Driver
  4. CST Cost Pool Allocation
  5. CST Activity Allocation
  6. CST Service Line Cost
  7. CST Profit and Loss Report
  8. CST Allocation Reconciliation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.tm1py_connect import get_tm1_service
from TM1py.Objects import Cube

tm1 = get_tm1_service()


def create_cube(cube_name, dimensions):
    """Create a cube if it does not already exist."""
    print(f"\n── {cube_name} ──")
    if tm1.cubes.exists(cube_name):
        print(f"  Exists — skipping")
    else:
        cube = Cube(cube_name, dimensions)
        tm1.cubes.create(cube)
        print(f"  ✓ Created ({len(dimensions)} dimensions)")


print("Building cubes for Healthcare ABC model...\n")

# 1 ── CST GL Input ────────────────────────────────────────────────────────────
create_cube('CST GL Input', [
    'GBL Account',
    'GBL Department',
    'GBL Period',
    'GBL Version',
    'CST GL Input Measure',
])

# 2 ── CST Pool Driver ─────────────────────────────────────────────────────────
create_cube('CST Pool Driver', [
    'CST Cost Pool',
    'CST Activity',
    'GBL Period',
    'GBL Version',
    'CST Pool Driver Measure',
])

# 3 ── CST Activity Driver ─────────────────────────────────────────────────────
create_cube('CST Activity Driver', [
    'CST Activity',
    'CST Service Line',
    'GBL Period',
    'GBL Version',
    'CST Activity Driver Measure',
])

# 4 ── CST Cost Pool Allocation ────────────────────────────────────────────────
create_cube('CST Cost Pool Allocation', [
    'CST Cost Pool',
    'GBL Account',
    'GBL Period',
    'GBL Version',
    'CST Cost Pool Allocation Measure',
])

# 5 ── CST Activity Allocation ─────────────────────────────────────────────────
create_cube('CST Activity Allocation', [
    'CST Activity',
    'CST Cost Pool',
    'GBL Period',
    'GBL Version',
    'CST Activity Allocation Measure',
])

# 6 ── CST Service Line Cost ───────────────────────────────────────────────────
create_cube('CST Service Line Cost', [
    'CST Service Line',
    'CST Activity',
    'GBL Period',
    'GBL Version',
    'CST Service Line Cost Measure',
])

# 7 ── CST Profit and Loss Report ──────────────────────────────────────────────
create_cube('CST Profit and Loss Report', [
    'GBL Account',
    'CST Service Line',
    'GBL Period',
    'GBL Version',
    'CST Allocation Stage',
    'CST Profit and Loss Report Measure',
])

# 8 ── CST Allocation Reconciliation ──────────────────────────────────────────
create_cube('CST Allocation Reconciliation', [
    'CST Reconciliation Check',
    'GBL Period',
    'GBL Version',
    'CST Allocation Reconciliation Measure',
])

tm1.logout()

print("\n\n✅  All CST cubes created successfully.")
