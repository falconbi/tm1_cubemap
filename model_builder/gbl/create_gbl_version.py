"""
create_gbl_version.py  (v2 — TM1py)
Builds the GBL Version dimension using TM1py.

Elements:   Actual, Budget, Forecast
Aliases:    Desc
Attributes: Is Snapshot, Start Period, End Period, Number of Rolling Months
            (structural definition only — values edited directly in PAW via
            the }ElementAttributes_GBL Version cube)
"""

import sys
sys.path.insert(0, '/home/jdlove/tm1-governance')
from core.tm1py_connect import get_tm1_service
from TM1py.Objects import Dimension, Hierarchy, ElementAttribute

tm1 = get_tm1_service()

DIM = 'GBL Version'

print(f"Building {DIM}...")

h = Hierarchy(name=DIM, dimension_name=DIM)

# Display alias
h.add_element_attribute('Desc',               'Alias')

# Operational attributes — structure defined here, values edited directly
# in }ElementAttributes_GBL Version in PAW. META DATA GBL Version TI
# reads these and updates GBL Assumptions period flags.
h.add_element_attribute('Is Snapshot',             'String')
h.add_element_attribute('Start Period',            'String')
h.add_element_attribute('End Period',              'String')
h.add_element_attribute('Number of Rolling Months','Numeric')

# Elements and their Desc alias values
versions = [
    ('Actual',   'Actual results'),
    ('Budget',   'Annual budget'),
    ('Forecast', 'Rolling forecast'),
]

for el, desc in versions:
    h.add_element(el, 'Numeric')

d = Dimension(name=DIM, hierarchies=[h])
tm1.dimensions.update_or_create(d)
print("  Dimension created/updated")

# Explicitly add attributes — update_or_create does not add new attributes
# to existing dimensions so we add them individually if missing
from TM1py.Objects import ElementAttribute
existing_attrs = tm1.elements.get_element_attribute_names(DIM, DIM)
for attr_name, attr_type in [
    ('Desc',                     'Alias'),
    ('Is Snapshot',              'String'),
    ('Start Period',             'String'),
    ('End Period',               'String'),
    ('Number of Rolling Months', 'Numeric'),
]:
    if attr_name not in existing_attrs:
        tm1.elements.create_element_attribute(DIM, DIM, ElementAttribute(attr_name, attr_type))
        print(f"  Added attribute: {attr_name}")
    else:
        print(f"  Attribute exists: {attr_name}")

# Set Desc aliases
cube_name = f"}}ElementAttributes_{DIM}"
dims      = [DIM, f"}}ElementAttributes_{DIM}"]
cells     = {(el, 'Desc'): desc for el, desc in versions}
tm1.cells.write_values(cube_name, cells, dimensions=dims)
print(f"  Aliases set — {len(cells)} values")

# ── Set default attribute values ─────────────────────────────────────────────
# String attributes via write_through_unbound_process
print("  Setting default attribute values...")

attr_cube = f"}}ElementAttributes_{DIM}"
attr_dims  = [DIM, f"}}ElementAttributes_{DIM}"]

string_defaults = {
    ('Actual',   'Is Snapshot'):  'N',
    ('Actual',   'Start Period'): '2025-04',
    ('Actual',   'End Period'):   '2026-02',
    ('Budget',   'Is Snapshot'):  'N',
    ('Budget',   'Start Period'): '2025-04',
    ('Budget',   'End Period'):   '2026-03',
    ('Forecast', 'Is Snapshot'):  'N',
    ('Forecast', 'Start Period'): '2026-03',
    ('Forecast', 'End Period'):   '',
}
tm1.cells.write_through_unbound_process(attr_cube, string_defaults, dimensions=attr_dims)
print("  String attributes set")

# Numeric attribute — Number of Rolling Months
numeric_defaults = {
    ('Actual',   'Number of Rolling Months'): 0,
    ('Budget',   'Number of Rolling Months'): 0,
    ('Forecast', 'Number of Rolling Months'): 18,
}
tm1.cells.write_values(attr_cube, numeric_defaults, dimensions=attr_dims)
print("  Numeric attributes set")

tm1.logout()
print("Done!")
