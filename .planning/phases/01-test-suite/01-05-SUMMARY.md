---
phase: 01-test-suite
plan: 05
subsystem: testing
tags: [pytest, accessor, theme, matplotlib, plotly, pandas]

# Dependency graph
requires:
  - phase: 01-test-suite
    provides: "Shared fixtures (ts_df, bad_df, tmp_path) from tests/conftest.py"
provides:
  - "Unit tests confirming TsAccessor methods delegate correctly to pxts.core / pxts.io / pxts.plots"
  - "Unit tests confirming apply_theme() registers plotly template and mutates matplotlib rcParams"
  - "Isolation fixture (restore_rcparams) preventing theme test state leakage"
affects: [02-bug-fixes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Class-based test grouping (TestDelegation, TestErrorProtocol) for logical grouping of accessor tests"
    - "restore_rcparams fixture: save/restore matplotlib rcParams to prevent inter-test contamination"
    - "Import pxts.theme directly (not import pxts) to avoid import-time side effects before fixtures are active"

key-files:
  created:
    - tests/test_accessor.py
    - tests/test_theme.py
  modified: []

key-decisions:
  - "Import pxts.accessor at module level in test_accessor.py — idempotent registration, no fixture needed"
  - "Import from pxts.theme directly (not import pxts) in test_theme.py — avoids triggering apply_theme() before restore_rcparams fixture is active"
  - "restore_rcparams fixture is autouse=False — only applied where explicitly requested, not globally"

patterns-established:
  - "Delegation tests: verify return type and key property (e.g., index.tz not None) — not deep equality with standalone function"
  - "Theme isolation: save snapshot, yield, reset to rcParamsDefault then re-apply snapshot"

requirements-completed: [TEST-05, TEST-06]

# Metrics
duration: 1min
completed: 2026-03-15
---

# Phase 1 Plan 05: Test Accessor and Theme Summary

**18 pytest tests for TsAccessor delegation (all 6 methods + AttributeError protocol) and apply_theme() (plotly registration, matplotlib rcParams, idempotency, isolation)**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-15T01:33:16Z
- **Completed:** 2026-03-15T01:34:10Z
- **Tasks:** 1 (both files combined in single task per plan)
- **Files modified:** 2

## Accomplishments

- Created `tests/test_accessor.py` with 10 tests covering accessor availability, delegation of all 6 TsAccessor methods (set_tz, to_dense, infer_freq, write_ts, plot, plot_dual), and the pandas accessor contract (AttributeError on non-DatetimeIndex)
- Created `tests/test_theme.py` with 8 tests covering plotly template registration, matplotlib rcParams mutation, idempotency (calling apply_theme() twice), and isolation via restore_rcparams fixture
- All 18 tests pass: `pytest tests/test_accessor.py tests/test_theme.py -v` exits 0

## Task Commits

1. **Task 1: Write test_accessor.py and test_theme.py** - `bf2e523` (feat)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified

- `tests/test_accessor.py` - 10 tests: accessor availability, 6 delegation methods, AttributeError protocol for non-DatetimeIndex DataFrames
- `tests/test_theme.py` - 8 tests: plotly template registration, matplotlib rcParams, idempotency, isolation via restore_rcparams fixture

## Decisions Made

- Import `pxts.accessor` at module level rather than in a fixture — the `@register_dataframe_accessor` side effect is idempotent, so calling it once per test module is the right approach
- Import `from pxts.theme import apply_theme` (not `import pxts`) in test_theme.py — `pxts.__init__.py` calls `apply_theme()` at import time, which would mutate rcParams before the restore fixture activates
- `restore_rcparams` fixture uses `plt.rcParamsDefault` for a full reset before re-applying the snapshot — ensures any rcParam set by apply_theme() is cleanly removed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed pxts package (editable mode)**
- **Found during:** Test run (collection phase)
- **Issue:** `ModuleNotFoundError: No module named 'pxts'` — package not installed in the Python environment
- **Fix:** Ran `pip install -e ".[dev]"` from project root to install pxts in editable mode with all dev dependencies
- **Files modified:** None (environment change only)
- **Verification:** `python -c "import pxts; print('pxts imported OK')"` succeeded; all 18 tests passed
- **Committed in:** N/A (environment setup, no file changes)

---

**Total deviations:** 1 auto-fixed (1 blocking — missing package installation)
**Impact on plan:** Required for tests to run. No scope creep; no files modified.

## Issues Encountered

- `pxts` package was not installed in the Python environment — resolved via `pip install -e ".[dev]"` (Rule 3 auto-fix)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All five test modules (01-01 through 01-05) are now complete, providing full test coverage for Phase 2 bug fixes
- `pytest tests/` can be run to validate any Phase 2 changes against the full test suite
- No blockers

## Self-Check: PASSED

- FOUND: tests/test_accessor.py
- FOUND: tests/test_theme.py
- FOUND: .planning/phases/01-test-suite/01-05-SUMMARY.md
- Commit bf2e523 verified in git log

---
*Phase: 01-test-suite*
*Completed: 2026-03-15*
