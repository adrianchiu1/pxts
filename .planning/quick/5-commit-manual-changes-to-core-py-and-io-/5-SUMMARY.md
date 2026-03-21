---
phase: quick-5
plan: 1
subsystem: core,io,tests
tags: [bugfix, test-alignment, bloomberg, validate_ts, read_bdh]
dependency_graph:
  requires: []
  provides: [validate_ts with MultiIndex/uniqueness guards, read_bdh with ticker coercion and timeout]
  affects: [src/pxts/core.py, src/pxts/io.py, tests/test_bdh.py]
tech_stack:
  added: []
  patterns: [lazy pdblp import, validate_ts gate in read_bdh]
key_files:
  modified:
    - src/pxts/core.py
    - src/pxts/io.py
    - tests/test_bdh.py
decisions:
  - "match=r'pip install pdblp' used as ImportError test substring — stable against URL changes in the full message"
metrics:
  duration: "~3 min"
  completed: "2026-03-16"
---

# Quick Task 5: Commit Manual Changes to core.py and io.py Summary

**One-liner:** Aligned test_importerror_without_pdblp match regex to new ImportError message and committed all manual core.py/io.py changes in a single verified commit with 117 tests passing.

## What Was Done

Fixed the single broken test caused by the updated ImportError message in io.py, then committed all manual changes to core.py, io.py, and tests/test_bdh.py as one atomic commit.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Fix broken test assertion for updated ImportError message | 7df78c8 | tests/test_bdh.py |
| 2 | Verify full test suite and commit all changes | 7df78c8 | src/pxts/core.py, src/pxts/io.py, tests/test_bdh.py |

## Commits

- `7df78c8` — fix(core,io): validate_ts uniqueness/MultiIndex checks; read_bdh ticker coercion and timeout

## Verification

- `python -m pytest tests/ -q` → **117 passed** (0 failures, 0 errors)
- `git show --stat HEAD` → confirms all 3 files in commit, no untracked planning/cache files included

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- `src/pxts/core.py` — present in commit `7df78c8`
- `src/pxts/io.py` — present in commit `7df78c8`
- `tests/test_bdh.py` — present in commit `7df78c8`
- 117 tests pass confirmed
