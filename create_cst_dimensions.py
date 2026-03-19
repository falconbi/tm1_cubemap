"""
create_cst_dimensions.py  (v4 — TM1py)
Builds all CST module dimensions using TM1py.
TM1py handles all V12 REST API endpoint differences internally.
GBL dimensions are built by their own scripts in build_gbl_model.py.

Dimensions built:
  CST Cost Pool            CP01-CP09, Code & Desc + Desc aliases
  CST Activity             A01-A11,   Code & Desc + Desc aliases
  CST Service Line         SL01-SL08, Code & Desc + Desc aliases
  CST Reconciliation Check RC01-RC04, Code & Desc + Desc aliases
  All 8 Measure dimensions flat, no codes, Desc alias
"""

import sys
sys.path.insert(0, '/home/jdlove/tm1-governance')
from tm1py_connect import get_tm1_service
from TM1py.Objects import Dimension, Hierarchy, Element, ElementAttribute

# ── Connect ───────────────────────────────────────────────────────────────────
tm1 = get_tm1_service()


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_flat_dim(dim_name, elements_with_desc):
    """
    Build a flat dimension with Desc alias only.
    elements_with_desc: list of (element_name, desc_string)
    """
    print(f"\n{'─'*60}")
    print(f"  {dim_name}")
    print(f"{'─'*60}")

    h = Hierarchy(name=dim_name, dimension_name=dim_name)
    h.add_element_attribute('Desc', 'Alias')

    for el, desc in elements_with_desc:
        h.add_element(el, 'Numeric')

    d = Dimension(name=dim_name, hierarchies=[h])
    tm1.dimensions.update_or_create(d)
    print(f"  Dimension created/updated")

    # Write Desc alias values
    cube_name = f"}}ElementAttributes_{dim_name}"
    dims      = [dim_name, f"}}ElementAttributes_{dim_name}"]
    cells     = {(el, 'Desc'): desc for el, desc in elements_with_desc}
    tm1.cells.write_values(cube_name, cells, dimensions=dims)
    print(f"  Aliases set — {len(cells)} values")


def build_coded_dim(dim_name, structure, total_code, total_desc):
    """
    Build a dimension with Code & Desc and Desc aliases.
    Leaf elements use codes. Consolidated nodes use descriptive names.

    structure: list of (code, desc, el_type, parent)
      Leaves:    ('D001', 'Emergency Department', 'Numeric', 'Total Clinical Depts')
      Sub-total: ('Total Clinical Departments', 'Total Clinical Departments', 'Consolidated', 'Total Departments')
    total_code: top-level consolidated element name
    total_desc: description for the top element
    """
    print(f"\n{'─'*60}")
    print(f"  {dim_name}")
    print(f"{'─'*60}")

    h = Hierarchy(name=dim_name, dimension_name=dim_name)
    h.add_element_attribute('Code & Desc', 'Alias')
    h.add_element_attribute('Desc', 'Alias')

    # Top total
    h.add_element(total_code, 'Consolidated')

    # All other elements and edges
    for code, desc, el_type, parent in structure:
        h.add_element(code, el_type)
        if parent:
            h.add_edge(parent, code, 1)

    d = Dimension(name=dim_name, hierarchies=[h])
    tm1.dimensions.update_or_create(d)
    print(f"  Dimension created/updated")

    # Build alias value dict for both attributes
    cube_name = f"}}ElementAttributes_{dim_name}"
    dims      = [dim_name, f"}}ElementAttributes_{dim_name}"]
    cells     = {}

    # Top total
    cells[(total_code, 'Code & Desc')] = total_desc
    cells[(total_code, 'Desc')]        = total_desc

    for code, desc, el_type, parent in structure:
        if el_type == 'Numeric':
            cells[(code, 'Code & Desc')] = f"{code} {desc}"
            cells[(code, 'Desc')]        = desc
        else:
            # Consolidated sub-node — no code prefix
            cells[(code, 'Code & Desc')] = desc
            cells[(code, 'Desc')]        = desc

    tm1.cells.write_values(cube_name, cells, dimensions=dims)
    print(f"  Aliases set — {len(cells)} values")


# ══════════════════════════════════════════════════════════════════════════════
# CST Cost Pool  CP01-CP09
# ══════════════════════════════════════════════════════════════════════════════
build_coded_dim('CST Cost Pool', [
    ('CP01', 'Facility Management',      'Numeric', 'Total Cost Pools'),
    ('CP02', 'Clinical Engineering',     'Numeric', 'Total Cost Pools'),
    ('CP03', 'Information Technology',   'Numeric', 'Total Cost Pools'),
    ('CP04', 'Human Resources',          'Numeric', 'Total Cost Pools'),
    ('CP05', 'Finance and Admin',        'Numeric', 'Total Cost Pools'),
    ('CP06', 'Sterilisation',            'Numeric', 'Total Cost Pools'),
    ('CP07', 'Patient Transport',        'Numeric', 'Total Cost Pools'),
    ('CP08', 'Catering',                 'Numeric', 'Total Cost Pools'),
    ('CP09', 'Executive and Governance', 'Numeric', 'Total Cost Pools'),
], total_code='Total Cost Pools', total_desc='Total Cost Pools')


# ══════════════════════════════════════════════════════════════════════════════
# CST Activity  A01-A11
# ══════════════════════════════════════════════════════════════════════════════
build_coded_dim('CST Activity', [
    ('A01', 'Patient Admission',       'Numeric', 'Total Activities'),
    ('A02', 'Surgical Preparation',    'Numeric', 'Total Activities'),
    ('A03', 'Clinical Procedure',      'Numeric', 'Total Activities'),
    ('A04', 'Patient Monitoring',      'Numeric', 'Total Activities'),
    ('A05', 'Diagnostic Ordering',     'Numeric', 'Total Activities'),
    ('A06', 'Diagnostic Reporting',    'Numeric', 'Total Activities'),
    ('A07', 'Medication Management',   'Numeric', 'Total Activities'),
    ('A08', 'Theatre Scheduling',      'Numeric', 'Total Activities'),
    ('A09', 'Discharge Planning',      'Numeric', 'Total Activities'),
    ('A10', 'Outpatient Coordination', 'Numeric', 'Total Activities'),
    ('A11', 'Infection Prevention',    'Numeric', 'Total Activities'),
], total_code='Total Activities', total_desc='Total Activities')


# ══════════════════════════════════════════════════════════════════════════════
# CST Service Line  SL01-SL08
# ══════════════════════════════════════════════════════════════════════════════
build_coded_dim('CST Service Line', [
    ('SL01', 'Emergency Department', 'Numeric', 'Total Service Lines'),
    ('SL02', 'Elective Surgery',     'Numeric', 'Total Service Lines'),
    ('SL03', 'Intensive Care Unit',  'Numeric', 'Total Service Lines'),
    ('SL04', 'Outpatient Clinics',   'Numeric', 'Total Service Lines'),
    ('SL05', 'Radiology',            'Numeric', 'Total Service Lines'),
    ('SL06', 'Pathology Laboratory', 'Numeric', 'Total Service Lines'),
    ('SL07', 'Maternity',            'Numeric', 'Total Service Lines'),
    ('SL08', 'Allied Health',        'Numeric', 'Total Service Lines'),
], total_code='Total Service Lines', total_desc='Total Service Lines')


# ══════════════════════════════════════════════════════════════════════════════
# CST Reconciliation Check  RC01-RC04
# ══════════════════════════════════════════════════════════════════════════════
build_coded_dim('CST Reconciliation Check', [
    ('RC01', 'Stage 1 Balance',  'Numeric', 'Total Reconciliation'),
    ('RC02', 'Stage 2A Balance', 'Numeric', 'Total Reconciliation'),
    ('RC03', 'Stage 2B Balance', 'Numeric', 'Total Reconciliation'),
    ('RC04', 'Total Variance',   'Numeric', 'Total Reconciliation'),
], total_code='Total Reconciliation', total_desc='Total Reconciliation')


# ══════════════════════════════════════════════════════════════════════════════
# Measure Dimensions — flat, Desc alias only
# ══════════════════════════════════════════════════════════════════════════════
measure_dims = {

    'CST GL Input Measure': [
        ('Amount', 'GL account amount loaded from Costs.csv'),
    ],

    'CST Pool Driver Measure': [
        ('Driver Value',            'Raw driver quantity for this cost pool and activity'),
        ('Driver Percentage Share', 'Driver value as percentage of total pool drivers — must sum to 100 per pool'),
    ],

    'CST Activity Driver Measure': [
        ('Driver Value',            'Raw driver quantity for this activity and service line'),
        ('Driver Percentage Share', 'Driver value as percentage of total activity drivers — must sum to 100 per activity'),
    ],

    'CST Cost Pool Allocation Measure': [
        ('Allocated Amount', 'GL overhead accumulated into this cost pool'),
        ('Allocation Rate',  'Pool total cost divided by sum of driver values for this pool'),
        ('Pool Total',       'Total cost in this pool available for allocation to activities'),
    ],

    'CST Activity Allocation Measure': [
        ('Allocated Amount', 'Cost allocated from cost pools into this activity'),
        ('Allocation Rate',  'Activity total cost divided by sum of driver values for this activity'),
        ('Activity Total',   'Total cost in this activity available for allocation to service lines'),
    ],

    'CST Service Line Cost Measure': [
        ('Allocated Amount', 'Activity cost allocated to this service line'),
        ('Allocation Rate',  'Cost per unit of service line cost driver'),
        ('Per Admission',    'Allocated cost divided by service line admissions count'),
        ('Per Bed Day',      'Allocated cost divided by service line occupied bed days'),
    ],

    'CST Profit and Loss Report Measure': [
        ('Amount',                      'Financial amount for this account and service line'),
        ('Variance to Budget',          'Amount minus Budget amount'),
        ('Variance Percent',            'Variance to Budget as a percentage of Budget'),
        ('ABC vs Traditional Variance', 'After ABC minus Before ABC — measures ABC impact'),
    ],

    'CST Allocation Reconciliation Measure': [
        ('Input Total',      'Total cost entering this allocation stage'),
        ('Output Total',     'Total cost leaving this allocation stage'),
        ('Variance',         'Input minus Output — tolerance 1 dollar, halt on breach'),
        ('Variance Percent', 'Variance as a percentage of Input Total'),
    ],
}

for dim_name, elements in measure_dims.items():
    build_flat_dim(dim_name, elements)

# ══════════════════════════════════════════════════════════════════════════════
# CST Allocation Stage
# Flat — Pre Allocation, Post Allocation
# Used on CST Profit and Loss Report to compare traditional vs ABC costs
# ══════════════════════════════════════════════════════════════════════════════
build_flat_dim('CST Allocation Stage', [
    ('Pre Allocation',  'Costs using traditional allocation — before ABC is applied'),
    ('Post Allocation', 'Costs after ABC allocation has been applied'),
])


tm1.logout()

print(f"\n\n{'═'*60}")
print("All CST dimensions created.")
print(f"{'═'*60}")
print("""
Coding scheme:
  GBL Department           D001-D017  Code & Desc, Desc aliases
  CST Cost Pool            CP01-CP09  Code & Desc, Desc aliases
  CST Activity             A01-A11    Code & Desc, Desc aliases
  CST Service Line         SL01-SL08  Code & Desc, Desc aliases
  CST Reconciliation Check RC01-RC04  Code & Desc, Desc aliases
  GBL Version              No codes   Desc alias only
  All Measure dimensions   No codes   Desc alias only
""")
