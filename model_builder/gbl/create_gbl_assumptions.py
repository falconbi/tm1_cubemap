"""
create_gbl_assumptions.py  (TM1py)
Builds the GBL Assumptions cube and its measure dimension.

This cube is the central control layer for the model.
Every version-aware operational setting lives here by period.

Cube:       GBL Assumptions
Dimensions: GBL Version x GBL Period x GBL Assumptions Measure

Measure elements:
  Is Active            1 = period is valid for allocation run in this version
  Is Locked            1 = period is closed to further input
  Current Period Flag  1 = this is the current open period for this version
  Working Days         Number of working days in this period
  Allocation Tolerance Variance threshold before reconciliation halts (default 1)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.tm1py_connect import get_tm1_service
from TM1py.Objects import Cube, Dimension, Hierarchy

tm1 = get_tm1_service()

DIM     = 'GBL Assumptions Measure'
CUBE    = 'GBL Assumptions'

# ── GBL Assumptions Measure dimension ────────────────────────────────────────
print(f"Building {DIM}...")

measures = [
    ('Is Active',            'Numeric', '1 = period is valid for allocation run in this version'),
    ('Is Locked',            'Numeric', '1 = period is closed to further input'),
    ('Current Period Flag',  'Numeric', '1 = this is the current open period for this version'),
    ('Working Days',         'Numeric', 'Number of working days in this period by version'),
    ('Allocation Tolerance', 'Numeric', 'Variance threshold in dollars before reconciliation halts — default 1'),
]

h = Hierarchy(name=DIM, dimension_name=DIM)
h.add_element_attribute('Desc', 'Alias')

for el, el_type, desc in measures:
    h.add_element(el, el_type)

d = Dimension(name=DIM, hierarchies=[h])
tm1.dimensions.update_or_create(d)
print("  Dimension created/updated")

# Set Desc aliases
cube_name = f"}}ElementAttributes_{DIM}"
dims      = [DIM, f"}}ElementAttributes_{DIM}"]
cells     = {(el, 'Desc'): desc for el, el_type, desc in measures}
tm1.cells.write_values(cube_name, cells, dimensions=dims)
print(f"  Aliases set — {len(cells)} values")

# ── GBL Assumptions cube ──────────────────────────────────────────────────────
print(f"\nBuilding {CUBE}...")
if tm1.cubes.exists(CUBE):
    print("  Exists — skipping")
else:
    cube = Cube(CUBE, ['GBL Version', 'GBL Period', 'GBL Assumptions Measure'])
    tm1.cubes.create(cube)
    print("  ✓ Created")

# ── Default Allocation Tolerance = 1 for all versions ────────────────────────
print("\nSetting default Allocation Tolerance = 1...")
CUBE_DIMS = ['GBL Version', 'GBL Period', 'GBL Assumptions Measure']

# Get all leaf periods
periods = tm1.elements.get_leaf_element_names('GBL Period', 'GBL Period')
versions = ['Actual', 'Budget', 'Forecast']

cells = {}
for version in versions:
    for period in periods:
        cells[(version, period, 'Allocation Tolerance')] = 1

tm1.cells.write_values(CUBE, cells, dimensions=CUBE_DIMS)
print(f"  Set Allocation Tolerance = 1 for {len(versions)} versions x {len(periods)} periods")

tm1.logout()
print("\nDone!")
