"""
create_cst_allocation_stage.py  (TM1py)
Builds the CST Allocation Stage dimension.

This dimension represents where in the allocation process costs are viewed:
  Pre Allocation  — costs using traditional allocation method (before ABC)
  Post Allocation — costs after ABC allocation has been applied

Used on cubes where the Before/After ABC comparison is meaningful,
primarily CST Profit and Loss Report.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.tm1py_connect import get_tm1_service
from TM1py.Objects import Dimension, Hierarchy

tm1 = get_tm1_service()

DIM = 'CST Allocation Stage'
print(f"Building {DIM}...")

stages = [
    ('Pre Allocation',  'Costs using traditional allocation — before ABC is applied'),
    ('Post Allocation', 'Costs after ABC allocation has been applied'),
]

h = Hierarchy(name=DIM, dimension_name=DIM)
h.add_element_attribute('Desc', 'Alias')

for el, desc in stages:
    h.add_element(el, 'Numeric')

d = Dimension(name=DIM, hierarchies=[h])
tm1.dimensions.update_or_create(d)
print("  Dimension created/updated")

cube_name = f"}}ElementAttributes_{DIM}"
dims      = [DIM, f"}}ElementAttributes_{DIM}"]
cells     = {(el, 'Desc'): desc for el, desc in stages}
tm1.cells.write_values(cube_name, cells, dimensions=dims)
print(f"  Aliases set — {len(cells)} values")

tm1.logout()
print("Done!")
