---
phase: 02-bug-fixes-and-dependencies
plan: 03
subsystem: plotting
tags: [adjustText, warnings, validation, matplotlib, UserWarning, ValueError]

# Dependency graph
requires:
  - phase: 01-test-suite
    provides: test_plots.py with 19 passing tests for tsplot/tsplot_dual
provides:
  - Once-per-session UserWarning when adjustText is absent (DEP-02)
  - Module-level _ADJUSTTEXT_WARNED flag in pxts.plots
  - _validate_plot_params helper for type-checking public API parameters (FIX-05)
  - ValueError with clear message for invalid hlines, vlines, title, subtitle, date_format types
affects: [future plot features, end-label behavior, API callers passing wrong types]

# Tech tracking
tech-stack:
  added: [warnings (stdlib, now imported in plots.py)]
  patterns:
    - Module-level once-per-session warning flag pattern (_ADJUSTTEXT_WARNED)
    - Centralized parameter type validation helper before dispatching to backends
    - TDD RED→GREEN for both warning behavior and ValueError behavior

key-files:
  created: []
  modified:
    - src/pxts/plots.py
    - tests/test_plots.py

key-decisions:
  - "hlines/vlines accept list, dict, or None in _validate_plot_params — dicts used for labeled reference lines, must not be rejected"
  - "stacklevel=2 in warnings.warn points the UserWarning at the tsplot/tsplot_dual call site (user-visible location)"
  - "_ADJUSTTEXT_WARNED mutated via global declaration inside _add_mpl_end_labels — module-level persistence across calls"

patterns-established:
  - "Module-level boolean flag for once-per-session warnings: declare at module level, mutate via global inside the function"
  - "Validate params immediately after validate_ts(df), before any cols validation or backend dispatch"

requirements-completed: [DEP-02, FIX-05]

# Metrics
duration: 5min
completed: 2026-03-15
---

# Phase 2 Plan 3: adjustText Warning and Parameter Type Validation Summary

**Once-per-session UserWarning for missing adjustText (DEP-02) and clear ValueError type validation at tsplot/tsplot_dual entry points (FIX-05) — 8 new tests, all 89 pass**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-15T06:56:03Z
- **Completed:** 2026-03-15T07:00:58Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `_ADJUSTTEXT_WARNED` module-level flag and once-per-session `UserWarning` in `_add_mpl_end_labels` — users now learn about the missing dep on first use instead of silently getting inferior layout
- Added `_validate_plot_params` helper covering hlines, vlines, title, subtitle, date_format — wrong types now raise clear `ValueError` at the call site instead of cryptic `NoneType is not iterable` deep inside helpers
- 8 new tests added (4 per task via TDD) — full suite remains green at 89 tests

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: once-per-session adjustText warning (DEP-02)** - `ad29049` (test)
2. **Task 1 GREEN: once-per-session adjustText warning (DEP-02)** - `7c6792e` (feat)
3. **Task 2 RED: parameter type validation (FIX-05)** - `7366258` (test)
4. **Task 2 GREEN: parameter type validation (FIX-05)** - `80e3aa1` (feat)

## Files Created/Modified

- `src/pxts/plots.py` - Added `import warnings`, `_ADJUSTTEXT_WARNED` flag, updated `_add_mpl_end_labels` except block, added `_validate_plot_params` helper, added validation calls in `tsplot` and `tsplot_dual`
- `tests/test_plots.py` - Added `TestAdjustTextWarning` and `TestParameterTypeValidation` classes with 8 new tests

## Decisions Made

- `hlines`/`vlines` accept `list`, `dict`, or `None` in `_validate_plot_params` — existing tests pass dicts for labeled reference lines, rejecting them would break the existing API
- `stacklevel=2` in `warnings.warn` ensures the warning points at `tsplot`/`tsplot_dual` in the user's traceback, not at `_add_mpl_end_labels`
- `_validate_plot_params` is called before `_validate_cols` and backend dispatch — type errors surface before any column lookup work

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Extended _validate_plot_params to accept dict for hlines/vlines**
- **Found during:** Task 2 (parameter type validation GREEN phase)
- **Issue:** Plan specified `list | None` for hlines/vlines, but existing test `test_hlines_as_dict` passes `hlines={"low": 1.0, "high": 4.0}` and the plan frontmatter `must_haves` note states "hlines/vlines accept list | None (not dict — dicts are used internally but not validated here per user decision)" — the intent was to not reject dicts, only primitives (float, int, str)
- **Fix:** Updated isinstance check to `(list, dict, type(None))` so dicts pass through; error message still says "must be list or None" to communicate the public contract
- **Files modified:** src/pxts/plots.py
- **Verification:** test_hlines_as_dict passes, test_tsplot_hlines_wrong_type_raises still raises for float
- **Committed in:** 80e3aa1 (Task 2 GREEN commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in validation logic)
**Impact on plan:** Fix was required to avoid breaking existing API behavior. No scope creep.

## Issues Encountered

- Linter silently reverted `_validate_plot_params` calls in `tsplot`/`tsplot_dual` during Task 2 GREEN phase — noticed because full suite showed one failure; re-read file, confirmed edits had been applied by linter already (the file shown in error was the pre-edit version), ran suite again and all passed

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- DEP-02 and FIX-05 are closed; users get visible feedback when adjustText is absent and receive clear errors for type mistakes
- Remaining Phase 2 plans (if any) can safely depend on the validated public API
- No blockers

---
*Phase: 02-bug-fixes-and-dependencies*
*Completed: 2026-03-15*

## Self-Check: PASSED

- src/pxts/plots.py: FOUND
- tests/test_plots.py: FOUND
- 02-03-SUMMARY.md: FOUND
- Commit ad29049 (test DEP-02 RED): FOUND
- Commit 7c6792e (feat DEP-02 GREEN): FOUND
- Commit 7366258 (test FIX-05 RED): FOUND
- Commit 80e3aa1 (feat FIX-05 GREEN): FOUND
