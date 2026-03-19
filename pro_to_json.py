"""
pro_to_json.py
==============
Converts TM1 TurboIntegrator .pro files to the JSON format required
by the TM1 REST API (TM1 Server 12 / Planning Analytics).

Usage:
    Single file:  python pro_to_json.py --file path/to/process.pro
    Folder:       python pro_to_json.py --src_folder ./pro_files --out_folder ./json_files

Folder defaults (if no args given):
    Source : ./pro_files
    Output : ./json_files
"""

import os
import re
import json
import argparse
from ti_lint import lint_json_file

# ---------------------------------------------------------------------------
# .pro field code reference
# ---------------------------------------------------------------------------
# 602  = Process name
# 560  = Parameter count
# 561  = Parameter types  (1=Numeric, 2=String)
# 590  = Parameter default values
# 637  = Parameter prompts
# 572  = Prolog code  (code length prefix, then code block)
# 573  = Metadata code
# 574  = Data code      (note: some versions use 574)
# 575  = Epilog code
# 577-582 = Variable definitions (name/type/start/end/position etc.)
# 564  = Datasource type
# 565  = Datasource name/path
# 566  = Delimiter
# 567  = Thousands separator
# 568  = Quote character
# 569  = Header rows
# 592  = Number of data rows to skip
# 580  = Cube name (for cube datasource)
# 581  = View name (for cube datasource)
# ---------------------------------------------------------------------------

PARAM_TYPE_MAP = {
    '1': 'Numeric',
    '2': 'String'
}

DATASOURCE_TYPE_MAP = {
    '0': 'None',
    '1': 'TM1CubeView',
    '2': 'Subset',
    '3': 'ODBC',
    '4': 'ASCII',          # plain text/CSV file
    '5': 'TM1DimensionSubset',
    '6': 'TM1File',
    '8': 'View',
}


def read_pro_file(filepath: str) -> str:
    """Read a .pro file, handling BOM and various encodings."""
    for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Cannot decode file: {filepath}")


def extract_field(lines: list, code: str) -> str:
    """
    Return the value for a given numeric field code.
    Handles:
      - Inline:  602,"SomeName"   or  566,","
      - Bare:    566,
      - Multi-line code blocks prefixed with the code and a character count.
    """
    prefix = f"{code},"
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(prefix):
            value = stripped[len(prefix):]
            # Strip surrounding quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            return value
    return ''


def extract_code_block(lines: list, code: str) -> str:
    """
    Extract a multi-line TI code block.

    The .pro format is:   <code>,<char_count>
                          <actual code lines ...>
                          <next_section_code>,<value>

    IMPORTANT: The char_count in the header is NOT reliable — in TM1 12 it
    often reflects only the first sub-section, not the full procedure.
    Instead we read all lines between this section marker and the NEXT
    numeric section marker (a line that starts with a pure integer followed
    by a comma, e.g. "573," or "575,27").

    We then strip the trailing newline TM1 leaves before the next marker.
    """
    # Regex: a line that IS a numeric .pro field marker
    section_marker = re.compile(r'^\d{3,4},')

    prefix = f"{code},"
    start_idx = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(prefix):
            # Verify the remainder is numeric (char count / value)
            remainder = stripped[len(prefix):]
            start_idx = i
            break

    if start_idx is None:
        return ''

    # Collect lines from start_idx+1 until the next section marker
    block_lines = []
    for j in range(start_idx + 1, len(lines)):
        if section_marker.match(lines[j].strip()):
            break
        block_lines.append(lines[j])

    # Join preserving original line endings, strip one trailing newline
    result = '\n'.join(block_lines)
    # Remove a single trailing newline that TM1 adds before the next marker
    if result.endswith('\n'):
        result = result[:-1]
    return result


def extract_param_list(lines: list, code: str) -> list:
    """
    Return a list of raw values for list-style fields that repeat per param.
    These appear as one value per line after the  <code>,<count>  header line.
    """
    prefix = f"{code},"
    results = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(prefix):
            try:
                count = int(stripped[len(prefix):].strip())
            except ValueError:
                return results
            for j in range(1, count + 1):
                if i + j < len(lines):
                    results.append(lines[i + j].strip())
            break
    return results


def extract_param_defaults(lines: list) -> list:
    """
    590,<count>
    pName,value          <- numeric default (no quotes)
    pName,"value"        <- string default (quoted)
    """
    results = []
    prefix = '590,'
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(prefix):
            try:
                count = int(stripped[len(prefix):].strip())
            except ValueError:
                return results
            for j in range(1, count + 1):
                if i + j < len(lines):
                    raw = lines[i + j].strip()
                    # Split on first comma only
                    comma_idx = raw.find(',')
                    if comma_idx == -1:
                        results.append({'name': raw, 'value': ''})
                    else:
                        name = raw[:comma_idx]
                        val  = raw[comma_idx + 1:]
                        if val.startswith('"') and val.endswith('"'):
                            val = val[1:-1]
                        results.append({'name': name, 'value': val})
            break
    return results


def extract_param_prompts(lines: list) -> list:
    """
    637,<count>
    pName,"prompt text"
    """
    results = []
    prefix = '637,'
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(prefix):
            try:
                count = int(stripped[len(prefix):].strip())
            except ValueError:
                return results
            for j in range(1, count + 1):
                if i + j < len(lines):
                    raw = lines[i + j].strip()
                    comma_idx = raw.find(',')
                    if comma_idx == -1:
                        results.append({'name': raw, 'prompt': ''})
                    else:
                        name   = raw[:comma_idx]
                        prompt = raw[comma_idx + 1:]
                        if prompt.startswith('"') and prompt.endswith('"'):
                            prompt = prompt[1:-1]
                        results.append({'name': name, 'prompt': prompt})
            break
    return results


def build_parameters(lines: list) -> list:
    """Assemble the Parameters array from the .pro file."""
    # 560 = count, 561 = types, param names are bare lines after 560 header
    prefix_count = '560,'
    param_names  = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(prefix_count):
            try:
                count = int(stripped[len(prefix_count):].strip())
            except ValueError:
                break
            for j in range(1, count + 1):
                if i + j < len(lines):
                    param_names.append(lines[i + j].strip())
            break

    if not param_names:
        return []

    types    = extract_param_list(lines, '561')
    defaults = extract_param_defaults(lines)
    prompts  = extract_param_prompts(lines)

    # Build lookup dicts for defaults and prompts by name
    default_map = {d['name']: d['value'] for d in defaults}
    prompt_map  = {p['name']: p['prompt'] for p in prompts}

    parameters = []
    for idx, name in enumerate(param_names):
        type_code = types[idx] if idx < len(types) else '2'
        param_type = PARAM_TYPE_MAP.get(type_code, 'String')

        raw_value = default_map.get(name, '')
        if param_type == 'Numeric':
            try:
                value = float(raw_value) if '.' in str(raw_value) else int(raw_value)
            except (ValueError, TypeError):
                value = 0
        else:
            value = raw_value

        parameters.append({
            'Name':   name,
            'Type':   param_type,
            'Value':  value,
            'Prompt': prompt_map.get(name, '')
        })

    return parameters


def build_datasource(lines: list) -> dict:
    """Build the DataSource object from .pro fields."""
    ds_type_code = extract_field(lines, '564')
    ds_type      = DATASOURCE_TYPE_MAP.get(ds_type_code, 'None')

    datasource = {'Type': ds_type}

    if ds_type == 'None':
        return datasource

    # ASCII / file source
    if ds_type in ('ASCII', 'TM1File'):
        datasource['dataSourceNameForServer'] = extract_field(lines, '565')
        datasource['dataSourceNameForClient'] = extract_field(lines, '586')
        datasource['delimiter']               = extract_field(lines, '566') or ','
        datasource['decimalSeparator']        = extract_field(lines, '588') or '.'
        datasource['thousandSeparator']       = extract_field(lines, '589') or ','
        datasource['quoteCharacter']          = extract_field(lines, '568') or '"'
        try:
            datasource['headerRecords']       = int(extract_field(lines, '569') or 0)
        except ValueError:
            datasource['headerRecords']       = 0

    # ODBC source
    elif ds_type == 'ODBC':
        datasource['dataSourceNameForServer'] = extract_field(lines, '565')
        datasource['userName']                = extract_field(lines, '593')
        datasource['password']                = extract_field(lines, '594')
        datasource['query']                   = extract_field(lines, '595')

    # Cube view source
    elif ds_type in ('TM1CubeView', 'View'):
        datasource['cubeName']                = extract_field(lines, '580')
        datasource['viewName']                = extract_field(lines, '581')

    # Subset source
    elif ds_type in ('Subset', 'TM1DimensionSubset'):
        datasource['dimensionName']           = extract_field(lines, '582')
        datasource['subsetName']              = extract_field(lines, '583')

    return datasource


def pro_to_json(filepath: str) -> dict:
    """Main conversion: parse a .pro file and return a dict ready for json.dumps."""
    content = read_pro_file(filepath)
    lines   = content.splitlines()

    # Process name — strip surrounding quotes
    name = extract_field(lines, '602').strip('"')

    prolog   = extract_code_block(lines, '572')
    metadata = extract_code_block(lines, '573')
    data     = extract_code_block(lines, '574')
    epilog   = extract_code_block(lines, '575')

    parameters = build_parameters(lines)
    datasource = build_datasource(lines)

    process = {
        'Name':              name,
        'DataSource':        datasource,
        'Parameters':        parameters,
        'Variables':         [],          # Only needed for datasource variable mappings
        'PrologProcedure':   prolog,
        'MetadataProcedure': metadata,
        'DataProcedure':     data,
        'EpilogProcedure':   epilog
    }

    return process


def convert_file(src_path: str, out_path: str) -> None:
    """Convert a single .pro file and write to out_path as .json."""
    print(f"  Converting: {os.path.basename(src_path)}")
    try:
        # Delete existing JSON first to ensure clean write
        if os.path.exists(out_path):
            os.remove(out_path)
            print(f"  -> Deleted:  {os.path.basename(out_path)} (old version)")
        process_json = pro_to_json(src_path)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(process_json, f, indent=2, ensure_ascii=False)
        print(f"  -> Written:  {os.path.basename(out_path)}")
        lint_json_file(out_path)
    except Exception as e:
        print(f"  ERROR converting {src_path}: {e}")


def convert_folder(src_folder: str, out_folder: str) -> None:
    """Convert all .pro files in src_folder and write JSON to out_folder."""
    os.makedirs(out_folder, exist_ok=True)
    pro_files = [f for f in os.listdir(src_folder) if f.lower().endswith('.pro')]

    if not pro_files:
        print(f"No .pro files found in: {src_folder}")
        return

    print(f"\nFound {len(pro_files)} .pro file(s) in '{src_folder}'")
    for filename in sorted(pro_files):
        src_path = os.path.join(src_folder, filename)
        out_name = os.path.splitext(filename)[0] + '.json'
        out_path = os.path.join(out_folder, out_name)
        convert_file(src_path, out_path)

    print(f"\nDone. {len(pro_files)} file(s) converted -> '{out_folder}'")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert TM1 .pro files to TM1 REST API JSON format'
    )
    parser.add_argument('--file',       help='Single .pro file to convert')
    parser.add_argument('--src_folder', default='./pro_files',  help='Folder of .pro files (default: ./pro_files)')
    parser.add_argument('--out_folder', default='./json_files', help='Output folder for JSON (default: ./json_files)')
    args = parser.parse_args()

    if args.file:
        # Single file mode
        if not os.path.isfile(args.file):
            print(f"File not found: {args.file}")
        else:
            out_name = os.path.splitext(args.file)[0] + '.json'
            convert_file(args.file, out_name)
    else:
        # Folder mode
        convert_folder(args.src_folder, args.out_folder)
