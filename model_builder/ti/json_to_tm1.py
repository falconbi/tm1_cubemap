"""
json_to_tm1.py
==============
Imports TM1 TurboIntegrator processes from JSON files into TM1 Server 12
via the REST API.

Uses tm1_connect.py for the session (cookie-based auth via TM1SessionId).

Usage:
    Single file:  python json_to_tm1.py --file path/to/process.json
    Folder:       python json_to_tm1.py --json_folder ./json_files

Behaviour:
    - If the process DOES NOT exist  -> POST  (create)
    - If the process ALREADY EXISTS  -> PATCH (update / overwrite)
    - Logs success/fail per file, continues on errors
"""

import os
import json
import argparse
from tm1_connect import get_session

# ---------------------------------------------------------------------------
# Connect
# ---------------------------------------------------------------------------
session  = get_session()
BASE_URL = session.base_url      # e.g. http://192.168.1.178:4444/tm1/api/v1/Databases('TM1 Governance')
print(f"Connected -> {BASE_URL}\n")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def process_exists(process_name: str) -> bool:
    """Return True if the process already exists on the server."""
    safe_name = process_name.replace("'", "''")   # escape single quotes in OData key
    url = f"{BASE_URL}/Processes('{safe_name}')"
    try:
        resp = session.get(url)
        return resp.status_code == 200
    except Exception as e:
        print(f"    WARNING: Could not check '{process_name}': {e}")
        return False


def create_process(process_data: dict):
    url = f"{BASE_URL}/Processes"
    return session.post(url, json=process_data)


def update_process(process_name: str, process_data: dict):
    safe_name = process_name.replace("'", "''")
    url = f"{BASE_URL}/Processes('{safe_name}')"
    return session.patch(url, json=process_data)


def import_process(process_data: dict) -> bool:
    """POST or PATCH a single process. Returns True on success."""
    name = process_data.get('Name', 'UNKNOWN')
    print(f"  Process : {name}")

    exists = process_exists(name)
    if exists:
        print(f"    Action : UPDATE (PATCH)")
        resp = update_process(name, process_data)
    else:
        print(f"    Action : CREATE (POST)")
        resp = create_process(process_data)

    if resp.status_code in (200, 201, 204):
        print(f"    Result : OK [{resp.status_code}]")
        return True
    else:
        print(f"    Result : FAILED [{resp.status_code}]")
        print(f"    Detail : {resp.text[:400]}")
        return False


# ---------------------------------------------------------------------------
# Single file
# ---------------------------------------------------------------------------

def import_file(json_path: str) -> None:
    print(f"Loading: {json_path}")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ERROR reading file: {e}")
        return
    import_process(data)


# ---------------------------------------------------------------------------
# Folder
# ---------------------------------------------------------------------------

def import_folder(json_folder: str) -> None:
    json_files = sorted(f for f in os.listdir(json_folder) if f.lower().endswith('.json'))

    if not json_files:
        print(f"No .json files found in: {json_folder}")
        return

    print(f"Found {len(json_files)} JSON file(s) in '{json_folder}'")
    print(f"Target : {BASE_URL}\n")
    print("-" * 60)

    success, failed = 0, 0

    for filename in json_files:
        filepath = os.path.join(json_folder, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"  ERROR reading {filename}: {e}")
            failed += 1
            continue

        if import_process(data):
            success += 1
        else:
            failed += 1
        print()

    print("=" * 60)
    print(f"Done:  {success} succeeded   {failed} failed   {len(json_files)} total")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Import TM1 process JSON files into TM1 Server via REST API'
    )
    parser.add_argument('--file',        help='Single .json file to import')
    parser.add_argument('--json_folder', default='./json_files',
                        help='Folder of .json files (default: ./json_files)')
    args = parser.parse_args()

    if args.file:
        if not os.path.isfile(args.file):
            print(f"File not found: {args.file}")
        else:
            import_file(args.file)
    else:
        import_folder(args.json_folder)
