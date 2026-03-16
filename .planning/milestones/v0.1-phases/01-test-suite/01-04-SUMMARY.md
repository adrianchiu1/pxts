---
phase: 01-test-suite
plan: 04
subsystem: testing
tags: [pytest, matplotlib, plotly, mocking, tsplot, tsplot_dual]

# Dependency graph
requires:
  - phase: 01-test-suite
    provides: "tests/ package with conftest.py fixtures (ts_df, bad_df)"
provides:
  - "Unit tests for tsplot covering matplotlib and plotly backends (7 + 5 tests)"
  - "Unit tests for tsplot_dual covering matplotlib and plotly backends (2 + 1 tests)"
  - "Validation path tests for pxtsValidationError and ValueError (3 tests)"
  - "18 passing tests in tests/test_plots.py"
affects: [01-05, 02-bug-fixes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "matplotlib.use('Agg') at module level before pyplot import for headless CI"
    - "Explicit backend= parameter bypasses get_backend() in tests — no patching needed"
    - "plt.close(fig) after each matplotlib test to prevent resource leaks"
    - "Class-based test grouping per backend (TestTsplotMatplotlib, TestTsplotPlotly, etc.)"

key-files:
  created:
    - tests/test_plots.py
  modified: []

key-decisions:
  - "Use explicit backend= parameter instead of patching get_backend() — simpler, more reliable, tests the public API directly"
  - "matplotlib.use('Agg') at module level — non-interactive backend required for headless test environments"
  - "Class-based grouping: TestTsplotMatplotlib, TestTsplotPlotly, TestTsplotDualMatplotlib, TestTsplotDualPlotly, TestValidation — clear ownership per backend"

patterns-established:
  - "Plot tests pass explicit backend= to avoid environment-dependent behavior"
  - "Plotly assertions check fig.data length (traces) and fig.layout properties"
  - "Matplotlib assertions check isinstance(fig, matplotlib.figure.Figure)"

requirements-completed: [TEST-04]

# Metrics
duration: 5min
completed: 2026-03-15
---

# Phase 1 Plan 04: test_plots.py — mocked backend tests for tsplot and tsplot_dual Summary

**18 pytest tests covering tsplot and tsplot_dual for both matplotlib (Agg) and plotly backends, with pxtsValidationError and ValueError validation path coverage**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-15T02:13:08Z
- **Completed:** 2026-03-15T02:18:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `tests/test_plots.py` with 18 tests organized across 5 classes
- Covered tsplot for matplotlib: default cols, explicit cols, title/subtitle, hlines (list and dict), vlines, unknown col error
- Covered tsplot for plotly: default cols, explicit cols, title, hlines (shape count), unknown col error
- Covered tsplot_dual for both backends: left/right axes, title/subtitle, dual-trace count verification
- Covered validation paths: pxtsValidationError (non-DatetimeIndex), ValueError (unknown cols and left axis)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write unit tests for tsplot and tsplot_dual** - `953fb01` (feat)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified

- `tests/test_plots.py` - 18 unit tests for tsplot and tsplot_dual across matplotlib and plotly backends

## Decisions Made

- Used explicit `backend=` parameter throughout — bypasses `get_backend()` entirely, no patching required, tests the public API cleanly
- `matplotlib.use("Agg")` at module level before any pyplot import — required for headless environments with no display server
- Closed matplotlib figures with `plt.close(fig)` after each test to prevent figure accumulation and resource warnings
- Verified plotly hlines produce `len(fig.layout.shapes) == 2` for two hline inputs — confirms rendering path exercised

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed pxts package in editable mode**
- **Found during:** Task 1 (running tests for the first time)
- **Issue:** `pxts` was not installed in the current Python environment; `from pxts.plots import tsplot` raised `ModuleNotFoundError`
- **Fix:** Ran `pip install -e ".[dev]"` from the project root
- **Files modified:** None (pip installation only)
- **Verification:** `python -m pytest tests/test_plots.py -x -q` passes with 18/18 after install
- **Committed in:** N/A (environment setup, no file change)

---

**Total deviations:** 1 auto-fixed (1 blocking — missing package install)
**Impact on plan:** Essential environment fix. No scope creep. No plan files changed.

## Issues Encountered

None beyond the missing package install (documented above as deviation).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All plots test coverage complete (TEST-04 satisfied)
- Remaining plan 01-05 can proceed immediately using the same fixture infrastructure
- No blockers

## Self-Check: PASSED

- FOUND: tests/test_plots.py
- FOUND: .planning/phases/01-test-suite/01-04-SUMMARY.md
- Commit 953fb01 verified in git log

---
*Phase: 01-test-suite*
*Completed: 2026-03-15*
