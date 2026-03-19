"""
create_cst_subsets_and_views.py  (v3 — MDX views)
Creates default subsets and views for all dimensions and cubes.

Subsets — two per dimension:
  SYS All   — MDX: all elements including consolidations
  SYS Leaf  — MDX: leaf elements only

Views — MDX views throughout:
  RPT Default — MDX view with correct axis layout:
                Columns = GBL Period (leaf)
                Rows    = primary analytical dimension (leaf)
                WHERE   = sensible defaults (Actual, totals, key measure)

MDX views are used instead of native views because:
  - Reliable on TM1 V12 REST API
  - Full MDX power for filtering and calculated members
  - Users can still explore and modify in PAW
  - Simple REST API call — no subset reference complexity
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.tm1py_connect import get_tm1_service
from TM1py.Objects import Subset, MDXView

tm1 = get_tm1_service()


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_mdx_subset(dim_name, subset_name, mdx):
    """Create or replace an MDX-based public subset."""
    s = Subset(
        subset_name    = subset_name,
        dimension_name = dim_name,
        hierarchy_name = dim_name,
        expression     = mdx,
    )
    tm1.subsets.update_or_create(s, private=False)


def make_static_subset(dim_name, subset_name, elements):
    """Create or replace a static public subset."""
    s = Subset(
        subset_name    = subset_name,
        dimension_name = dim_name,
        hierarchy_name = dim_name,
        elements       = elements,
    )
    tm1.subsets.update_or_create(s, private=False)


def make_mdx_view(cube_name, view_name, mdx):
    """Delete existing view then create fresh MDX view."""
    for private in [False, True]:
        try:
            tm1.views.delete(cube_name, view_name, private=private)
        except Exception:
            pass
    v = MDXView(cube_name=cube_name, view_name=view_name, MDX=mdx)
    tm1.views.create(v, private=False)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Subsets for all dimensions
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'═'*60}")
print("  STEP 1 — Subsets")
print(f"{'═'*60}")

ALL_DIMENSIONS = [
    'GBL Account',
    'GBL Department',
    'GBL Period',
    'GBL Version',
    'CST Cost Pool',
    'CST Activity',
    'CST Service Line',
    'CST Reconciliation Check',
    'CST Allocation Stage',
    'CST GL Input Measure',
    'CST Pool Driver Measure',
    'CST Activity Driver Measure',
    'CST Cost Pool Allocation Measure',
    'CST Activity Allocation Measure',
    'CST Service Line Cost Measure',
    'CST Profit and Loss Report Measure',
    'CST Allocation Reconciliation Measure',
]

for dim in ALL_DIMENSIONS:
    safe = dim.replace("'", "''")
    make_mdx_subset(dim, 'SYS All',
        f"{{TM1SUBSETALL( [{safe}] )}}")
    make_mdx_subset(dim, 'SYS Leaf',
        f"{{TM1FILTERBYLEVEL( {{TM1SUBSETALL( [{safe}] )}}, 0)}}")
    print(f"  ✓ {dim}")

# ── Single-element filter subsets ─────────────────────────────────────────────
print(f"\n  Filter subsets...")

# GBL Version — read dynamically from TM1
gbl_versions = tm1.elements.get_leaf_element_names('GBL Version', 'GBL Version')
for ver in gbl_versions:
    make_static_subset('GBL Version', f"SYS {ver}", [ver])
    print(f"    GBL Version — SYS {ver}")

make_static_subset('GBL Period',      'SYS FY 2025',               ['FY 2025'])
make_static_subset('GBL Account',     'SYS NET PROFIT',             ['NET PROFIT'])
make_static_subset('GBL Department',  'SYS Total Departments',      ['Total Departments'])
make_static_subset('CST Cost Pool',   'SYS Total Cost Pools',       ['Total Cost Pools'])
make_static_subset('CST Activity',    'SYS Total Activities',       ['Total Activities'])
make_static_subset('CST Service Line','SYS Total Service Lines',    ['Total Service Lines'])
make_static_subset('CST Profit and Loss Report Measure', 'SYS Amount',          ['Amount'])
make_static_subset('CST Pool Driver Measure',            'SYS Driver Value',    ['Driver Value'])
make_static_subset('CST Activity Driver Measure',        'SYS Driver Value',    ['Driver Value'])
make_static_subset('CST Cost Pool Allocation Measure',   'SYS Pool Total',      ['Pool Total'])
make_static_subset('CST Activity Allocation Measure',    'SYS Activity Total',  ['Activity Total'])
make_static_subset('CST Service Line Cost Measure',      'SYS Allocated Amount',['Allocated Amount'])
make_static_subset('CST Allocation Reconciliation Measure', 'SYS Variance',     ['Variance'])
make_static_subset('CST Allocation Stage', 'SYS Post Allocation',   ['Post Allocation'])
make_static_subset('CST Allocation Stage', 'SYS Pre Allocation',    ['Pre Allocation'])
print("    Filter subsets done")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — RPT Default MDX views
# Layout: Columns = GBL Period (leaf), Rows = primary dim (leaf)
#         WHERE   = Version=Actual, totals for other dims, key measure
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'═'*60}")
print("  STEP 2 — MDX Views")
print(f"{'═'*60}")

# ── CST GL Input ──────────────────────────────────────────────────────────────
make_mdx_view('CST GL Input', 'Default', """
SELECT
  {TM1FILTERBYLEVEL({TM1SUBSETALL([GBL Period])},0)} ON 0,
  {TM1FILTERBYLEVEL({TM1SUBSETALL([GBL Account])},0)} ON 1
FROM [CST GL Input]
WHERE (
  [GBL Department].[GBL Department].[Total Departments],
  [GBL Version].[GBL Version].[Actual],
  [CST GL Input Measure].[CST GL Input Measure].[Amount]
)
""")
print("  ✓ CST GL Input — RPT Default")

# ── CST Pool Driver ───────────────────────────────────────────────────────────
make_mdx_view('CST Pool Driver', 'Default', """
SELECT
  {TM1FILTERBYLEVEL({TM1SUBSETALL([GBL Period])},0)} ON 0,
  {TM1FILTERBYLEVEL({TM1SUBSETALL([CST Cost Pool])},0)} ON 1
FROM [CST Pool Driver]
WHERE (
  [CST Activity].[CST Activity].[Total Activities],
  [GBL Version].[GBL Version].[Actual],
  [CST Pool Driver Measure].[CST Pool Driver Measure].[Driver Value]
)
""")
print("  ✓ CST Pool Driver — RPT Default")

# ── CST Activity Driver ───────────────────────────────────────────────────────
make_mdx_view('CST Activity Driver', 'Default', """
SELECT
  {TM1FILTERBYLEVEL({TM1SUBSETALL([GBL Period])},0)} ON 0,
  {TM1FILTERBYLEVEL({TM1SUBSETALL([CST Activity])},0)} ON 1
FROM [CST Activity Driver]
WHERE (
  [CST Service Line].[CST Service Line].[Total Service Lines],
  [GBL Version].[GBL Version].[Actual],
  [CST Activity Driver Measure].[CST Activity Driver Measure].[Driver Value]
)
""")
print("  ✓ CST Activity Driver — RPT Default")

# ── CST Cost Pool Allocation ──────────────────────────────────────────────────
make_mdx_view('CST Cost Pool Allocation', 'Default', """
SELECT
  {TM1FILTERBYLEVEL({TM1SUBSETALL([GBL Period])},0)} ON 0,
  {TM1FILTERBYLEVEL({TM1SUBSETALL([CST Cost Pool])},0)} ON 1
FROM [CST Cost Pool Allocation]
WHERE (
  [GBL Account].[GBL Account].[NET PROFIT],
  [GBL Version].[GBL Version].[Actual],
  [CST Cost Pool Allocation Measure].[CST Cost Pool Allocation Measure].[Pool Total]
)
""")
print("  ✓ CST Cost Pool Allocation — RPT Default")

# ── CST Activity Allocation ───────────────────────────────────────────────────
make_mdx_view('CST Activity Allocation', 'Default', """
SELECT
  {TM1FILTERBYLEVEL({TM1SUBSETALL([GBL Period])},0)} ON 0,
  {TM1FILTERBYLEVEL({TM1SUBSETALL([CST Activity])},0)} ON 1
FROM [CST Activity Allocation]
WHERE (
  [CST Cost Pool].[CST Cost Pool].[Total Cost Pools],
  [GBL Version].[GBL Version].[Actual],
  [CST Activity Allocation Measure].[CST Activity Allocation Measure].[Activity Total]
)
""")
print("  ✓ CST Activity Allocation — RPT Default")

# ── CST Service Line Cost ─────────────────────────────────────────────────────
make_mdx_view('CST Service Line Cost', 'Default', """
SELECT
  {TM1FILTERBYLEVEL({TM1SUBSETALL([GBL Period])},0)} ON 0,
  {TM1FILTERBYLEVEL({TM1SUBSETALL([CST Service Line])},0)} ON 1
FROM [CST Service Line Cost]
WHERE (
  [CST Activity].[CST Activity].[Total Activities],
  [GBL Version].[GBL Version].[Actual],
  [CST Service Line Cost Measure].[CST Service Line Cost Measure].[Allocated Amount]
)
""")
print("  ✓ CST Service Line Cost — RPT Default")

# ── CST Profit and Loss Report ────────────────────────────────────────────────
make_mdx_view('CST Profit and Loss Report', 'Default', """
SELECT
  {TM1FILTERBYLEVEL({TM1SUBSETALL([GBL Period])},0)} ON 0,
  {TM1FILTERBYLEVEL({TM1SUBSETALL([GBL Account])},0)} ON 1
FROM [CST Profit and Loss Report]
WHERE (
  [CST Service Line].[CST Service Line].[Total Service Lines],
  [GBL Version].[GBL Version].[Actual],
  [CST Allocation Stage].[CST Allocation Stage].[Post Allocation],
  [CST Profit and Loss Report Measure].[CST Profit and Loss Report Measure].[Amount]
)
""")
print("  ✓ CST Profit and Loss Report — RPT Default")

# ── CST Allocation Reconciliation ─────────────────────────────────────────────
make_mdx_view('CST Allocation Reconciliation', 'Default', """
SELECT
  {TM1FILTERBYLEVEL({TM1SUBSETALL([GBL Period])},0)} ON 0,
  {TM1FILTERBYLEVEL({TM1SUBSETALL([CST Reconciliation Check])},0)} ON 1
FROM [CST Allocation Reconciliation]
WHERE (
  [GBL Version].[GBL Version].[Actual],
  [CST Allocation Reconciliation Measure].[CST Allocation Reconciliation Measure].[Variance]
)
""")
print("  ✓ CST Allocation Reconciliation — RPT Default")


tm1.logout()

print(f"\n\n{'═'*60}")
print("  Subsets and views created successfully.")
print(f"{'═'*60}")
print("""
Subsets per dimension:
  SYS All       all elements including consolidations (MDX)
  SYS Leaf      leaf elements only (MDX)
  SYS <filter>  single-element subsets for filtering

Views per cube (MDX):
  RPT Default   columns = GBL Period (leaf)
                rows    = primary analytical dimension (leaf)
                WHERE   = Version=Actual, key measure, totals
""")
