"""
fix_allocation_config.py
Deletes CST Allocation Config objects and rebuilds them cleanly.
"""
import sys
sys.path.insert(0, '/home/jdlove/tm1-governance')
from core.tm1py_connect import get_tm1_service
import runpy

tm1 = get_tm1_service()

for name in ['CST Allocation Config']:
    if tm1.cubes.exists(name):
        tm1.cubes.delete(name)
        print(f"  ✓ Deleted cube: {name}")

for name in ['CST Allocation Config Measure', 'CST Config Item']:
    if tm1.dimensions.exists(name):
        tm1.dimensions.delete(name)
        print(f"  ✓ Deleted dim: {name}")

tm1.logout()
print("Rebuilding...")
runpy.run_path('create_cst_allocation_config.py', run_name='__main__')
