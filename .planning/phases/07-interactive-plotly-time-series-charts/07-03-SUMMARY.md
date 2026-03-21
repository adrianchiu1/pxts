---
phase: 07-interactive-plotly-time-series-charts
plan: "03"
subsystem: plots
tags:
  - plotly
  - annotations
  - add_annotation
  - tsplot
  - tsplot_dual
dependency_graph:
  requires:
    - "07-02"
  provides:
    - annotation processing in _plot_ts_plotly and _plot_ts_dual_plotly
    - add_annotation() public helper
    - annotations= validation in _validate_plot_params
  affects:
    - src/pxts/plots.py
    - src/pxts/__init__.py
tech_stack:
  added: []
  patterns:
    - "y auto-lookup via to_pytimedelta() for nearest-timestamp matching"
    - "showarrow=False floating label with bgcolor for readability"
    - "secondary_y_cols routing for dual-axis annotation yref"
key_files:
  created:
    - tests/_verify_07_03.py
  modified:
    - src/pxts/plots.py
    - src/pxts/__init__.py
decisions:
  - "_validate_plot_params gains annotations= parameter: validates list-of-dicts with x and text keys"
  - "y auto-lookup uses to_pytimedelta() list comprehension — TimedeltaIndex.abs() not available on all pandas versions"
  - "add_annotation() places annotation at yref=paper, y=0.5 when y is None — caller should supply y for accurate positioning"
  - "secondary_y_cols routing: col in secondary_y_cols maps to yref=y2 in dual-axis annotations"
metrics:
  duration: "6 min"
  completed_date: "2026-03-17"
  tasks_completed: 2
  files_modified: 2
---

# Phase 07 Plan 03: Annotation Processing and add_annotation() Summary

**One-liner:** Annotation processing wired into both Plotly renderers with y auto-lookup and a standalone `add_annotation()` helper exported from the pxts package.

## What Was Built

### _validate_plot_params annotations validation
- Added `annotations=None` parameter to `_validate_plot_params`
- Validates: must be list or None; each item must be dict with "x" and "text" keys
- Clear ValueError messages naming the failing parameter and item index
- Both `tsplot()` and `tsplot_dual()` callers now forward `annotations=annotations`

### _apply_plotly_annotations() private helper
- Accepts `fig`, `annotations`, `df`, `cols`, `secondary_y_cols=None`
- For each annotation dict: converts x to `pd.Timestamp`, resolves col (defaults to `cols[0]`)
- y auto-lookup: finds nearest row using `to_pytimedelta()` list comprehension
- Routes `yref` to "y2" when `col in secondary_y_cols` (dual-axis support)
- Adds annotation with `showarrow=False`, `bgcolor="rgba(255,255,255,0.7)"`, `yanchor="bottom"`

### Wiring into renderers
- `_plot_ts_plotly`: `_apply_plotly_annotations(fig, annotations, df, cols)` after vlines block
- `_plot_ts_dual_plotly`: `_apply_plotly_annotations(fig, annotations, df, left + right, secondary_y_cols=right)` after vlines block

### add_annotation() public function
- Signature: `add_annotation(fig, x, y=None, text='', col=None)`
- When `y=None`: uses `yref="paper"`, `y_val=0.5`
- When `y` provided: uses `yref="y"`, `y_val=y`
- Modifies fig in place; returns None
- Exported via `__init__.py` and added to `__all__`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed TimedeltaIndex.abs() AttributeError**
- **Found during:** Task 1 verify script execution
- **Issue:** `(df.index - x_ts).abs().argmin()` fails — `TimedeltaIndex` has no `.abs()` method
- **Fix:** Replaced with `to_pytimedelta()` list comprehension: `idx = (df.index - x_ts).to_pytimedelta(); idx = [abs(d) for d in idx]; nearest_pos = idx.index(min(idx))`
- **Files modified:** src/pxts/plots.py
- **Commit:** 0f7d1f9

## Test Results

- Verify script `tests/_verify_07_03.py`: PASSED
- Full regression: 126 tests passed (up from 56 at phase start — suite grew in earlier phases)

## Commits

| Task | Hash    | Message |
|------|---------|---------|
| 1    | 0f7d1f9 | feat(07-03): implement annotation processing in Plotly renderers |
| 2    | ee6bea4 | feat(07-03): export add_annotation via __init__.py |

## Self-Check: PASSED

- src/pxts/plots.py: FOUND
- src/pxts/__init__.py: FOUND
- tests/_verify_07_03.py: FOUND
- 07-03-SUMMARY.md: FOUND
- commit 0f7d1f9: FOUND
- commit ee6bea4: FOUND
