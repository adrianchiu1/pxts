---
phase: quick
plan: 2
subsystem: io
tags: [date-format, british, ambiguous, user-warning]
dependency_graph:
  requires: []
  provides: [british-date-default]
  affects: [src/pxts/io.py, tests/test_io.py]
tech_stack:
  added: []
  patterns: [British-first ambiguous date fallback]
key_files:
  modified:
    - src/pxts/io.py
    - tests/test_io.py
decisions:
  - "British (DD/MM/YYYY) is now the default for ambiguous slash-delimited dates; US users must pass date_format='%m/%d/%Y' explicitly"
metrics:
  duration: "2 min"
  completed: "2026-03-16"
  tasks_completed: 2
  files_modified: 2
---

# Quick Task 2: Change Date Default to DD/MM/YYYY (British) Summary

**One-liner:** Changed ambiguous slash-date fallback from US MM/DD/YYYY to British DD/MM/YYYY, updating warning message and two test assertions.

## What Was Done

`_detect_date_format` previously defaulted ambiguous dates (where both the first and second parts are <= 12) to US format MM/DD/YYYY. This task flipped the default to British DD/MM/YYYY, updated the UserWarning to reference "British" and hint `%m/%d/%Y` as the US override, and updated the two tests that were asserting the old US behavior.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | Switch ambiguous date default to British | 1f29991 | src/pxts/io.py |
| 2 | Update tests to assert British default | 74e97ea | tests/test_io.py |

## Changes Made

### src/pxts/io.py

- Docstring comment: `ambiguous (both <= 12) -> default to British ("%d/%m/%Y", True)`
- Warning message: `"assumed DD/MM/YYYY (British). Pass date_format='%m/%d/%Y' to override."`
- Return value: `return ("%d/%m/%Y", True)` (was `("%m/%d/%Y", False)`)

### tests/test_io.py

- `test_ambiguous_defaults_to_us` renamed to `test_ambiguous_defaults_to_british`; assertion updated to `("%d/%m/%Y", True)`
- `test_ambiguous_slash_csv_treated_as_us` renamed to `test_ambiguous_slash_csv_treated_as_british`; Timestamp assertion updated to `pd.Timestamp("2024-02-01")`

## Verification

- `_detect_date_format("01/02/2024")` returns `("%d/%m/%Y", True)` with UserWarning mentioning "British"
- Full test suite: **89 passed** in 4.42s

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- src/pxts/io.py: FOUND
- tests/test_io.py: FOUND
- Commit 1f29991: FOUND
- Commit 74e97ea: FOUND
