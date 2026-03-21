---
phase: quick-3
plan: 3
subsystem: plots
tags: [hlines, vlines, normalization, convenience, validation]
dependency_graph:
  requires: []
  provides: [scalar-hlines-vlines-normalization]
  affects: [src/pxts/plots.py, tests/test_plots.py]
tech_stack:
  added: []
  patterns: [normalize-before-validate]
key_files:
  created: []
  modified:
    - src/pxts/plots.py
    - tests/test_plots.py
decisions:
  - "_normalize_lines excludes bool via explicit isinstance(value, bool) guard — bool is subclass of int, so True/False would silently pass without the guard"
  - "Normalization happens before _validate_plot_params — validate function sees only list/dict/None, no changes needed there"
metrics:
  duration: "2 min"
  completed: "2026-03-16"
  tasks_completed: 1
  files_modified: 2
---

# Quick Task 3: Allow float or int for hlines/vlines Summary

**One-liner:** Scalar int/float hlines/vlines normalized to single-element list via _normalize_lines helper before validation, with bool explicitly excluded.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 (RED) | Add failing tests for scalar hlines/vlines | 57609a4 | tests/test_plots.py |
| 1 (GREEN) | Implement _normalize_lines and wire into tsplot/tsplot_dual | 3582058 | src/pxts/plots.py |

## Changes Made

### src/pxts/plots.py

- Added `_normalize_lines(value, name)` helper function (placed after constants, before `_validate_cols`):
  - If `value` is `int` or `float` AND NOT `bool` → return `[value]`
  - Otherwise → return `value` unchanged
- In `tsplot()`: call `_normalize_lines` for both `hlines` and `vlines` before `_validate_plot_params`
- In `tsplot_dual()`: same normalization before `_validate_plot_params`
- Updated `_validate_plot_params` docstring to note scalar normalization happens upstream

### tests/test_plots.py

- Replaced `test_tsplot_hlines_wrong_type_raises` (asserted 42.0 raises) with three new tests in `TestParameterTypeValidation`:
  - `test_hlines_scalar_float`: `tsplot(hlines=42.0)` succeeds, returns Figure
  - `test_hlines_scalar_int`: `tsplot(hlines=0)` succeeds, returns Figure (int zero)
  - `test_hlines_bool_raises`: `tsplot(hlines=True)` raises ValueError mentioning 'hlines'

## Verification

- `pytest tests/test_plots.py`: 29 passed (was 27 — net +2 tests)
- `pytest tests/`: 91 passed, 0 failures

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- `src/pxts/plots.py` contains `_normalize_lines` function
- `tests/test_plots.py` contains `test_hlines_scalar_float`, `test_hlines_scalar_int`, `test_hlines_bool_raises`
- Commits 57609a4 and 3582058 exist in git log
- All 91 tests pass
