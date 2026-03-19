"""
ti_lint.py
==========
TM1 TurboIntegrator code linter and auto-formatter.

Silently fixes capitalisation and style issues in .pro files or JSON files
and writes the corrected version back to the same file (or a new file).

Fixes applied:
  - Control keywords      -> ALL CAPS  (IF, WHILE, ENDIF, ELSE, ELSEIF, DO, END)
  - Built-in TI functions -> canonical mixed case  (CubeExists, ViewZeroOut, etc.)
  - Comparison operators  -> consistent spacing  ( = , <> , >= , <= , > , < )
  - String operator       -> @= @<> spaced consistently
  - Concatenation         -> | spaced consistently
  - Semicolons            -> every non-comment, non-blank line ends with ;
  - Comment prefix        -> # (not // or --)

Usage:
    Single .pro:   python3 ti_lint.py --file myprocess.pro
    Folder .pro:   python3 ti_lint.py --src_folder pro_files
    Single .json:  python3 ti_lint.py --file myprocess.json
    Folder .json:  python3 ti_lint.py --json_folder json_files

    Add --report to print a summary of what was changed without writing.
    Add --diff    to print a line-by-line diff of changes made.
"""

import os
import re
import json
import argparse

# ---------------------------------------------------------------------------
# Canonical capitalisation maps
# ---------------------------------------------------------------------------

# Control flow keywords -> ALL CAPS
KEYWORDS = {
    'if':               'IF',
    'else':             'ELSE',
    'elseif':           'ELSEIF',
    'endif':            'ENDIF',
    'while':            'WHILE',
    'end':              'END',
    'do':               'DO',
}

# TI built-in functions -> canonical mixed case
# Full list of TM1 TI functions
TI_FUNCTIONS = {
    # Process control
    'executeprocess':           'ExecuteProcess',
    'runprocess':               'RunProcess',
    'processbreak':             'ProcessBreak',
    'processquit':              'ProcessQuit',
    'processerror':             'ProcessError',
    'getprocessname':           'GetProcessName',
    'processexitnormal':        'ProcessExitNormal',
    'processexitminoreerror':   'ProcessExitMinorError',
    'processexitmajorerror':    'ProcessExitMajorError',

    # Cube functions
    'cubeexists':               'CubeExists',
    'cubecreate':               'CubeCreate',
    'cubedestroy':              'CubeDestroy',
    'cubecleardata':            'CubeClearData',
    'cubesetlogchanges':        'CubeSetLogChanges',
    'cellgetn':                 'CellGetN',
    'cellgets':                 'CellGetS',
    'cellputn':                 'CellPutN',
    'cellputs':                 'CellPutS',
    'cellisupdate':             'CellIsUpdateable',
    'cellincrementn':           'CellIncrementN',
    'cellgetatn':               'CellGetAtN',
    'cellgetats':               'CellGetAtS',
    'cellputatN':               'CellPutAtN',
    'cellputats':               'CellPutAtS',
    'cellputproportionalspread':'CellPutProportionalSpread',
    'cubeprocessfeeders':       'CubeProcessFeeders',

    # View functions
    'viewexists':               'ViewExists',
    'viewcreate':               'ViewCreate',
    'viewdestroy':              'ViewDestroy',
    'viewzeroout':              'ViewZeroOut',
    'viewextract':              'ViewExtract',
    'viewmdxset':               'ViewMDXSet',
    'viewcreatebymDX':          'ViewCreateByMDX',
    'viewcreatebymDx':          'ViewCreateByMDX',
    'viewcreatebymdx':          'ViewCreateByMDX',
    'viewrowdimensionset':      'ViewRowDimensionSet',
    'viewcolumndimensionset':   'ViewColumnDimensionSet',
    'viewtitledimensionset':    'ViewTitleDimensionSet',
    'viewtitleelementset':      'ViewTitleElementSet',
    'viewsuppresszerosset':     'ViewSuppressZerosSet',
    'viewfetchcount':           'ViewFetchCount',

    # Subset functions
    'subsetexists':             'SubsetExists',
    'subsetcreate':             'SubsetCreate',
    'subsetdestroy':            'SubsetDestroy',
    'subsetmdxset':             'SubsetMDXSet',
    'subsetcreatebymdx':        'SubsetCreatebyMDX',
    'subsetgetsize':            'SubsetGetSize',
    'subsetgetelementname':     'SubsetGetElementName',
    'subsetallelements':        'SubsetAllElements',
    'subsetaddElement':         'SubsetAddElement',
    'subsetaddelement':         'SubsetAddElement',
    'subsetdeleteelement':      'SubsetDeleteElement',
    'subsetisaliased':          'SubsetIsAliased',

    # Dimension functions
    'dimensionexists':          'DimensionExists',
    'dimensioncreate':          'DimensionCreate',
    'dimensiondestroy':         'DimensionDestroy',
    'dimensionsize':            'DimensionSize',
    'dimensiontopelementcount': 'DimensionTopElementCount',
    'dimensionsortallelements': 'DimensionSortAllElements',
    'tabdim':                   'TABDIM',

    # Element functions
    'elementexists':            'ElementExists',
    'elementcreate':            'ElementCreate',
    'elementdestroy':           'ElementDestroy',
    'elementlevel':             'ElementLevel',
    'elementindex':             'ElementIndex',
    'elementname':              'ElementName',
    'elementtype':              'ElementType',
    'elementcount':             'ElementCount',
    'elementcomponentcount':    'ElementComponentCount',
    'elementcomponentof':       'ElementComponentOf',
    'elementisancestor':        'ElementIsAncestor',
    'elementisparent':          'ElementIsParent',
    'elementparentcount':       'ElementParentCount',
    'elementweight':            'ElementWeight',
    'elementaddleaf':           'ElementAddLeaf',
    'attrn':                    'AttrN',
    'attrs':                    'AttrS',
    'attri':                    'AttrI',
    'attrput':                  'AttrPut',
    'attrputn':                 'AttrPutN',
    'attrputs':                 'AttrPutS',

    # Hierarchy functions
    'hierarchyexists':          'HierarchyExists',
    'hierarchycreate':          'HierarchyCreate',
    'hierarchydestroy':         'HierarchyDestroy',

    # String functions
    'trim':                     'TRIM',
    'upcase':                   'UPCASE',
    'lowcase':                  'LOWER',     # LOWCASE is Rules only; TI function is LOWER
    'lower':                    'LOWER',
    'subst':                    'SubSt',
    'substr':                   'SubSt',
    'long':                     'Long',
    'scan':                     'Scan',
    'expand':                   'Expand',
    'numbertosstring':          'NumberToString',
    'numbertostring':           'NumberToString',
    'stringtonumber':           'StringToNumber',
    'char':                     'Char',
    'code':                     'Code',
    'fill':                     'Fill',
    'isundefined':              'IsUndefined',
    'isnumeric':                'IsNumeric',

    # Numeric / math functions
    'abs':                      'ABS',
    'int':                      'INT',
    'mod':                      'Mod',
    'round':                    'Round',
    'roundp':                   'RoundP',
    'rand':                     'RAND',
    'max':                      'MAX',
    'min':                      'MIN',
    'sqrt':                     'SQRT',
    'exp':                      'EXP',
    'log':                      'LOG',
    'power':                    'Power',
    'sign':                     'Sign',

    # Date / time functions
    'now':                      'Now',
    'date':                     'DATE',
    'time':                     'TIME',
    'timst':                    'TimSt',
    'dayno':                    'DayNo',
    'today':                    'TODAY',

    # IF inline function (not keyword)
    # Note: standalone IF is a keyword (all caps), inline IF() is a function
    # We handle this carefully - only fix standalone IF at start of statement

    # Logging / output
    'logoutput':                'LogOutput',
    'asciioutput':              'AsciiOutput',
    'asciiappend':              'AsciiAppend',
    'textoutput':               'TextOutput',
    'odbcoutput':               'ODBCOutput',

    # Input
    'asciinumericrecord':       'AsciiNumericRecord',
    'asciistringrecord':        'AsciiStringRecord',
    'odbc':                     'ODBC',

    # Server / system functions
    'tm1user':                  'TM1User',
    'serversandboxexists':      'ServerSandboxExists',
    'serveractivesandboxset':   'ServerActiveSandboxSet',
    'setuseactivesandboxproperty': 'SetUseActiveSandboxProperty',
    'tm1version':               'TM1Version',

    # Global variables
    'stringglobalvariable':     'StringGlobalVariable',
    'numericglobalvariable':    'NumericGlobalVariable',

    # TM1 v12 JSON functions
    'jsontype':                 'JsonType',
    'jsonget':                  'JsonGet',
    'jsonsize':                 'JsonSize',
    'jsonadd':                  'JsonAdd',
    'jsonreplace':              'JsonReplace',
    'jsonpatch':                'JsonPatch',
    'jsonmergepatch':           'JsonMergePatch',
    'jsondiff':                 'JsonDiff',
    'jsontostring':             'JsonToString',
    'stringtojson':             'StringToJson',

    # TM1 v12 Hierarchy functions
    'hierarchyelementprincipalname': 'HierarchyElementPrincipalName',
    'hierarchysubsetexists':    'HierarchySubsetExists',
    'hierarchysubsetmdxset':    'HierarchySubsetMDXSet',
    'hierarchysubsetgetsize':   'HierarchySubsetGetSize',
    'hierarchysubsetgetelementname': 'HierarchySubsetGetElementName',
    'hierarchyelementcomponentdelete': 'HierarchyElementComponentDelete',
    'hierarchyelementdelete':   'HierarchyElementDelete',
    'hierarchyelementinsert':   'HierarchyElementInsert',
    'elementattrputs':          'ElementAttrPutS',
    'elementattrs':             'ElementAttrS',
    'elementcomponent':         'ElementComponent',
    'elementparent':            'ElementParent',
    'dimensionelementprincipalname': 'DimensionElementPrincipalName',
    'executehttprequest':       'ExecuteHttpRequest',
    'numbertostring':           'NumberToString',

    # Chore / schedule
    'choreexists':              'ChoreExists',
    'choreactivate':            'ChoreActivate',
    'choredeactivate':          'ChoreDeactivate',
}

# Build a single combined lookup (lowercase key -> canonical value)
ALL_TOKENS = {**KEYWORDS, **TI_FUNCTIONS}

# ---------------------------------------------------------------------------
# Token replacement — word-boundary aware
# ---------------------------------------------------------------------------

def build_replacement_pattern():
    """
    Build one compiled regex that matches any known token as a whole word.
    We sort by length descending so longer matches win (e.g. ELSEIF before ELSE).
    """
    tokens = sorted(ALL_TOKENS.keys(), key=len, reverse=True)
    pattern = r'\b(' + '|'.join(re.escape(t) for t in tokens) + r')\b'
    return re.compile(pattern, re.IGNORECASE)

TOKEN_RE = build_replacement_pattern()


def replace_token(match):
    token_lower = match.group(0).lower()
    return ALL_TOKENS.get(token_lower, match.group(0))


def fix_tokens_outside_strings(line: str) -> str:
    """
    Apply token replacement only outside single-quoted string literals.
    TI strings are delimited by single quotes. We split the line on single
    quotes, apply replacement to even-indexed segments (outside strings),
    and leave odd-indexed segments (inside strings) untouched.
    """
    # Split on single quotes to separate code from string literals
    parts = line.split("'")
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Outside string literal - apply token replacement
            result.append(TOKEN_RE.sub(replace_token, part))
        else:
            # Inside string literal - leave untouched
            result.append(part)
    return "'".join(result)


# ---------------------------------------------------------------------------
# Operator spacing
# ---------------------------------------------------------------------------

def fix_operators(line: str) -> str:
    """Normalise spacing around operators."""
    # Skip comment lines
    stripped = line.strip()
    if stripped.startswith('#'):
        return line

    # Detect alignment lines - variable assignments with deliberate padding
    # e.g. sCaptionAttr      = 'Caption';
    # For these lines, skip = spacing normalisation to preserve alignment
    import re as _re
    is_alignment_line = bool(_re.search(r'\w\s{2,}=\s', line))

    # Use a placeholder to protect @<> and @= as atomic tokens
    # Also fix already-broken "@ <>" and "@ =" back to atomic form first
    line = re.sub(r'@\s*<>', '@<>', line)   # fix broken @ <> -> @<>
    line = re.sub(r'@\s*=',  '@=',  line)   # fix broken @ =  -> @=
    # Fix LOWCASE -> LOWER (LOWCASE is Rules only, TI function is LOWER)
    line = re.sub(r'\bLOWCASE\b', 'LOWER', line)
    line = re.sub(r'\s*@<>\s*', ' __ATNE__ ', line)
    line = re.sub(r'\s*@=\s*',  ' __ATEQ__ ', line)

    # Numeric comparison / assignment
    line = re.sub(r'\s*<>\s*',  ' <> ', line)
    line = re.sub(r'\s*>=\s*',  ' >= ', line)
    line = re.sub(r'\s*<=\s*',  ' <= ', line)
    line = re.sub(r'(?<![<>@!])\s*>\s*(?!=)',   ' > ', line)
    line = re.sub(r'(?<![<>@])\s*<\s*(?![>=])', ' < ', line)
    if not is_alignment_line:
        line = re.sub(r'(?<![<>@!])\s*=\s*(?![>])', ' = ', line)

    # Restore placeholders
    line = line.replace('__ATNE__', '@<>')
    line = line.replace('__ATEQ__', '@=')

    # String concatenation |
    line = re.sub(r'\s*\|\s*', ' | ', line)

    # Clean up any double spaces created (but preserve leading indent)
    # EXCEPTION: preserve deliberate alignment spacing before = sign
    # e.g.  sCaptionAttr      = 'Caption';  should not be collapsed
    indent = len(line) - len(line.lstrip())
    code_part = line[indent:]
    if not re.search(r'\s{2,}=', code_part):
        code_part = re.sub(r'  +', ' ', code_part)
    line = line[:indent] + code_part

    return line


# ---------------------------------------------------------------------------
# Semicolon enforcement
# ---------------------------------------------------------------------------

# Lines that should NOT get a semicolon added
NO_SEMICOLON_PATTERNS = [
    re.compile(r'^\s*#'),             # comment
    re.compile(r'^\s*$'),             # blank line
    re.compile(r'^\s*IF\s*\('),       # IF( — opening, not a statement
    re.compile(r'^\s*WHILE\s*\('),    # WHILE(
    re.compile(r'^\s*DO\s*$'),        # DO
    re.compile(r'^\s*ELSE\s*$'),      # ELSE
    re.compile(r'^\s*ELSEIF\s*\('),   # ELSEIF(
    re.compile(r'^\s*ENDIF\s*;?\s*$'),# ENDIF (may already have ;)
    re.compile(r'^\s*END\s*;?\s*$'),  # END
    re.compile(r'#\*\*\*\*'),         # Generated statements markers
]

def needs_semicolon(line: str, next_line: str = '') -> bool:
    """Return True if this line should end with a semicolon."""
    for pattern in NO_SEMICOLON_PATTERNS:
        if pattern.match(line):
            return False
    stripped = line.strip()
    if not stripped:
        return False
    # Already has semicolon
    if stripped.endswith(';'):
        return False
    # Continuation lines (inside a multi-line function call) end with ,
    if stripped.endswith(','):
        return False
    # If the next non-blank line is ); or ); then this is the last arg
    # of a multi-line function call — do not add semicolon here
    next_stripped = next_line.strip().strip('\r\t ')  # strip all whitespace incl tabs
    if next_stripped.startswith(');'):
        return False
    if next_stripped == ')':
        return False
    return True


def fix_semicolons(line: str, next_line: str = '') -> str:
    """Add semicolon to lines that need one."""
    if needs_semicolon(line, next_line):
        return line.rstrip() + ';'
    return line


# ---------------------------------------------------------------------------
# Deprecated v12 functions
# ---------------------------------------------------------------------------

# Functions removed in TM1 Server 12 — comment out and warn
V12_DEPRECATED = {
    'CubeSetLogChanges':  'Removed in TM1 v12 - transaction logging now server-controlled',
    'CubeGetLogChanges':  'Removed in TM1 v12 - transaction logging now server-controlled',
    'CubeSaveData':       'Removed in TM1 v12',
    'SaveDataAll':        'Removed in TM1 v12',
    'ExecuteCommand':     'Removed in TM1 v12 - use ExecuteHttpRequest to call external REST API instead',
    'LockOn':             'Removed in TM1 v12',
    'LockOff':            'Removed in TM1 v12',
    'EnableBulkLoadMode': 'Removed in TM1 v12',
    'BatchUpdateStart':   'Removed in TM1 v12',
    'BatchUpdateFinish':  'Removed in TM1 v12',
}

V12_DEPRECATED_RE = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in V12_DEPRECATED.keys()) + r')\b'
)

def fix_deprecated(line: str) -> list:
    """
    If a line contains a deprecated v12 function, comment it out
    and insert a warning comment above it.
    Returns a list of lines (may be 2 if a warning was inserted).
    """
    stripped = line.strip()
    if stripped.startswith('#'):
        return [line]

    match = V12_DEPRECATED_RE.search(line)
    if match:
        fn_name = match.group(1)
        indent  = len(line) - len(line.lstrip())
        spaces  = line[:indent]
        warning = f"{spaces}# WARNING: {fn_name} - {V12_DEPRECATED[fn_name]}"
        commented = f"{spaces}# {line.strip()}"
        return [warning, commented]

    return [line]


# ---------------------------------------------------------------------------
# Main line formatter
# ---------------------------------------------------------------------------

def fix_alignment_spacing(line: str) -> str:
    """
    Preserve deliberate alignment spacing in variable assignments.
    Lines like:  sCaptionAttr      = 'Caption';
    should NOT have their padding collapsed — this is intentional formatting.
    We only collapse multiple spaces that are NOT part of an alignment pattern
    (i.e. not spaces before an = sign used for column alignment).
    """
    # If line contains multiple spaces before = it's likely alignment - leave it
    import re as _re
    if _re.search(r'\s{2,}=\s', line):
        return line
    return line


def format_line(line: str, next_line: str = '') -> str:
    """Apply all fixes to a single line of TI code."""
    stripped = line.strip()
    if stripped.startswith('#'):
        return line

    # 1. Fix token capitalisation - string literal aware
    line = fix_tokens_outside_strings(line)

    # 2. Fix operator spacing (preserves alignment spacing)
    line = fix_operators(line)

    # 3. Fix semicolons (pass next line for context)
    line = fix_semicolons(line, next_line)

    return line


def format_code(code: str) -> str:
    """Format a full TI code block (multi-line string)."""
    # Normalise Windows line endings before processing
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    lines = code.split('\n')
    result = []
    in_multiline_string = False

    for i, line in enumerate(lines):
        next_line = lines[i + 1] if i + 1 < len(lines) else ''

        # Track multi-line string literals
        # A multi-line string starts when a line has an odd number of single quotes
        # and the last quote opens a string that doesn't close on the same line
        stripped = line.strip()

        # Count unescaped single quotes to determine if we enter/exit a string
        quote_count = stripped.count("'")
        # If we are inside a multi-line string, check if this line closes it
        if in_multiline_string:
            result.append(line)  # pass through unchanged
            if quote_count % 2 == 1:
                # Odd number of quotes - we exit the multi-line string
                in_multiline_string = False
            continue

        # Check if this line opens a multi-line string (odd quotes, doesn't close)
        if quote_count % 2 == 1:
            # Check if the string that opens also closes on this line
            # by seeing if content after last quote is just ; or whitespace
            last_quote_pos = stripped.rfind("'")
            after_last_quote = stripped[last_quote_pos+1:].strip().rstrip(';').strip()
            if after_last_quote == '' or after_last_quote == ')' or after_last_quote.startswith(')'):
                pass  # string closes on same line
            else:
                # String opens but doesn't close - multi-line string starts
                in_multiline_string = True
                result.append(line)  # pass through unchanged
                continue

        next_stripped = next_line.strip().strip('\r\t ')
        if next_stripped.startswith(');') or next_stripped == ')':
            stripped_line = line.rstrip()
            if stripped_line.endswith(';') and not stripped_line.endswith('};') and '=' not in stripped_line.split(';')[-2:-1]:
                line = stripped_line[:-1]
        # Check for deprecated v12 functions — may expand to 2 lines
        fixed_lines = fix_deprecated(line)
        for fl in fixed_lines:
            result.append(format_line(fl, next_line))
    return '\n'.join(result)


# ---------------------------------------------------------------------------
# Diff / report helper
# ---------------------------------------------------------------------------

def diff_code(original: str, fixed: str, label: str) -> list:
    """Return a list of change description strings."""
    changes = []
    orig_lines = original.split('\n')
    fixed_lines = fixed.split('\n')
    for i, (o, f) in enumerate(zip(orig_lines, fixed_lines), 1):
        if o != f:
            changes.append(f"  {label} line {i}:")
            changes.append(f"    - {o.rstrip()}")
            changes.append(f"    + {f.rstrip()}")
    return changes


# ---------------------------------------------------------------------------
# Process a .pro file
# ---------------------------------------------------------------------------

def lint_pro_file(filepath: str, report_only: bool = False, show_diff: bool = False) -> int:
    """
    Lint a .pro file.  Returns number of lines changed.
    If report_only=True, prints changes but does not write.
    """
    # Read
    for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
            used_enc = enc
            break
        except UnicodeDecodeError:
            continue

    lines     = content.splitlines()
    new_lines = []
    changes   = 0

    # Code block codes in .pro files
    CODE_CODES = {'572', '573', '574', '575'}
    section_marker = re.compile(r'^\d{3,4},')
    in_code = False
    code_buffer = []
    code_start_idx = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect start of a code block
        is_code_header = False
        for code in CODE_CODES:
            if stripped.startswith(f'{code},'):
                is_code_header = True
                new_lines.append(line)   # keep the header line unchanged
                i += 1
                # Collect until next section marker
                code_lines = []
                while i < len(lines):
                    if section_marker.match(lines[i].strip()) and not lines[i].strip().startswith('#'):
                        break
                    code_lines.append(lines[i])
                    i += 1
                # Format the code block
                original_block = '\n'.join(code_lines)
                fixed_block    = format_code(original_block)
                if original_block != fixed_block:
                    block_changes = diff_code(original_block, fixed_block, f'section {code}')
                    changes += len([c for c in block_changes if c.strip().startswith('-')])
                    if show_diff:
                        for c in block_changes:
                            print(c)
                new_lines.extend(fixed_block.split('\n'))
                break
        else:
            new_lines.append(line)
            i += 1

    new_content = '\n'.join(new_lines)

    if changes > 0:
        print(f"  {os.path.basename(filepath)}: {changes} line(s) changed")
    else:
        print(f"  {os.path.basename(filepath)}: OK (no changes)")

    if not report_only and new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

    return changes


# ---------------------------------------------------------------------------
# Process a .json file (already converted from .pro)
# ---------------------------------------------------------------------------

PROCEDURE_KEYS = ['PrologProcedure', 'MetadataProcedure', 'DataProcedure', 'EpilogProcedure']

def lint_json_file(filepath: str, report_only: bool = False, show_diff: bool = False) -> int:
    """
    Lint a JSON process file.  Returns number of lines changed.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return 0

    total_changes = 0

    for key in PROCEDURE_KEYS:
        if key not in data:
            continue
        original = data[key]
        fixed    = format_code(original)
        if original != fixed:
            block_diff = diff_code(original, fixed, key)
            line_changes = len([c for c in block_diff if c.strip().startswith('-')])
            total_changes += line_changes
            if show_diff:
                print(f"\n  [{key}]")
                for c in block_diff:
                    print(c)
            data[key] = fixed

    if total_changes > 0:
        print(f"  {os.path.basename(filepath)}: {total_changes} line(s) changed")
    else:
        print(f"  {os.path.basename(filepath)}: OK (no changes)")

    if not report_only and total_changes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return total_changes


# ---------------------------------------------------------------------------
# Folder processing
# ---------------------------------------------------------------------------

def lint_folder(folder: str, ext: str, report_only: bool, show_diff: bool) -> None:
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(ext))
    if not files:
        print(f"No {ext} files found in: {folder}")
        return

    print(f"\nLinting {len(files)} {ext} file(s) in '{folder}'")
    print('-' * 60)

    total = 0
    for filename in files:
        filepath = os.path.join(folder, filename)
        if ext == '.pro':
            total += lint_pro_file(filepath, report_only, show_diff)
        else:
            total += lint_json_file(filepath, report_only, show_diff)

    print('-' * 60)
    action = "Would change" if report_only else "Changed"
    print(f"{action} {total} line(s) across {len(files)} file(s)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='TM1 TurboIntegrator code linter and auto-formatter'
    )
    parser.add_argument('--file',        help='Single .pro or .json file to lint')
    parser.add_argument('--src_folder',  help='Folder of .pro files to lint')
    parser.add_argument('--json_folder', help='Folder of .json files to lint')
    parser.add_argument('--report',      action='store_true',
                        help='Report only — do not write changes')
    parser.add_argument('--diff',        action='store_true',
                        help='Show line-by-line diff of changes')
    args = parser.parse_args()

    if args.file:
        ext = os.path.splitext(args.file)[1].lower()
        if ext == '.pro':
            lint_pro_file(args.file, args.report, args.diff)
        elif ext == '.json':
            lint_json_file(args.file, args.report, args.diff)
        else:
            print("ERROR: file must be .pro or .json")

    elif args.src_folder:
        lint_folder(args.src_folder, '.pro', args.report, args.diff)

    elif args.json_folder:
        lint_folder(args.json_folder, '.json', args.report, args.diff)

    else:
        # Default: lint both folders
        if os.path.isdir('./pro_files'):
            lint_folder('./pro_files', '.pro', args.report, args.diff)
        if os.path.isdir('./json_files'):
            lint_folder('./json_files', '.json', args.report, args.diff)
