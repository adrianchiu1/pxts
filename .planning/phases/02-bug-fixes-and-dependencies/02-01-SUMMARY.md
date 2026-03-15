---
phase: 02-bug-fixes-and-dependencies
plan: 01
subsystem: io
tags: [pandas, warnings, toml, cycler, date-format]

# Dependency graph
requires:
  - phase: 01-test-suite
    provides: test_io.py with full coverage of read_ts, write_ts, _detect_date_format
provides:
  - cycler declared as explicit runtime dependency in pyproject.toml
  - _detect_date_format emits UserWarning for ambiguous slash dates (both parts <=12)
  - Warning message names the ambiguous date, assumed format, and override hint
affects:
  - 02-bug-fixes-and-dependencies
  - any phase touching io.py or package dependencies

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "warnings.warn with stacklevel=3 to surface warnings at user call site (not internal helper)"
    - "warnings.catch_warnings(record=True) + simplefilter for no-warning assertions in pytest 9.x"

key-files:
  created: []
  modified:
    - pyproject.toml
    - src/pxts/io.py
    - tests/test_io.py

key-decisions:
  - "stacklevel=3 in warnings.warn: call chain is user -> read_ts -> _detect_date_format, so 3 puts warning at user call site"
  - "Use warnings.catch_warnings(record=True) instead of pytest.warns(None): pytest.warns(None) was removed in pytest 7+, catch_warnings is stdlib and stable"
  - "Warning message includes sample date, assumed format (MM/DD/YYYY), and override hint (date_format=): gives user enough context to self-correct"

patterns-established:
  - "TDD RED/GREEN for config file changes: verification command serves as test; current state is RED, edit is GREEN"
  - "No-warning assertions: use warnings.catch_warnings(record=True) with simplefilter('always') in pytest 9.x"

requirements-completed: [DEP-01, FIX-01]

# Metrics
duration: 5min
completed: 2026-03-15
---

# Phase 2 Plan 1: Cycler Dependency and Ambiguous Date Warning Summary

**cycler added as explicit runtime dep and _detect_date_format now emits UserWarning with sample date, assumed US format, and override hint for ambiguous slash dates**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-15T06:55:48Z
- **Completed:** 2026-03-15T07:01:29Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- pyproject.toml [project].dependencies now lists both "pandas>=2.0" and "cycler" — prevents import errors when matplotlib not installed in base path
- _detect_date_format warns users when a slash date is ambiguous (both parts <= 12), naming the assumed format and the override parameter
- 5 new tests added to test_io.py (4 unit, 1 integration) covering warning emission, no-warning paths, and warning suppression via explicit date_format

## Task Commits

Each task was committed atomically:

1. **Task 1: Add cycler to runtime dependencies (DEP-01)** - `f72eaf0` (chore)
2. **Task 2 RED: Add failing tests for ambiguous date warning** - `2a5b58d` (test)
3. **Task 2 GREEN: Implement warning in _detect_date_format** - `ab1d93d` (feat)

_Note: TDD tasks have separate test (RED) and implementation (GREEN) commits_

## Files Created/Modified

- `pyproject.toml` - Added "cycler" to [project].dependencies alongside pandas>=2.0
- `src/pxts/io.py` - Added `import warnings`; replaced silent ambiguous else-branch with warnings.warn(UserWarning, stacklevel=3)
- `tests/test_io.py` - Updated test_ambiguous_defaults_to_us and test_ambiguous_slash_csv_treated_as_us to assert UserWarning; added 4 new tests for no-warning paths and explicit format suppression

## Decisions Made

- **stacklevel=3**: Call chain is user code -> read_ts -> _detect_date_format, so stacklevel=3 correctly points the warning at the user's read_ts() call site rather than the internal helper.
- **warnings.catch_warnings(record=True) instead of pytest.warns(None)**: pytest.warns(None) was removed in pytest 7+. The stdlib `warnings.catch_warnings` approach is stable and version-agnostic.
- **Warning message format**: Includes the raw sample string, the assumed format name (MM/DD/YYYY), and the exact override parameter (`date_format='%d/%m/%Y'`). This gives users full self-correction context without reading docs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Replaced pytest.warns(None) with warnings.catch_warnings for no-warning assertions**
- **Found during:** Task 2 (GREEN phase — running tests after implementing warning)
- **Issue:** Plan specified `pytest.warns(None)` pattern for no-warning assertions, but pytest 9.x removed support for `pytest.warns(None)` — raises TypeError at collection time
- **Fix:** Replaced all `with pytest.warns(None) as record:` blocks with `with warnings.catch_warnings(record=True) as record: warnings.simplefilter("always")` — stdlib approach, stable across pytest versions
- **Files modified:** tests/test_io.py
- **Verification:** All 21 test_io.py tests pass; full suite 89 tests pass
- **Committed in:** ab1d93d (Task 2 GREEN commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in test pattern)
**Impact on plan:** Fix was necessary for test correctness on pytest 9.x. No scope creep.

## Issues Encountered

None beyond the pytest.warns(None) incompatibility documented above.

## Next Phase Readiness

- DEP-01 and FIX-01 requirements are complete
- test_io.py now has 21 tests covering all io.py paths including warning paths
- Remaining Phase 2 plans (02-02 through 02-05) can proceed independently
- Full suite at 89 tests, all passing

---
*Phase: 02-bug-fixes-and-dependencies*
*Completed: 2026-03-15*
