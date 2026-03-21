---
phase: 05-bloomberg-bdh-historical-data-integration
plan: "01"
subsystem: api
tags: [bloomberg, pdblp, bdh, optional-dependency, io]

# Dependency graph
requires:
  - phase: 01-test-suite
    provides: validated test infrastructure
  - phase: 02-bug-fixes-and-dependencies
    provides: stable core with validate_ts
provides:
  - read_bdh() function in io.py with lazy pdblp import
  - Bloomberg optional dependency group in pyproject.toml
  - TsAccessor.read_bdh() delegation method
  - read_bdh in pxts public API (__all__)
affects: [testing, future-bloomberg-phases]

# Tech tracking
tech-stack:
  added: [pdblp (optional, bloomberg extra)]
  patterns:
    - Lazy optional import pattern (try/except ImportError at call time, not module level)
    - BCon open/fetch/close with try/finally for safe connection cleanup
    - Wide-format reshape via xs(field, axis=1, level=1) from MultiIndex columns

key-files:
  created: []
  modified:
    - src/pxts/io.py
    - src/pxts/__init__.py
    - src/pxts/accessor.py
    - pyproject.toml

key-decisions:
  - "Lazy import of pdblp at call time (not module level) — allows from pxts import read_bdh without pdblp installed"
  - "BCon try/finally pattern ensures con.stop() always called even on fetch failure"
  - "xs(field, axis=1, level=1) reshapes MultiIndex columns to wide format with one column per ticker"

patterns-established:
  - "Lazy optional import pattern: try/import except ImportError with pip install hint"

requirements-completed: []

# Metrics
duration: 2min
completed: 2026-03-16
---

# Phase 5 Plan 01: Bloomberg BDH Historical Data Integration Summary

**read_bdh() added to io.py with lazy pdblp import, BCon connection management, and wide-format DataFrame reshape — accessible via top-level import and .ts accessor with pdblp declared as optional bloomberg extra**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-16T05:27:16Z
- **Completed:** 2026-03-16T05:29:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Implemented read_bdh() in io.py with lazy pdblp import (ImportError with install hint if missing), BCon open/fetch/close with try/finally, wide-format xs reshape, and validate_ts() call
- Declared bloomberg = ["pdblp"] under [project.optional-dependencies] in pyproject.toml
- Wired read_bdh into pxts public API (__init__.py import, __all__, module docstring) and TsAccessor delegation method

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement read_bdh() in io.py and declare bloomberg optional dependency** - `0056bd4` (feat)
2. **Task 2: Wire read_bdh into __init__.py and TsAccessor** - `f41e24a` (feat)

## Files Created/Modified

- `src/pxts/io.py` - Added read_bdh() function; updated module docstring Public API list
- `pyproject.toml` - Added bloomberg = ["pdblp"] optional dependency group
- `src/pxts/__init__.py` - Added read_bdh import, __all__ entry, module docstring entry
- `src/pxts/accessor.py` - Added _read_bdh import and TsAccessor.read_bdh() delegation method

## Decisions Made

- Lazy import of pdblp at call time (not module level) — allows `from pxts import read_bdh` without pdblp installed; ImportError is only raised when read_bdh() is actually called
- BCon try/finally pattern ensures con.stop() is always called even if con.bdh() raises an exception
- xs(field, axis=1, level=1) reshapes the MultiIndex columns returned by pdblp.BCon.bdh() to a wide-format DataFrame with one column per Bloomberg ticker string

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

Bloomberg Terminal with API access and pdblp installed is required at runtime to call read_bdh(). Install with: `pip install pxts[bloomberg]`. No configuration is needed at import time.

## Next Phase Readiness

- read_bdh() is importable and callable from pxts top-level and .ts accessor
- pdblp optional dependency group in place — researchers can install with pip install pxts[bloomberg]
- Tests for read_bdh() (mocking pdblp.BCon) can be written in a subsequent plan

---
*Phase: 05-bloomberg-bdh-historical-data-integration*
*Completed: 2026-03-16*
