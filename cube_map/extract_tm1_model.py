"""
extract_tm1_model.py
────────────────────
Connects to TM1 V12 on-prem via TM1py and extracts the full cube model
into tm1_model.json — which the CubeMap diagram reads at load time.

Usage:
    python3 extract_tm1_model.py              # extract all cubes
    python3 extract_tm1_model.py --prefix CST # only cubes starting with CST

Output:
    tm1_model.json  (same directory — copy next to tm1_cube_lineage.html)

Run this script any time the model changes to refresh the diagram.
"""

import sys
import re
import json
import argparse
from datetime import datetime, timezone

# ── Path setup ───────────────────────────────────────────────────────────────
# Adjust this if tm1py_connect.py is in a different location
sys.path.insert(0, '/home/jdlove/tm1-governance')
from core.tm1py_connect import get_tm1_service, TM1_CONFIG


# ── Helpers ───────────────────────────────────────────────────────────────────

def classify_cube_type(cube_name: str, dims: list[str], has_rules: bool, rules_text: str) -> str:
    """
    Classify a cube into one of six types for colour coding in the diagram.
    Uses cube name conventions from your naming standard first,
    then falls back to rules/dimension analysis.
    """
    name_upper = cube_name.upper()

    # Name-convention hints (your standard: CST prefix + descriptive name)
    if 'RECONCILI' in name_upper:
        return 'recon'
    if any(x in name_upper for x in ['REPORT', 'P&L', 'PROFIT', 'LOSS']):
        return 'report'
    if 'DRIVER' in name_upper:
        return 'driver'
    if 'ALLOCATION' in name_upper:
        return 'allocation'
    if any(x in name_upper for x in ['GL INPUT', 'INPUT', 'LOAD', 'IMPORT']):
        return 'input'
    if any(x in name_upper for x in ['SERVICE LINE', 'COST ROLLUP', 'ROLL']):
        return 'rollup'

    # Rules-based fallback
    if not has_rules:
        return 'input'
    if rules_text and 'DB(' in rules_text.upper():
        return 'allocation'

    return 'input'


def extract_rules_header(rules_text: str) -> str:
    """Extract comment block from top of rules file (lines starting with #)."""
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
                continue  # allow blank lines within header
        else:
            break  # hit actual rules code
    return ' '.join(l for l in header_lines if l)


def analyse_rules(rules_text: str) -> dict:
    """Count rules metrics for complexity scoring."""
    if not rules_text:
        return {'total': 0, 'lines': 0, 'comments': 0, 'dbRefs': 0,
                'feeders': 0, 'ifs': 0, 'stet': 0, 'skip': 0}

    all_lines   = rules_text.split('\n')
    total       = len(all_lines)
    comments    = sum(1 for l in all_lines if l.strip().startswith('#'))
    blanks      = sum(1 for l in all_lines if l.strip() == '')
    rule_lines  = total - comments - blanks
    upper       = rules_text.upper()

    return {
        'total':    total,
        'lines':    rule_lines,
        'comments': comments,
        'dbRefs':   upper.count('DB('),
        'feeders':  sum(1 for l in all_lines if 'FEEDERS' in l.upper()),
        'ifs':      upper.count('\nIF(') + (1 if upper.startswith('IF(') else 0),
        'stet':     upper.count('STET'),
        'skip':     upper.count('SKIP'),
    }


def find_db_references(cube_name: str, rules_text: str) -> list[dict]:
    """Find all DB() calls in rules that reference other cubes."""
    if not rules_text:
        return []
    # DB("CubeName", ...) — capture the cube name in quotes
    pattern = r'DB\s*\(\s*["\']([^"\']+)["\']'
    matches = re.findall(pattern, rules_text, re.IGNORECASE)
    seen = set()
    edges = []
    for target in matches:
        key = (cube_name, target)
        if key not in seen and target.lower() != cube_name.lower():
            seen.add(key)
            edges.append({'source': target, 'target': cube_name, 'type': 'rules'})
    return edges


def get_cube_attribute(tm1, cube_name: str, attr: str) -> str:
    """Safely read a cube attribute — returns '' if not found."""
    try:
        val = tm1.cubes.get_attribute(cube_name, attr)
        return val or ''
    except Exception:
        return ''


def classify_dimension_kind(dim_name: str) -> str:
    """Classify a dimension as global / measure / control / cst."""
    if dim_name.startswith('}'):
        return 'control'
    name_upper = dim_name.upper()
    if name_upper.startswith('GBL '):
        return 'global'
    if 'MEASURE' in name_upper:
        return 'measure'
    return 'cst'


# ── Main extraction ───────────────────────────────────────────────────────────

def extract_model(prefix_filter: str = '') -> dict:
    print(f"\nConnecting to TM1 — {TM1_CONFIG['address']}:{TM1_CONFIG['port']}")
    print(f"Database: {TM1_CONFIG['database']}\n")

    with get_tm1_service() as tm1:
        print("✅ Connected\n")

        # 1. Get all cube names (exclude system cubes starting with })
        all_cube_names = [
            c for c in tm1.cubes.get_all_names()
            if not c.startswith('}')
        ]
        if prefix_filter:
            all_cube_names = [c for c in all_cube_names if c.upper().startswith(prefix_filter.upper())]

        print(f"Found {len(all_cube_names)} cubes{f' matching prefix \"{prefix_filter}\"' if prefix_filter else ''}\n")

        cubes_data = {}
        all_edges  = []

        for cube_name in all_cube_names:
            print(f"  Processing: {cube_name}")
            try:
                cube = tm1.cubes.get(cube_name)

                # Dimensions
                dims_raw = cube.dimensions  # list of dimension names in order
                dims = [
                    {'n': d, 'k': classify_dimension_kind(d)}
                    for d in dims_raw
                ]

                # Rules
                has_rules  = cube.has_rules
                rules_text = cube.rules.text if has_rules else ''
                rules_stats = analyse_rules(rules_text)

                # Description — try attributes first, then rules header, then blank
                desc1 = get_cube_attribute(tm1, cube_name, 'Description_1')
                desc2 = get_cube_attribute(tm1, cube_name, 'Description_2')
                desc3 = get_cube_attribute(tm1, cube_name, 'Description_3')
                desc_source = 'manual' if any([desc1, desc2, desc3]) else ''

                if not desc1:
                    # Try rules header
                    header = extract_rules_header(rules_text)
                    if header:
                        desc1 = header
                        desc_source = 'rules_header'
                    else:
                        desc1 = f'{cube_name} — description not yet set.'
                        desc_source = 'ai_inferred'

                description = ' '.join(filter(None, [desc1, desc2, desc3]))

                # Cube type classification
                cube_type = classify_cube_type(
                    cube_name, dims_raw, has_rules, rules_text
                )

                # DB() rule references → edges
                rule_edges = find_db_references(cube_name, rules_text)
                all_edges.extend(rule_edges)

                cubes_data[cube_name] = {
                    'type':       cube_type,
                    'desc':       description,
                    'descSource': desc_source,
                    'dims':       dims,
                    'rules':      rules_stats,
                    'hasRules':   has_rules,
                    'from':       [],   # filled in below
                    'to':         [],   # filled in below
                }

            except Exception as e:
                print(f"    ⚠️  Error processing {cube_name}: {e}")
                continue

        # 2. Build from/to from edges (only edges where both cubes are in scope)
        in_scope = set(cubes_data.keys())
        for edge in all_edges:
            src, tgt = edge['source'], edge['target']
            if src in in_scope and tgt in in_scope:
                if tgt not in cubes_data[src]['to']:
                    cubes_data[src]['to'].append(tgt)
                if src not in cubes_data[tgt]['from']:
                    cubes_data[tgt]['from'].append(src)

        # 3. Architecture score
        score = calculate_architecture_score(cubes_data, all_edges)

        model = {
            'meta': {
                'database':    TM1_CONFIG['database'],
                'server':      f"{TM1_CONFIG['address']}:{TM1_CONFIG['port']}",
                'extractedAt': datetime.now(timezone.utc).isoformat(),
                'cubeCount':   len(cubes_data),
                'archScore':   score,
            },
            'cubes': cubes_data,
        }

        print(f"\n✅ Extracted {len(cubes_data)} cubes")
        print(f"   Architecture score: {score}/100")
        return model


def calculate_architecture_score(cubes: dict, edges: list) -> int:
    """
    Score the model architecture 0-100.
    Penalises: undocumented cubes, very high complexity, circular-looking refs.
    Rewards:   clean left-to-right flow, documented cubes.
    """
    score = 100

    for name, c in cubes.items():
        # Penalise undocumented cubes
        if c['descSource'] == 'ai_inferred':
            score -= 3

        # Penalise very high complexity
        r = c['rules']
        complexity = r['lines'] + r['dbRefs']*5 + r['ifs']*3 + r['feeders']*2
        if complexity > 300:
            score -= 10
        elif complexity > 150:
            score -= 5
        elif complexity > 60:
            score -= 2

    # Penalise backwards edges (source appears after target alphabetically — rough heuristic)
    cube_names = list(cubes.keys())
    for edge in edges:
        src, tgt = edge['source'], edge['target']
        if src in cube_names and tgt in cube_names:
            if cube_names.index(src) > cube_names.index(tgt):
                score -= 3  # backwards reference

    return max(0, min(100, score))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract TM1 model to JSON for CubeMap diagram')
    parser.add_argument('--prefix', default='', help='Only extract cubes with this prefix (e.g. CST)')
    parser.add_argument('--out',    default='tm1_model.json', help='Output file path')
    args = parser.parse_args()

    model = extract_model(prefix_filter=args.prefix)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(model, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Written to: {args.out}")
    print(f"   Copy this file to the same folder as tm1_cube_lineage.html\n")

    # Quick summary
    print("── Cube summary ─────────────────────────────────────────")
    for name, c in model['cubes'].items():
        r = c['rules']
        conn = len(c['from']) + len(c['to'])
        print(f"  {name:<40} type={c['type']:<12} dims={len(c['dims'])}  "
              f"rules={r['lines']}  conn={conn}  src={c['descSource']}")
    print("─────────────────────────────────────────────────────────\n")
