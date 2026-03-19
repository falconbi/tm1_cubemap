"""
create_cst_allocation_config.py  (v2 — TM1py)
Builds the CST Allocation Config cube and supporting dimensions using TM1py.

This cube is the single source of truth for all version-aware model settings:
  Is Allocated    Y/N per GL account
  Pool Mapping    CST Cost Pool code per GL account
  Primary Driver  driver description per cost pool
  Cost Driver     driver description per activity
  Revenue Type    funding type per service line

All settings are stored by GBL Version so Actual, Budget and Forecast
can have different structural configurations to Actual.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.tm1py_connect import get_tm1_service
from TM1py.Objects import Cube, Dimension, Hierarchy, Element, ElementAttribute

tm1 = get_tm1_service()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — CST Config Item dimension
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'─'*60}")
print("  CST Config Item")
print(f"{'─'*60}")

h = Hierarchy(name='CST Config Item', dimension_name='CST Config Item')
h.add_element_attribute('Desc',         'Alias')
h.add_element_attribute('Setting Type', 'String')

# Consolidated nodes
h.add_element('Total Config',          'Consolidated')
h.add_element('Account Settings',      'Consolidated')
h.add_element('Cost Pool Settings',    'Consolidated')
h.add_element('Activity Settings',     'Consolidated')
h.add_element('Service Line Settings', 'Consolidated')

h.add_edge('Total Config', 'Account Settings',      1)
h.add_edge('Total Config', 'Cost Pool Settings',    1)
h.add_edge('Total Config', 'Activity Settings',     1)
h.add_edge('Total Config', 'Service Line Settings', 1)

# Account leaves
account_leaves = [
    ('4001', 'Inpatient Revenue'),
    ('4002', 'Outpatient Revenue'),
    ('4003', 'Radiology Revenue'),
    ('4004', 'Pathology Revenue'),
    ('4005', 'Other Revenue'),
    ('5001', 'Direct Labour'),
    ('5002', 'Direct Materials'),
    ('5003', 'Direct Supplies'),
    ('6001', 'Indirect Nursing Salaries'),
    ('6002', 'Medical Administration Salaries'),
    ('6003', 'Building Depreciation'),
    ('6004', 'Rent and Rates'),
    ('6005', 'Cleaning and Waste'),
    ('6006', 'Medical Equipment Depreciation'),
    ('6007', 'Equipment Maintenance'),
    ('6008', 'IT Infrastructure'),
    ('6009', 'Software Licences'),
    ('6010', 'IT Helpdesk'),
    ('6011', 'Recruitment Costs'),
    ('6012', 'Training and Development'),
    ('6013', 'HR Administration'),
    ('6014', 'Finance Team Salaries'),
    ('6015', 'Payroll Processing'),
    ('6016', 'Accounts Payable'),
    ('6017', 'Autoclave Operation'),
    ('6018', 'Sterilisation Materials'),
    ('6019', 'Orderly Salaries'),
    ('6020', 'Patient Transfer Equipment'),
    ('6021', 'Catering Salaries'),
    ('6022', 'Food and Beverage'),
    ('6023', 'Executive Salaries'),
    ('6024', 'Board Costs'),
    ('6025', 'Legal and Compliance'),
    ('6026', 'Accreditation Costs'),
    ('7001', 'Facility Management Allocated'),
    ('7002', 'Clinical Engineering Allocated'),
    ('7003', 'Information Technology Allocated'),
    ('7004', 'Human Resources Allocated'),
    ('7005', 'Finance and Admin Allocated'),
    ('7006', 'Sterilisation Allocated'),
    ('7007', 'Patient Transport Allocated'),
    ('7008', 'Catering Allocated'),
    ('7009', 'Executive and Governance Allocated'),
]

cost_pool_leaves = [
    ('CP01', 'Facility Management'),
    ('CP02', 'Clinical Engineering'),
    ('CP03', 'Information Technology'),
    ('CP04', 'Human Resources'),
    ('CP05', 'Finance and Admin'),
    ('CP06', 'Sterilisation'),
    ('CP07', 'Patient Transport'),
    ('CP08', 'Catering'),
    ('CP09', 'Executive and Governance'),
]

activity_leaves = [
    ('A01', 'Patient Admission'),
    ('A02', 'Surgical Preparation'),
    ('A03', 'Clinical Procedure'),
    ('A04', 'Patient Monitoring'),
    ('A05', 'Diagnostic Ordering'),
    ('A06', 'Diagnostic Reporting'),
    ('A07', 'Medication Management'),
    ('A08', 'Theatre Scheduling'),
    ('A09', 'Discharge Planning'),
    ('A10', 'Outpatient Coordination'),
    ('A11', 'Infection Prevention'),
]

service_line_leaves = [
    ('SL01', 'Emergency Department'),
    ('SL02', 'Elective Surgery'),
    ('SL03', 'Intensive Care Unit'),
    ('SL04', 'Outpatient Clinics'),
    ('SL05', 'Radiology'),
    ('SL06', 'Pathology Laboratory'),
    ('SL07', 'Maternity'),
    ('SL08', 'Allied Health'),
]

for code, desc in account_leaves:
    h.add_element(code, 'Numeric')
    h.add_edge('Account Settings', code, 1)

for code, desc in cost_pool_leaves:
    h.add_element(code, 'Numeric')
    h.add_edge('Cost Pool Settings', code, 1)

for code, desc in activity_leaves:
    h.add_element(code, 'Numeric')
    h.add_edge('Activity Settings', code, 1)

for code, desc in service_line_leaves:
    h.add_element(code, 'Numeric')
    h.add_edge('Service Line Settings', code, 1)

d = Dimension(name='CST Config Item', hierarchies=[h])
tm1.dimensions.update_or_create(d)
print("  Dimension created/updated")

# Set aliases and Setting Type attribute values
cube_name = '}ElementAttributes_CST Config Item'
dims      = ['CST Config Item', '}ElementAttributes_CST Config Item']
cells     = {}

# Consolidated nodes
for el, desc in [
    ('Total Config',          'Total Config'),
    ('Account Settings',      'Account Settings'),
    ('Cost Pool Settings',    'Cost Pool Settings'),
    ('Activity Settings',     'Activity Settings'),
    ('Service Line Settings', 'Service Line Settings'),
]:
    cells[(el, 'Desc')] = desc

# Leaves with Setting Type
all_leaves = (
    [(c, d, 'Account')      for c, d in account_leaves] +
    [(c, d, 'Cost Pool')    for c, d in cost_pool_leaves] +
    [(c, d, 'Activity')     for c, d in activity_leaves] +
    [(c, d, 'Service Line') for c, d in service_line_leaves]
)
for code, desc, setting_type in all_leaves:
    cells[(code, 'Desc')]         = desc
    cells[(code, 'Setting Type')] = setting_type

tm1.cells.write_through_unbound_process(cube_name, cells, dimensions=dims)
print(f"  Aliases set — {len(cells)} values")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — CST Allocation Config Measure dimension
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'─'*60}")
print("  CST Allocation Config Measure")
print(f"{'─'*60}")

measures = [
    ('Is Allocated',   'Y = overhead account allocated through ABC, N = direct cost or revenue'),
    ('Pool Mapping',   'CST Cost Pool code this GL account maps to'),
    ('Primary Driver', 'Driver used to allocate this cost pool to activities'),
    ('Cost Driver',    'Driver used to allocate this activity to service lines'),
    ('Revenue Type',   'Funding type for this service line'),
]

h2 = Hierarchy(name='CST Allocation Config Measure', dimension_name='CST Allocation Config Measure')
h2.add_element_attribute('Desc', 'Alias')
for el, desc in measures:
    h2.add_element(el, 'String')

d2 = Dimension(name='CST Allocation Config Measure', hierarchies=[h2])
tm1.dimensions.update_or_create(d2)
print("  Dimension created/updated")

cube2   = '}ElementAttributes_CST Allocation Config Measure'
dims2   = ['CST Allocation Config Measure', '}ElementAttributes_CST Allocation Config Measure']
cells2  = {(el, 'Desc'): desc for el, desc in measures}
tm1.cells.write_through_unbound_process(cube2, cells2, dimensions=dims2)
print(f"  Aliases set — {len(cells2)} values")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — CST Allocation Config cube
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'─'*60}")
print("  CST Allocation Config (cube)")
print(f"{'─'*60}")

CUBE = 'CST Allocation Config'
if tm1.cubes.exists(CUBE):
    print(f"  Exists — skipping")
else:
    cube = Cube(CUBE, ['CST Config Item', 'GBL Version', 'CST Allocation Config Measure'])
    tm1.cubes.create(cube)
    print(f"  ✓ Created")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Populate default settings for all versions
# ══════════════════════════════════════════════════════════════════════════════
# Read versions dynamically from GBL Version dimension
VERSIONS = tm1.elements.get_leaf_element_names('GBL Version', 'GBL Version')
CUBE_DIMS = ['CST Config Item', 'GBL Version', 'CST Allocation Config Measure']

is_allocated_map = {
    '4001': 'N', '4002': 'N', '4003': 'N', '4004': 'N', '4005': 'N',
    '5001': 'N', '5002': 'N', '5003': 'N',
    '6001': 'Y', '6002': 'Y', '6003': 'Y', '6004': 'Y', '6005': 'Y',
    '6006': 'Y', '6007': 'Y', '6008': 'Y', '6009': 'Y', '6010': 'Y',
    '6011': 'Y', '6012': 'Y', '6013': 'Y', '6014': 'Y', '6015': 'Y',
    '6016': 'Y', '6017': 'Y', '6018': 'Y', '6019': 'Y', '6020': 'Y',
    '6021': 'Y', '6022': 'Y', '6023': 'Y', '6024': 'Y', '6025': 'Y',
    '6026': 'Y',
    '7001': 'N', '7002': 'N', '7003': 'N', '7004': 'N', '7005': 'N',
    '7006': 'N', '7007': 'N', '7008': 'N', '7009': 'N',
}

pool_mapping_map = {
    '6001': 'CP01', '6002': 'CP04', '6003': 'CP01', '6004': 'CP01',
    '6005': 'CP01', '6006': 'CP02', '6007': 'CP02', '6008': 'CP03',
    '6009': 'CP03', '6010': 'CP03', '6011': 'CP04', '6012': 'CP04',
    '6013': 'CP04', '6014': 'CP05', '6015': 'CP05', '6016': 'CP05',
    '6017': 'CP06', '6018': 'CP06', '6019': 'CP07', '6020': 'CP07',
    '6021': 'CP08', '6022': 'CP08', '6023': 'CP09', '6024': 'CP09',
    '6025': 'CP09', '6026': 'CP09',
}

primary_driver_map = {
    'CP01': 'Floor space (square metres)',
    'CP02': 'Equipment hours',
    'CP03': 'IT tickets raised',
    'CP04': 'Headcount (FTE)',
    'CP05': 'Transactions processed',
    'CP06': 'Instrument trays processed',
    'CP07': 'Patient transfers',
    'CP08': 'Patient meal days',
    'CP09': 'Headcount (FTE)',
}

cost_driver_map = {
    'A01': 'Admissions count',
    'A02': 'Theatre sessions',
    'A03': 'Weighted procedure units',
    'A04': 'Occupied bed days',
    'A05': 'Diagnostic orders placed',
    'A06': 'Reports produced',
    'A07': 'Medication administrations',
    'A08': 'Theatre bookings',
    'A09': 'Discharges processed',
    'A10': 'Outpatient appointments',
    'A11': 'Bed days (all patients)',
}

revenue_type_map = {
    'SL01': 'Mixed — public and insured',
    'SL02': 'Predominantly insured',
    'SL03': 'Predominantly public',
    'SL04': 'Mixed — public and insured',
    'SL05': 'Fee for service',
    'SL06': 'Fee for service',
    'SL07': 'Mixed — public and insured',
    'SL08': 'Predominantly public',
}

print(f"\n{'─'*60}")
print("  Populating settings for all versions...")
print(f"{'─'*60}")

for version in VERSIONS:
    cells = {}
    for account, flag in is_allocated_map.items():
        cells[(account, version, 'Is Allocated')] = flag
    for account, pool in pool_mapping_map.items():
        cells[(account, version, 'Pool Mapping')] = pool
    for pool, driver in primary_driver_map.items():
        cells[(pool, version, 'Primary Driver')] = driver
    for activity, driver in cost_driver_map.items():
        cells[(activity, version, 'Cost Driver')] = driver
    for sl, rev_type in revenue_type_map.items():
        cells[(sl, version, 'Revenue Type')] = rev_type

    # All measures in CST Allocation Config are String type
    measure_types = {
        'Is Allocated':   'String',
        'Pool Mapping':   'String',
        'Primary Driver': 'String',
        'Cost Driver':    'String',
        'Revenue Type':   'String',
    }
    tm1.cells.write_through_unbound_process(
        CUBE, cells,
        dimensions=CUBE_DIMS,
        measure_dimension_elements=measure_types
    )
    print(f"  {version} — {len(cells)} cells written")

tm1.logout()

print(f"\n\n{'═'*60}")
print("CST Allocation Config built and populated.")
print(f"{'═'*60}")
