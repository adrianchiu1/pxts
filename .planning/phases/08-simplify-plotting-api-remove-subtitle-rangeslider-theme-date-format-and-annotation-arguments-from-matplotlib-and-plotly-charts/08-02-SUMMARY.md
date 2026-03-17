---
phase: 08-simplify-plotting-api-remove-subtitle-rangeslider-theme-date-format-and-annotation-arguments-from-matplotlib-and-plotly-charts
plan: "02"
subsystem: testing
tags: [pytest, plotly, matplotlib, test-cleanup]

# Dependency graph
requires:
  - phase: 08-01
    provides: simplified tsplot/tsplot_dual API (subtitle/rangeslider/theme/annotations removed)
provides:
  - test suite aligned with simplified plotting API — all 64 tests pass
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - tests/test_plots.py

key-decisions:
  - "TestPlotlyTemplate class introduced to preserve margin regression test after TestPhase7Theme deletion"
  - "date_format= kept in Plotly tests (TestTsplotPlotlyPhase6Fixes, TestPlotlyTickformatstops) — Plotly still supports it"

patterns-established: []

requirements-completed: []

# Metrics
duration: 2min
completed: 2026-03-17
---

# Phase 08 Plan 02: Update test_plots.py to match simplified API Summary

**Removed 152 lines of deleted-API tests (subtitle, rangeslider, theme, annotations) and rewrote 3 title tests — all 64 remaining tests pass**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-17T09:57:13Z
- **Completed:** 2026-03-17T09:59:13Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Rewrote 3 `test_title_and_subtitle` methods across `TestTsplotMatplotlib`, `TestTsplotPlotly`, and `TestTsplotDualMatplotlib` — removed `subtitle=` kwarg
- Deleted 4 rangeslider tests from `TestPhase7RangeNav`; updated class docstring to "Range selector buttons."
- Deleted entire `TestPhase7Theme` class; extracted `test_plotly_template_has_tighter_margins` into new `TestPlotlyTemplate` class
- Deleted entire `TestPhase7Annotations` class (10 tests)
- Removed `test_tsplot_subtitle_wrong_type_raises` and `test_tsplot_date_format_wrong_type_raises` from `TestParameterTypeValidation`
- All 64 remaining tests pass with no references to removed kwargs

## Task Commits

1. **Task 1: Remove deleted-API tests and update test_plots.py** - `325e808` (feat)

**Plan metadata:** _(docs commit to follow)_

## Files Created/Modified

- `tests/test_plots.py` - Removed 152 lines of tests for deleted API parameters; added `TestPlotlyTemplate` class

## Decisions Made

- `TestPlotlyTemplate` class introduced to preserve the margin regression test that was inside `TestPhase7Theme` before deletion
- `date_format=` tests in `TestTsplotPlotlyPhase6Fixes` and `TestPlotlyTickformatstops` left intact — Plotly still supports `date_format`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 8 API simplification complete: both plots.py changes (08-01) and test alignment (08-02) are done
- All tests pass; simplified API is verified

---
*Phase: 08-simplify-plotting-api*
*Completed: 2026-03-17*
