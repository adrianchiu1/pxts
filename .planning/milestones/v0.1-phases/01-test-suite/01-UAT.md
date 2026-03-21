---
status: complete
phase: 01-test-suite
source: 01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md, 01-05-SUMMARY.md
started: 2026-03-15T00:00:00Z
updated: 2026-03-15T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. pytest collection — no errors
expected: Run `python -m pytest tests/ --collect-only` — 73 tests collected, 0 errors.
result: pass

### 2. Full test suite passes
expected: Run `python -m pytest tests/ -q` — all 73 tests pass, 0 failures, 0 errors.
result: pass

### 3. test_core.py — 20 tests pass
expected: Run `python -m pytest tests/test_core.py -v` — exactly 20 tests pass covering validate_ts, set_tz, to_dense, and infer_freq.
result: pass

### 4. test_io.py — 17 tests pass
expected: Run `python -m pytest tests/test_io.py -v` — exactly 17 tests pass covering _detect_date_format, read_ts, and write_ts (including round-trip and ambiguous date path).
result: pass

### 5. test_plots.py — 18 tests pass
expected: Run `python -m pytest tests/test_plots.py -v` — exactly 18 tests pass covering tsplot and tsplot_dual for both matplotlib (Agg) and plotly backends.
result: pass

### 6. test_accessor.py — 10 tests pass
expected: Run `python -m pytest tests/test_accessor.py -v` — exactly 10 tests pass covering TsAccessor delegation of all 6 methods and the AttributeError protocol.
result: pass

### 7. test_theme.py — 8 tests pass
expected: Run `python -m pytest tests/test_theme.py -v` — exactly 8 tests pass covering plotly template registration, matplotlib rcParams mutation, idempotency, and isolation via restore_rcparams.
result: pass

## Summary

total: 7
passed: 7
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
