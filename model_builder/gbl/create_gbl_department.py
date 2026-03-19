"""
create_gbl_department.py  (TM1py)
Builds the GBL Department dimension.

Coding scheme: D001-D017, Code & Desc + Desc aliases
Three-group hierarchy:
  Total Departments
    Total Clinical Departments   (D001-D008)
    Total Administrative Departments (D009-D012)
    Total Support Services       (D013-D017)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.tm1py_connect import get_tm1_service
from TM1py.Objects import Dimension, Hierarchy

tm1 = get_tm1_service()

DIM = 'GBL Department'
print(f"Building {DIM}...")

h = Hierarchy(name=DIM, dimension_name=DIM)
h.add_element_attribute('Code & Desc', 'Alias')
h.add_element_attribute('Desc',        'Alias')

# Top total
h.add_element('Total Departments', 'Consolidated')

# Structure: (code, desc, el_type, parent)
structure = [
    # Clinical Departments
    ('Total Clinical Departments',       'Total Clinical Departments',       'Consolidated', 'Total Departments'),
    ('D001', 'Emergency Department',     'Numeric',                          'Total Clinical Departments'),
    ('D002', 'Elective Surgery',         'Numeric',                          'Total Clinical Departments'),
    ('D003', 'Intensive Care Unit',      'Numeric',                          'Total Clinical Departments'),
    ('D004', 'Outpatient Clinics',       'Numeric',                          'Total Clinical Departments'),
    ('D005', 'Radiology',                'Numeric',                          'Total Clinical Departments'),
    ('D006', 'Pathology Laboratory',     'Numeric',                          'Total Clinical Departments'),
    ('D007', 'Maternity',                'Numeric',                          'Total Clinical Departments'),
    ('D008', 'Allied Health',            'Numeric',                          'Total Clinical Departments'),
    # Administrative Departments
    ('Total Administrative Departments', 'Total Administrative Departments', 'Consolidated', 'Total Departments'),
    ('D009', 'Finance and Administration', 'Numeric',                        'Total Administrative Departments'),
    ('D010', 'Human Resources',            'Numeric',                        'Total Administrative Departments'),
    ('D011', 'Information Technology',     'Numeric',                        'Total Administrative Departments'),
    ('D012', 'Executive and Governance',   'Numeric',                        'Total Administrative Departments'),
    # Support Services
    ('Total Support Services',           'Total Support Services',           'Consolidated', 'Total Departments'),
    ('D013', 'Facility Management',      'Numeric',                          'Total Support Services'),
    ('D014', 'Clinical Engineering',     'Numeric',                          'Total Support Services'),
    ('D015', 'Sterilisation Services',   'Numeric',                          'Total Support Services'),
    ('D016', 'Patient Transport',        'Numeric',                          'Total Support Services'),
    ('D017', 'Catering Services',        'Numeric',                          'Total Support Services'),
]

for code, desc, el_type, parent in structure:
    h.add_element(code, el_type)
    if parent:
        h.add_edge(parent, code, 1)

d = Dimension(name=DIM, hierarchies=[h])
tm1.dimensions.update_or_create(d)
print("  Dimension created/updated")

# Set aliases
cube_name = f"}}ElementAttributes_{DIM}"
dims      = [DIM, f"}}ElementAttributes_{DIM}"]
cells     = {}

cells[('Total Departments',              'Code & Desc')] = 'Total Departments'
cells[('Total Departments',              'Desc')]        = 'Total Departments'

for code, desc, el_type, parent in structure:
    if el_type == 'Numeric':
        cells[(code, 'Code & Desc')] = f"{code} {desc}"
        cells[(code, 'Desc')]        = desc
    else:
        cells[(code, 'Code & Desc')] = desc
        cells[(code, 'Desc')]        = desc

tm1.cells.write_values(cube_name, cells, dimensions=dims)
print(f"  Aliases set — {len(cells)} values")

tm1.logout()
print("Done!")
