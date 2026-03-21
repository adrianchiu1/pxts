---
phase: quick-4
plan: 4
subsystem: plots
tags: [axis-limits, tsplot, tsplot_dual, matplotlib, plotly, validation]
dependency_graph:
  requires: []
  provides: [ylim/xlim/ylim_lhs/ylim_rhs parameter handling in tsplot and tsplot_dual]
  affects: [src/pxts/plots.py, tests/test_plots.py]
tech_stack:
  added: []
  patterns: [_validate_axis_limit helper, int/float guard for date-like xlim values]
key_files:
  modified:
    - src/pxts/plots.py
    - tests/test_plots.py
decisions:
  - Reject bare int/float for xlim — pd.Timestamp accepts them as nanoseconds but they are not meaningful date-like user inputs; require str, pd.Timestamp, or datetime objects
  - Apply axis limits after tight_layout() in matplotlib so layout changes do not override them
  - _validate_axis_limit is a standalone helper (not folded into _validate_plot_params body) for clarity and reuse
metrics:
  duration: 8 min
  completed: "2026-03-16T04:30:13Z"
  tasks_completed: 1
  files_modified: 2
---

# Quick Task 4: Add ylim/xlim/ylim_lhs/ylim_rhs to tsplot and tsplot_dual — Summary

**One-liner:** Axis limit parameters (ylim, xlim, ylim_lhs, ylim_rhs) added to tsplot and tsplot_dual with validation and dual-backend support.

## What Was Built

`tsplot` and `tsplot_dual` now accept explicit axis limit parameters so researchers can zoom into a date range or y-axis band without mutating the returned figure.

### New parameters

| Function | Parameter | Description |
|----------|-----------|-------------|
| `tsplot` | `ylim` | Y-axis limits `[lo, hi]` or `(lo, hi)` |
| `tsplot` | `xlim` | X-axis date limits `[date1, date2]` |
| `tsplot_dual` | `ylim_lhs` | Left (primary) y-axis limits |
| `tsplot_dual` | `ylim_rhs` | Right (secondary) y-axis limits |
| `tsplot_dual` | `xlim` | X-axis date limits |

All parameters default to `None` (no limit applied — existing behaviour preserved).

### New code

- `_validate_axis_limit(value, name, is_date=False)` — validates type (list/tuple), length (2), and date-likeness (for xlim). Rejects bare int/float for date parameters.
- `_validate_plot_params` extended with `ylim`, `xlim`, `ylim_lhs`, `ylim_rhs` keyword parameters.
- `_plot_ts_mpl`, `_plot_ts_plotly`, `_plot_ts_dual_mpl`, `_plot_ts_dual_plotly` each updated to accept and apply the relevant limits.
- `import pandas as pd` added at module level (was previously absent).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add axis limit validation helper and update plots.py signatures | 29311dd | src/pxts/plots.py, tests/test_plots.py |

## Test Results

- 14 new tests added in `TestAxisLimits`
- 105 total tests, all passing, no regressions

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Tightened xlim date-like validation to reject bare int/float**
- **Found during:** Task 1 (GREEN phase — test_tsplot_xlim_not_date_raises failed)
- **Issue:** `pd.Timestamp(1)` silently accepts integer 1 as nanoseconds since epoch. The plan states `xlim=[1, 2]` should raise ValueError, but the naive `pd.Timestamp()` try/except passed without error.
- **Fix:** Added explicit `isinstance(element, (int, float))` guard before the `pd.Timestamp()` conversion attempt, raising ValueError immediately for bare numerics.
- **Files modified:** src/pxts/plots.py
- **Commit:** 29311dd

## Self-Check: PASSED

- src/pxts/plots.py: FOUND
- tests/test_plots.py: FOUND
- Commit 29311dd: FOUND
