# Calculation Trace — Implementation Summary

## What was built

The Trace tab in the detail panel now shows an end-to-end data lineage chain for a selected measure on a cube with rules. The trace combines three legs:

### 1. Rules leg (`_traceCombined`)
Walks `DB('SourceCube', ...)` references in rules text recursively. For a selected measure (e.g. "Net Income"), finds matching assignment lines and follows each DB() call to the source cube, then continues tracing that cube's rules for the same measure.

### 2. TI leg (`_traceCombined` TI section)
At each cube in the rules chain, finds TI processes that **write TO** that cube (from `cube.from` where `t === "ti"`). For each TI, traces what cubes it **reads FROM** (`tiData.from`), then continues the full combined trace on those input cubes.

### 3. ExecuteProcess leg (`_traceExecChain`)
For each TI encountered, scans its `tiCode` (prolog/metadata/data/epilog) for `ExecuteProcess('ProcessName', ...)` calls. Recursively traces each called process — what IT reads, writes, and what processes IT calls. Cycle detection via a shared visited set.

**Infrastructure split**: Executed processes with NO cube writes (utility calls like dimension management, security, subsets) are separated into a collapsed **Infrastructure calls** section at the bottom of the tree. Only processes that write to cubes stay in the main lineage chain.

## Tree shape

```
FCM Consolidation › Net Income
  ├── [Rules] DB('FCM Journal Investment Summary', ..., 'Net Income')
  │     └── [Rules] DB('FCM Journal Investment', ..., 'Amount')
  │           └── [TI] Data.Import.FCMJournalInvestmentSummary
  │                 ├── [Rules] FCM Transaction Source : Amount
  │                 │     └── ...
  │                 └── [Exec] Bedrock.Cube.ViewAndSubsets.Create
  │                       ├── reads:  FCM Transaction Source
  │                       └── writes: FCM Journal Investment Summary
  │                 reads:  FCM Journal Investment
  │                 writes: FCM Journal Investment Summary
  └── [TI]   Data.Import.FCMConsolidation.FCMTranslationJournal
              └── [Rules] FCM Translation Journal : Net Income
              reads:  FCM Translation Journal
              writes: FCM Consolidation
```

## Node types in tree

| Badge | Color | Meaning |
|-------|-------|---------|
| `Cube : Measure` | white (bold) | Root — the starting cube and measure |
| `[Rules]` | gold `#d29922` | DB() reference in rules text (clickable) |
| `[TI]`   | orange `#f78166` | TI process that writes to this cube (clickable) |
| `[Exec]` | purple `#a371f7` | ExecuteProcess call from a TI (clickable) |

Each node shows:
- Clickable name → navigates graph to that node
- Snippet (Rules nodes) — first 100 chars of the matching line
- reads/writes (TI/Exec nodes) — lists of cubes

## Guards

- **Max depth**: 5 hops (configurable in `_traceCombined` and `_traceExecChain`)
- **Cycle detection**: shared `visited` Set of cube+process IDs passed through the entire chain
- **Self-reference**: Rules skip `DB('SameCube', ...)` at each level

## No new data extraction needed

All data comes from existing fields in `tm1_model.json`:
- `rulesText` — for parsing DB() refs
- `from`/`to` arrays with `t: "ti"` — for TI→cube edges
- `tiCode` (prolog/metadata/data/epilog) — for scanning ExecuteProcess calls

## Files changed

- `cube_map/static/tm1_cube_lineage.html`:
  - `_traceMeasure` → `_traceCombined` (added TI leg)
  - Added `_findExecutedProcesses()` — scans TI code for ExecuteProcess calls
  - Added `_traceExecChain()` — recursive ExecuteProcess resolution
  - Updated `_renderTrace()` — handles both no-rules (TI-only) and has-rules paths
  - Updated `_renderTraceTree()` — added `ti` and `exec` node type rendering
