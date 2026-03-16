---
status: complete
phase: 02-bug-fixes-and-dependencies
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md]
started: 2026-03-15T08:00:00Z
updated: 2026-03-16T08:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. cycler declared as runtime dependency
expected: pyproject.toml [project].dependencies lists "cycler" explicitly alongside "pandas>=2.0"
result: pass

### 2. Ambiguous date format warning
expected: |
  When reading a CSV where the date column has ambiguous slash dates (e.g., "01/02/2024" where
  both day and month parts are ≤12), read_ts() emits a UserWarning that includes the sample
  date, the assumed format (MM/DD/YYYY), and the override hint (date_format='%d/%m/%Y').
  The warning points at the read_ts() call in user code (not an internal helper).
result: pass

### 3. Explicit date_format suppresses the warning
expected: |
  When calling read_ts() with an explicit date_format= parameter on the same ambiguous CSV,
  no UserWarning is emitted — the explicit format bypasses detection entirely.
result: pass

### 4. set_tz no-op for semantically equivalent timezones
expected: |
  Calling set_tz(df, 'Etc/UTC') on a DataFrame already indexed in UTC returns the DataFrame
  unchanged — no spurious conversion or timezone mutation. Previously this was not treated as
  a no-op because 'UTC' != 'Etc/UTC' as strings.
result: pass

### 5. infer_freq returns 'B' for weekday-only daily data
expected: |
  A time series with daily data containing only weekday timestamps (Mon–Fri) gets infer_freq()
  returning 'B' (business day). Previously it incorrectly returned 'D' for all daily data.
result: pass

### 6. infer_freq returns 'D' for daily data with weekend timestamps
expected: |
  A time series with daily data that includes Saturday or Sunday timestamps gets infer_freq()
  returning 'D' (calendar day), not 'B'.
result: pass

### 7. to_dense treats '1D' and 'D' as equivalent
expected: |
  Calling to_dense(df, freq='1D') on a DataFrame that already has daily ('D') frequency
  is a no-op — returns the same DataFrame without duplicating or re-indexing. Previously
  the alias mismatch ('1D' != 'D') caused it to re-apply asfreq unnecessarily.
result: pass

### 8. adjustText missing warning fires once per session
expected: |
  When adjustText is not installed and tsplot() or tsplot_dual() is called with labels=True,
  a UserWarning is emitted on the first call. Subsequent calls in the same Python session
  do NOT re-emit the warning (_ADJUSTTEXT_WARNED flag prevents repeat).
result: issue
reported: "I got 2"
severity: major

### 9. Wrong parameter type raises ValueError at call site
expected: |
  Calling tsplot(df, hlines=42.0) (wrong type — float instead of list/dict/None) raises a
  ValueError with a clear message at the tsplot() call site, not a cryptic error deep inside
  a helper. Same applies to vlines, title, subtitle, date_format with wrong types.
result: pass

## Summary

total: 9
passed: 8
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "adjustText missing UserWarning fires exactly once per session when labels=True and adjustText is absent"
  status: failed
  reason: "User reported: I got 2"
  severity: major
  test: 8
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
