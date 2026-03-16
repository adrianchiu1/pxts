---
phase: 05-bloomberg-bdh-historical-data-integration
plan: "02"
subsystem: testing
tags: [bloomberg, pdblp, bdh, unit-tests, mock, sys-modules]

# Dependency graph
requires:
  - phase: 05-bloomberg-bdh-historical-data-integration
    plan: "01"
    provides: read_bdh() implementation with lazy pdblp import
provides:
  - tests/test_bdh.py with 8 unit tests for read_bdh()
  - Mock pattern for lazy-imported optional dependencies via patch.dict(sys.modules)
affects: [future-bloomberg-phases]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - patch.dict(sys.modules, {'pdblp': mock}) for mocking lazily-imported optional dependencies
    - _make_mock_pdblp() helper for consistent BCon mock setup across tests

key-files:
  created:
    - tests/test_bdh.py
  modified: []

key-decisions:
  - "patch.dict(sys.modules) required instead of patch('pxts.io.pdblp') — pdblp is imported lazily inside read_bdh(), not at module level, so pxts.io has no 'pdblp' attribute to patch"

patterns-established:
  - "Lazy-import mock pattern: patch.dict(sys.modules, {'libname': mock_module}) instead of patch('module.libname') when the library is imported inside the function body"

requirements-completed: []

# Metrics
duration: 2min
completed: 2026-03-16
---

# Phase 5 Plan 02: Bloomberg BDH Unit Tests Summary

**8 unit tests for read_bdh() using patch.dict(sys.modules) to mock lazily-imported pdblp — happy path, multi-ticker, date conversion, end default, field passthrough, finally-block stop, ImportError, and validate_ts compliance**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-16T05:51:31Z
- **Completed:** 2026-03-16T05:53:25Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created tests/test_bdh.py with TestReadBdh class containing 8 tests covering all specified behaviors
- Discovered and applied correct mock pattern for lazy imports: patch.dict(sys.modules) instead of patch('pxts.io.pdblp')
- All 117 tests in full suite pass with zero failures

## Task Commits

Each task was committed atomically:

1. **Task 1: Write tests/test_bdh.py with mocked pdblp** - `f9b7fa5` (test)

## Files Created/Modified

- `tests/test_bdh.py` - 8 unit tests for read_bdh() with _make_bdh_response() and _make_mock_pdblp() helpers

## Decisions Made

- patch.dict(sys.modules, {'pdblp': mock}) is the correct approach for mocking a lazily-imported optional dependency — patch('pxts.io.pdblp') fails because pdblp is never assigned as a module-level attribute of pxts.io

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected mock pattern for lazy import**
- **Found during:** Task 1 (initial test run)
- **Issue:** Plan specified `@patch('pxts.io.pdblp')` but read_bdh() uses `import pdblp` inside the function body, so pxts.io has no 'pdblp' attribute — patch raises AttributeError
- **Fix:** Replaced `@patch('pxts.io.pdblp')` with `patch.dict(sys.modules, {'pdblp': mock_pdblp})` throughout; extracted `_make_mock_pdblp()` helper for clean test structure
- **Files modified:** tests/test_bdh.py
- **Verification:** All 8 tests pass; pytest exits 0
- **Committed in:** f9b7fa5 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug — incorrect mock target for lazy import)
**Impact on plan:** Required fix to make tests work correctly against the actual lazy-import implementation. No scope creep.

## Issues Encountered

None — the lazy-import mock mismatch was caught immediately on first test run and corrected in the same task.

## User Setup Required

None - no external service configuration required. Tests run without Bloomberg terminal.

## Next Phase Readiness

- Full test coverage for read_bdh() in place
- Phase 5 complete: read_bdh() implemented, declared as optional dependency, wired into public API and TsAccessor, and fully tested
- Bloomberg functionality ready for researcher use with `pip install pxts[bloomberg]`

---
*Phase: 05-bloomberg-bdh-historical-data-integration*
*Completed: 2026-03-16*
