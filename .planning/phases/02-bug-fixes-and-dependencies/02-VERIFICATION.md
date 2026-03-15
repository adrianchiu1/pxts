---
phase: 02-bug-fixes-and-dependencies
verified: 2026-03-15T00:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
gaps: []
human_verification: []
---

# Phase 2: Bug Fixes and Dependencies — Verification Report

**Phase Goal:** Declare all missing runtime dependencies and eliminate five categories of silent bugs identified in Phase 1 tests.
**Verified:** 2026-03-15
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | `cycler` is listed in `pyproject.toml` dependencies so a fresh install cannot import-fail on theme application | VERIFIED | `dependencies = ["pandas>=2.0", "cycler"]` in `[project]` stanza — confirmed in the file directly |
| 2  | Importing pxts without `adjustText` installed prints a clear message explaining the fallback, and only once per session | VERIFIED | `_ADJUSTTEXT_WARNED: bool = False` at module level in `plots.py` line 31; `global _ADJUSTTEXT_WARNED` + `warnings.warn(...)` in `_add_mpl_end_labels` except block; flag set to `True` after first emit |
| 3  | Loading an ambiguous slash-delimited CSV emits a `UserWarning` naming the assumed format | VERIFIED | `warnings.warn(f"pxts: ambiguous date '{sample}' — assumed MM/DD/YYYY (US). Pass date_format='%d/%m/%Y' to override.", UserWarning, stacklevel=3)` in `io.py` ambiguous branch |
| 4  | Calling `set_tz` with a semantically equivalent timezone does not trigger a spurious conversion or warning | VERIFIED | `_tz_equal()` helper in `core.py` compares UTC offsets at two reference points (winter + summer); `elif _tz_equal(index.tz, tz): return df` no-op path confirmed |
| 5  | Calling `infer_freq` on daily data distinguishes B-vs-D by checking for weekend timestamps | VERIFIED | `if min_diff == pd.Timedelta(days=1): has_weekend = any(ts.weekday() >= 5 for ts in df.index); return "D" if has_weekend else "B"` in `core.py` |
| 6  | `to_dense(df, freq='1D')` on a `'D'`-frequency index is a recognized no-op | VERIFIED | `norm_freq = to_offset(freq).freqstr; if df.index.freqstr == norm_freq: return df` in `core.py` — normalizes both sides before comparing |
| 7  | `tsplot` and `tsplot_dual` validate hlines, vlines, title, subtitle, date_format parameter types with clear error messages | VERIFIED | `_validate_plot_params()` helper in `plots.py`; called immediately after `validate_ts(df)` in both `tsplot` (line 554) and `tsplot_dual` (line 596) |

**Score:** 7/7 truths verified

---

### Required Artifacts

| Artifact | Plan | Status | Details |
|----------|------|--------|---------|
| `pyproject.toml` | 02-01 | VERIFIED | `[project].dependencies` contains `"cycler"` alongside `"pandas>=2.0"`. Optional deps section unchanged. |
| `src/pxts/io.py` | 02-01 | VERIFIED | `import warnings` present; `warnings.warn(...)` with `UserWarning, stacklevel=3` in the ambiguous slash-date `else` branch. Non-ambiguous paths (first>12, second>12, ISO) do not warn. |
| `src/pxts/core.py` — `_tz_equal` helper | 02-02 | VERIFIED | Module-level function using dual-reference-point UTC offset comparison (more robust than single-timestamp approach in plan — handles DST zones correctly). |
| `src/pxts/core.py` — `set_tz` | 02-02 | VERIFIED | Uses `_tz_equal(index.tz, tz)` in the `elif` branch. Naive and different-tz paths unchanged. |
| `src/pxts/core.py` — `infer_freq` | 02-02 | VERIFIED | B-vs-D branch fires only when `min_diff == pd.Timedelta(days=1)`. Other frequencies fall through to existing `to_offset` path unchanged. |
| `src/pxts/core.py` — `to_dense` | 02-02 | VERIFIED | `try: norm_freq = to_offset(freq).freqstr; if df.index.freqstr == norm_freq: return df` with `except Exception: pass` fallback. |
| `src/pxts/plots.py` — `_ADJUSTTEXT_WARNED` flag | 02-03 | VERIFIED | `_ADJUSTTEXT_WARNED: bool = False` declared at module level after constants section (line 31). |
| `src/pxts/plots.py` — `_add_mpl_end_labels` | 02-03 | VERIFIED | `except ImportError: global _ADJUSTTEXT_WARNED; if not _ADJUSTTEXT_WARNED: warnings.warn(...); _ADJUSTTEXT_WARNED = True; _manual_deconflict(texts)` |
| `src/pxts/plots.py` — `_validate_plot_params` | 02-03 | VERIFIED | Helper validates hlines/vlines (list, dict, None), title/subtitle/date_format (str, None). Raises `ValueError` with caller name and type name in message. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `_detect_date_format` | user call site | `stacklevel=3` in `warnings.warn` | WIRED | Stack: user → `read_ts` → `_detect_date_format`; stacklevel=3 correctly points warning at user's `read_ts()` call |
| `_add_mpl_end_labels` | user call site | `stacklevel=2` in `warnings.warn` | WIRED | Stack: user → `tsplot` → `_add_mpl_end_labels`; stacklevel=2 points at `tsplot` call |
| `_ADJUSTTEXT_WARNED` | `_add_mpl_end_labels` | `global _ADJUSTTEXT_WARNED` mutation | WIRED | `global` declaration inside except block confirmed; flag persists across calls in same session |
| `_validate_plot_params` | `tsplot` | called after `validate_ts(df)` at line 554 | WIRED | Order: `validate_ts` → `_validate_plot_params` → `_validate_cols` → backend dispatch |
| `_validate_plot_params` | `tsplot_dual` | called after `validate_ts(df)` at line 596 | WIRED | Same order as `tsplot` |
| `_tz_equal` | `set_tz` | `elif _tz_equal(index.tz, tz)` | WIRED | Replaces the former string-equality check; returns `df` unchanged on match |
| `to_offset` | `to_dense` no-op guard | `to_offset(freq).freqstr` | WIRED | `to_offset` already imported from `pandas.tseries.frequencies`; used correctly in the guard |
| B-vs-D branch | `infer_freq` early return | `return "D" if has_weekend else "B"` before `to_offset` call | WIRED | Early return prevents falling through to `to_offset(min_diff)` for 1-day diffs |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DEP-01 | 02-01 | `cycler` declared as explicit runtime dependency in `pyproject.toml` | SATISFIED | `dependencies = ["pandas>=2.0", "cycler"]` confirmed in `[project]` stanza |
| DEP-02 | 02-03 | `adjustText` documented as optional install with clear user-facing message when absent | SATISFIED | Once-per-session `UserWarning` with install hint; `_ADJUSTTEXT_WARNED` flag prevents repetition |
| FIX-01 | 02-01 | `_detect_date_format` emits `UserWarning` when slash-delimited date is ambiguous | SATISFIED | Warning present with sample date, assumed format, and `date_format=` override hint |
| FIX-02 | 02-02 | `set_tz` uses proper timezone identity comparison to avoid spurious conversions | SATISFIED | `_tz_equal()` using dual-reference-point UTC offset comparison; `Etc/UTC` and `UTC` correctly identified as equivalent |
| FIX-03 | 02-02 | `infer_freq` emits `UserWarning` when 1-day timedelta detected (B-vs-D ambiguity) | SATISFIED (adapted) | Per plan 02-02 spec, smart detection replaced the warning: `has_weekend` check returns `'B'` or `'D'` directly. No warning emitted — behavior is deterministic, not ambiguous. This is the documented decision in the plan. |
| FIX-04 | 02-02 | `to_dense` normalizes `freq` alias before no-op comparison so `'1D'` and `'D'` are equivalent | SATISFIED | `norm_freq = to_offset(freq).freqstr` used before string comparison |
| FIX-05 | 02-02/02-03 | `tsplot` and `tsplot_dual` validate parameter types with clear error messages | SATISFIED | `_validate_plot_params()` validates all five parameters; `ValueError` message includes caller name and actual type |

**Orphaned requirements:** None. All 7 phase-2 requirement IDs (DEP-01, DEP-02, FIX-01, FIX-02, FIX-03, FIX-04, FIX-05) are claimed by plans and verified in the codebase.

**Note on FIX-03 vs ROADMAP Success Criterion 5:** The ROADMAP states "Calling `infer_freq` on daily data emits a `UserWarning` noting the B-vs-D ambiguity." The implementation instead uses smart detection (weekend check) to resolve the ambiguity deterministically — returning `'B'` for weekday-only data and `'D'` for data including weekends — with no warning. This is a deliberate design decision documented in plan 02-02 ("No UserWarning emitted by infer_freq (per user decision: smart detection replaces warning)"). The outcome is superior to the originally stated criterion: the ambiguity is resolved rather than surfaced. This is flagged for awareness but does not constitute a gap.

---

### Anti-Patterns Found

Scanned `pyproject.toml`, `src/pxts/io.py`, `src/pxts/core.py`, `src/pxts/plots.py` and all test files.

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| None found | — | — | — |

No TODO/FIXME/placeholder comments, empty implementations, or stub returns found in any modified file.

---

### Human Verification Required

None. All behaviors verified programmatically:

- `_detect_date_format` warning verified by test `test_ambiguous_defaults_to_us` (uses `pytest.warns`)
- `set_tz` no-op for `Etc/UTC` verified by `test_set_tz_etc_utc_is_noop` (raises on any warning)
- `infer_freq` B-vs-D verified by `test_infer_freq_daily_weekdays_returns_B` and `test_infer_freq_daily_with_weekends_returns_D`
- `to_dense` `'1D'` alias verified by `test_to_dense_1D_alias_is_noop`
- `_ADJUSTTEXT_WARNED` once-per-session behavior verified by `test_adjusttext_warning_emitted_once` (patches `sys.modules`, resets flag)
- All 89 tests pass: `pytest -x -q` → `89 passed in 8.50s`

---

### Test Suite Results

```
89 passed in 8.50s
```

All tests pass including new tests added in this phase:
- `test_ambiguous_defaults_to_us` — FIX-01 warning
- `test_unambiguous_uk_no_warning`, `test_unambiguous_us_no_warning`, `test_iso_no_warning` — FIX-01 non-ambiguous paths
- `test_explicit_date_format_suppresses_warning` — FIX-01 explicit format bypass
- `test_set_tz_etc_utc_is_noop` — FIX-02 semantic equivalence
- `test_infer_freq_daily_weekdays_returns_B`, `test_infer_freq_daily_with_weekends_returns_D` — FIX-03
- `test_to_dense_1D_alias_is_noop`, `test_to_dense_different_freq_is_not_noop` — FIX-04
- `TestAdjustTextWarning.test_adjusttext_warning_emitted_once` — DEP-02
- `TestParameterTypeValidation` (8 tests) — FIX-05

---

_Verified: 2026-03-15_
_Verifier: Claude (gsd-verifier)_
