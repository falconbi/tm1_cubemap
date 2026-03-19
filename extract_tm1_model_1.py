"""
extract_tm1_model_1.py
──────────────────────
Connects to TM1 V12 on-prem via requests (tm1_connect.py) and extracts the full cube model
into tm1_model.json for the Generic CubeMap diagram.

Features:
- Uses $expand to fetch all dimensions in 1 call (Performance).
- Uses ThreadPoolExecutor to fetch rules in parallel (Performance).
- Uses 3-character Prefixes for generic coloring (Configurable).
- Calculates Architecture Score and Complexity.
"""

import sys
import re
import json
import argparse
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Imports ───────────────────────────────────────────────────────────────
try:
    from tm1_connect import get_session
except ImportError:
    print("Error: Could not import get_session from tm1_connect.py.")
    sys.exit(1)

# ── Configuration ───────────────────────────────────────────────────────────
OUTPUT_FILE = "tm1_model.json"

# Regex: Matches [Cube]( or Cube(
RULE_DEPENDENCY_REGEX = re.compile(r'(?:\[)([^\]]+)(?:\]\()|(\b[\w %@$#-]+\b)(?=\()')

# 1. CONFIGURATION: Map your prefixes to colors here
PREFIX_COLORS = {
    'CST': '#8957e5', # Purple (Costing / ABC)
    'GBL': '#388bfd', # Blue (Global / Shared)
    'FIN': '#2ea043', # Green (Finance)
    'HRM': '#e36209', # Orange (HR / Payroll)
    'OPS': '#d29922', # Amber (Operations)
    'SYS': '#6e7681', # Grey (System / Control)
}

DEFAULT_COLOR = '#6e7681' # Grey for unknown prefixes

# ── Logic Helpers (Generic Prefix-Based) ───────────────────────────────────────

def classify_dimension_kind(dim_name: str) -> str:
    """Classify a dimension as global / measure / control / cst."""
    if dim_name.startswith('}'): return 'control'
    name_upper = dim_name.upper()
    if name_upper.startswith('GBL '): return 'global'
    if 'MEASURE' in name_upper: return 'measure'
    return 'cst'

def classify_and_get_color(cube_name: str):
    """
    Generic Classifier:
    Looks at the first 3 characters of the cube name.
    Returns the 'Type' (the prefix) and the 'Color'.
    """
    if len(cube_name) >= 3:
        prefix = cube_name[:3].upper()
        
        # If we have a color defined for this prefix, use it
        if prefix in PREFIX_COLORS:
            return prefix, PREFIX_COLORS[prefix]
        
        # Fallback: If prefix starts with } (System cube)
        if prefix.startswith('}'):
            return 'System', PREFIX_COLORS.get('SYS', DEFAULT_COLOR)

    # If no match found, return the first 3 chars anyway as the type, but use default color
    return cube_name[:3].upper(), DEFAULT_COLOR

def extract_rules_header(rules_text: str) -> str:
    """Extract comment block from top of rules file."""
    if not rules_text:
        return ''
    lines = rules_text.split('\n')
    header_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            header_lines.append(stripped.lstrip('#').strip())
        elif stripped == '':
            if header_lines:
                continue
        else:
            break
    return ' '.join(l for l in header_lines if l)

def analyse_rules(rules_text: str) -> dict:
    """Count rules metrics for complexity scoring."""
    if not rules_text:
        return {'total': 0, 'lines': 0, 'comments': 0, 'dbRefs': 0, 'feeders': 0, 'ifs': 0}
    
    all_lines = rules_text.split('\n')
    total = len(all_lines)
    comments = sum(1 for l in all_lines if l.strip().startswith('#'))
    blanks = sum(1 for l in all_lines if l.strip() == '')
    rule_lines = total - comments - blanks
    upper = rules_text.upper()

    return {
        'total': total,
        'lines': rule_lines,
        'comments': comments,
        'dbRefs': upper.count('DB('),
        'feeders': sum(1 for l in all_lines if 'FEEDERS' in l.upper()),
        'ifs': upper.count('\nIF(') + (1 if upper.startswith('IF(') else 0),
    }

def calculate_complexity_score(rules_stats: dict) -> int:
    """Calculates weighted complexity score (Section 8.3)."""
    return (rules_stats['lines'] * 1 +
            rules_stats['dbRefs'] * 5 +
            rules_stats['ifs'] * 3 +
            rules_stats['feeders'] * 2)

def find_db_references(cube_name: str, rules_text: str, all_cubes_set: set) -> list:
    """
    Find all DB() calls in rules that reference other cubes.
    Improved to ignore comments and string literals.
    """
    if not rules_text:
        return []
    
    # Remove string literals to avoid false positives inside quotes
    clean_text = re.sub(r"'[^']*'", "''", rules_text)
    
    matches = RULE_DEPENDENCY_REGEX.findall(clean_text)
    seen = set()
    edges = []
    
    for match in matches:
        target = match[0] if match[0] else match[1]
        if target in all_cubes_set and target.lower() != cube_name.lower():
            key = (cube_name, target)
            if key not in seen:
                seen.add(key)
                edges.append({'source': target, 'target': cube_name, 'type': 'rules'})
    return edges

# ── Main Extraction Logic ───────────────────────────────────────────────────

def fetch_rules_for_cube(session, base_url, cube_name):
    """Worker function for parallel fetching of rules."""
    try:
        url = f"{base_url}/Cubes('{cube_name}')/Rules"
        resp = session.get(url)
        
        # If the status code is 204 (No Content) or similar, handle it gracefully
        if resp.status_code == 204:
            return cube_name, ""
            
        # Try to parse JSON only if we have content
        if resp.status_code == 200:
            # Check if content is actually empty
            if not resp.content or len(resp.content) == 0:
                return cube_name, ""
            return cube_name, resp.json().get('Value', '')
        
        # If we get here, it's an unexpected error
        print(f"    ⚠️  Error fetching rules for {cube_name}: {resp.status_code} {resp.reason}")
        return cube_name, ""

    except Exception as e:
        # This catches the JSON decode error if TM1 sends garbage
        # print(f"    ⚠️  Error parsing rules for {cube_name}: {e}")
        return cube_name, ""

def extract_model(prefix_filter: str = '') -> dict:
    print(f"\nConnecting to TM1...")
    session = get_session()
    base_url = session.base_url
    print("✅ Connected\n")

    # 1. Get All Cubes AND Dimensions in ONE call (Optimization)
    print("Fetching Cube and Dimension metadata...")
    cubes_resp = session.get(f"{base_url}/Cubes?$expand=Dimensions")
    cubes_resp.raise_for_status()
    raw_cubes = cubes_resp.json().get('value', [])
    
    # Process Metadata
    cubes_data = {}
    cube_names = []
    
    for c in raw_cubes:
        name = c['Name']
        if name.startswith('}'): continue # Skip system cubes
        if prefix_filter and not name.upper().startswith(prefix_filter.upper()): continue
        
        cube_names.append(name)
        
        # Parse Dimensions
        dims_list = [d['Name'] for d in c.get('Dimensions', [])]
        dims_kinds = [{'n': d, 'k': classify_dimension_kind(d)} for d in dims_list]
        
        cubes_data[name] = {
            'dims': dims_kinds,
            'raw_dims': dims_list,
            'hasRules': False, 
            'rules_text': '',
            'type': 'standard',
            'color': DEFAULT_COLOR, # Will be updated by classify_and_get_color
            'desc': '',
            'descSource': 'manual',
            'rules_stats': {},
            'complexity': 0,
            'from': [],
            'to': []
        }

    print(f"Found {len(cube_names)} cubes to process.")

    # 2. Fetch Rules in Parallel (Performance)
    print("Fetching Rules (Parallel)...")
    rules_map = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_cube = {
            executor.submit(fetch_rules_for_cube, session, base_url, name): name 
            for name in cube_names
        }
        
        for future in as_completed(future_to_cube):
            name, rules = future.result()
            rules_map[name] = rules

    print("Analyzing Rules and Dependencies...")
    
    all_edges = []
    all_cubes_set = set(cube_names)

    # 3. Process & Enrich Data
    for name in cube_names:
        data = cubes_data[name]
        rules = rules_map.get(name, "")
        data['rules_text'] = rules
        data['hasRules'] = bool(rules.strip())
        
        # A. Analyze Rules
        stats = analyse_rules(rules)
        data['rules_stats'] = stats
        data['complexity'] = calculate_complexity_score(stats)
        
        # B. Determine Type & Color (Generic Prefix Logic)
        c_type, c_color = classify_and_get_color(name)
        data['type'] = c_type
        data['color'] = c_color
        
        # C. Determine Description (Rules Header Fallback)
        header = extract_rules_header(rules)
        if header:
            data['desc'] = header
            data['descSource'] = 'rules_header'
        else:
            data['desc'] = f'{name} — No description found.'
            data['descSource'] = 'missing'
        
        # D. Find Dependencies
        deps = find_db_references(name, rules, all_cubes_set)
        all_edges.extend(deps)

    # 4. Build Graph Links (From/To)
    for edge in all_edges:
        src, tgt = edge['source'], edge['target']
        if src in cubes_data and tgt in cubes_data:
            if tgt not in cubes_data[src]['to']: cubes_data[src]['to'].append(tgt)
            if src not in cubes_data[tgt]['from']: cubes_data[tgt]['from'].append(src)

    # 5. Architecture Score
    score = 100
    for name, c in cubes_data.items():
        if c['descSource'] == 'missing': score -= 3
        if c['complexity'] > 300: score -= 10
        elif c['complexity'] > 150: score -= 5
        elif c['complexity'] > 60: score -= 2
    
    # Penalize backwards edges
    for edge in all_edges:
        src, tgt = edge['source'], edge['target']
        if src in cube_names and tgt in cube_names:
            if cube_names.index(src) > cube_names.index(tgt): score -= 3
    
    score = max(0, min(100, score))

    # 6. Construct Final JSON (Cytoscape Format)
    nodes = []
    for name, data in cubes_data.items():
        nodes.append({
            "data": {
                "id": name,
                "label": name,
                "type": data['type'],
                "color": data['color'],
                "complexity": data['complexity'],
                "desc": data['desc'],
                "dims": data['dims']
            }
        })

    edges_cyto = []
    for e in all_edges:
        # Only add edge if both nodes are in our final set
        if e['source'] in cubes_data and e['target'] in cubes_data:
            edges_cyto.append({
                "data": {
                    "source": e['source'],
                    "target": e['target']
                }
            })

    model = {
        "meta": {
            "extractedAt": datetime.now(timezone.utc).isoformat(),
            "cubeCount": len(nodes),
            "archScore": score
        },
        "elements": {
            "nodes": nodes,
            "edges": edges_cyto
        }
    }

    return model

# ── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract TM1 model to JSON for Generic CubeMap')
    parser.add_argument('--prefix', default='', help='Filter cubes by prefix (e.g. CST)')
    parser.add_argument('--out', default='tm1_model.json', help='Output filename')
    args = parser.parse_args()

    model = extract_model(prefix_filter=args.prefix)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(model, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Extraction Complete.")
    print(f"   Nodes: {len(model['elements']['nodes'])}")
    print(f"   Edges: {len(model['elements']['edges'])}")
    print(f"   Arch Score: {model['meta']['archScore']}/100")
    print(f"   Output: {args.out}")
