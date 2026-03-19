"""
create_gbl_currency_from.py  (TM1py)
Builds the GBL Currency From dimension.

Used in the FIN Exchange Rate cube:
  GBL Currency From x GBL Currency To x GBL Period x GBL Version x FIN Exchange Rate Measure

Initial elements cover the currencies most relevant to Australian healthcare.
Add additional currencies as needed when the FIN module is built.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.tm1py_connect import get_tm1_service
from TM1py.Objects import Dimension, Hierarchy

tm1 = get_tm1_service()

DIM = 'GBL Currency From'
print(f"Building {DIM}...")

h = Hierarchy(name=DIM, dimension_name=DIM)
h.add_element_attribute('Desc', 'Alias')

currencies = [
    ('AUD', 'Australian Dollar'),
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ('GBP', 'British Pound'),
    ('NZD', 'New Zealand Dollar'),
    ('SGD', 'Singapore Dollar'),
    ('JPY', 'Japanese Yen'),
    ('CNY', 'Chinese Yuan'),
]

for code, desc in currencies:
    h.add_element(code, 'Numeric')

d = Dimension(name=DIM, hierarchies=[h])
tm1.dimensions.update_or_create(d)
print("  Dimension created/updated")

cube_name = f"}}ElementAttributes_{DIM}"
dims      = [DIM, f"}}ElementAttributes_{DIM}"]
cells     = {(code, 'Desc'): desc for code, desc in currencies}
tm1.cells.write_values(cube_name, cells, dimensions=dims)
print(f"  Aliases set — {len(cells)} values")

tm1.logout()
print("Done!")
