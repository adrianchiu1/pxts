---
phase: 08-simplify-plotting-api-remove-subtitle-rangeslider-theme-date-format-and-annotation-arguments-from-matplotlib-and-plotly-charts
verified: 2026-03-17T02:42:19Z
status: passed
score: 8/8 must-haves verified
---

# Phase 8: Simplify Plotting API — Verification Report

**Phase Goal:** Remove subtitle, rangeslider, theme, date_format (from mpl), and annotations/add_annotation from matplotlib and Plotly charts. All references to these arguments must be gone from the codebase. Code must be substantially simpler. All remaining tests must pass.
**Verified:** 2026-03-17T02:42:19Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `subtitle` param absent from all function signatures and call sites | VERIFIED | No match for `subtitle=` or `subtitle` as parameter in `plots.py`, `__init__.py`, or `test_plots.py` (method names like `test_title_and_subtitle` contain the word as a name only; no kwarg usage found) |
| 2 | `rangeslider` param absent from public API and internal signatures | VERIFIED | No `rangeslider=` kwarg in `tsplot`/`tsplot_dual` or any renderer signature; single remaining ref is `rangeslider=dict(visible=False)` at line 682 (hardcoded, correct) |
| 3 | `theme` param absent from all functions | VERIFIED | No `theme=` in any function signature or call site in `plots.py` or tests |
| 4 | `annotations` param absent from all functions | VERIFIED | No `annotations=` anywhere in `plots.py` or tests |
| 5 | `add_annotation()` and `_apply_plotly_annotations()` fully deleted | VERIFIED | Neither function definition nor call appears in `plots.py`; `__init__.py` does not import or export `add_annotation` |
| 6 | `date_format` removed from matplotlib renderers only; retained for Plotly | VERIFIED | `_plot_ts_mpl` (line 308) and `_plot_ts_dual_mpl` (line 534) signatures contain no `date_format`; Plotly renderers at lines 417, 609 still accept it; public API at lines 711, 759 still accept it |
| 7 | `ConciseDateFormatter` always applied in matplotlib (no conditional branch) | VERIFIED | `_plot_ts_mpl` line 324: unconditional `formatter = mdates.ConciseDateFormatter(locator)`; `_plot_ts_dual_mpl` line 568: `mdates.ConciseDateFormatter(locator)` unconditional |
| 8 | All tests pass with simplified API | VERIFIED | `python -m pytest tests/test_plots.py -x -q` reports **64 passed** |

**Score:** 8/8 truths verified

---

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `src/pxts/plots.py` | VERIFIED | 813 lines; all removed params absent from signatures; `add_annotation` and `_apply_plotly_annotations` deleted; `rangeslider` hardcoded `visible=False` in both Plotly renderers (lines 443, 682) |
| `src/pxts/__init__.py` | VERIFIED | Imports only `tsplot, tsplot_dual` from `plots`; `add_annotation` absent from import line 49, `__all__` list, and module docstring |
| `tests/test_plots.py` | VERIFIED | 560 lines; `TestPhase7Theme` deleted; `TestPhase7Annotations` deleted; 4 rangeslider tests deleted from `TestPhase7RangeNav`; `TestPlotlyTemplate` introduced; 3 `test_title_and_subtitle` methods rewritten without `subtitle=`; 2 validation tests for subtitle/date_format removed from `TestParameterTypeValidation` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tsplot` public API | `_plot_ts_mpl` | no `subtitle`, no `date_format` in call | VERIFIED | Line 750: `_plot_ts_mpl(df, cols, title, labels, hlines, vlines, ylim=ylim, xlim=xlim, **kwargs)` |
| `tsplot` public API | `_plot_ts_plotly` | `date_format` passed, no subtitle/annotations/rangeslider/theme | VERIFIED | Line 753: `_plot_ts_plotly(df, cols, title, labels, hlines, vlines, date_format, ylim=ylim, xlim=xlim, **kwargs)` |
| `tsplot_dual` public API | `_plot_ts_dual_mpl` | no `subtitle`, no `date_format` in call | VERIFIED | Line 803: `_plot_ts_dual_mpl(df, left, right, title, labels, hlines, vlines, ylim_lhs=..., ylim_rhs=..., xlim=..., **kwargs)` |
| `tsplot_dual` public API | `_plot_ts_dual_plotly` | `date_format` passed, no removed params | VERIFIED | Line 808: `_plot_ts_dual_plotly(df, left, right, title, labels, hlines, vlines, date_format, ylim_lhs=..., ylim_rhs=..., xlim=..., left_label=..., right_label=..., **kwargs)` |
| `_validate_plot_params` | call sites | no `subtitle`, `date_format`, `annotations` args | VERIFIED | Lines 740, 794: calls pass only `hlines, vlines, title, caller=..., ylim/xlim/ylim_lhs/ylim_rhs` |

---

### Requirements Coverage

No requirement IDs declared for this phase. The phase goal is fully achieved as verified above.

---

### Anti-Patterns Found

| File | Pattern | Severity | Notes |
|------|---------|----------|-------|
| `tests/test_plots.py` line 149 | String "subtitle may exist" in a comment inside a docstring | Info | Leftover wording in `test_year_annotation_absent_with_date_format_override` docstring — does not affect behavior; no `subtitle=` kwarg is passed |

No blockers. The comment at line 149 is inert documentation text, not a code reference.

---

### Human Verification Required

None. All phase goals are verifiable programmatically.

---

### Summary

Phase 8 achieved its goal completely:

- All five removed argument groups (`subtitle`, `rangeslider`, `theme`, `annotations`, `date_format` from mpl) are absent from every function signature, call site, docstring param list, and test kwarg in the codebase.
- `add_annotation()` and `_apply_plotly_annotations()` are fully deleted from `plots.py`.
- `__init__.py` has no trace of `add_annotation` in import, `__all__`, or module docstring.
- Both matplotlib renderers now unconditionally apply `ConciseDateFormatter` with no conditional branch.
- Both Plotly renderers hardcode `rangeslider=dict(visible=False)` while preserving the `rangeselector` nav buttons.
- `date_format` continues to work in `tsplot`/`tsplot_dual` public API and Plotly renderers.
- 64 tests pass; the deleted test classes (`TestPhase7Theme`, `TestPhase7Annotations`) and methods are gone; `TestPlotlyTemplate` preserves the margin regression test.

---

_Verified: 2026-03-17T02:42:19Z_
_Verifier: Claude (gsd-verifier)_
