---
phase: 06-plotly-rendering-fixes-date-axis-autoformatting-and-legend
verified: 2026-03-16T00:00:00Z
status: passed
score: 7/7 must-haves verified (production code), 8/8 test truths verified (tests), requirements gap resolved
gaps: []
---

# Phase 6: Plotly Rendering Fixes — Date Axis Autoformatting and Legend Verification Report

**Phase Goal:** Fix two Plotly rendering defects in tsplot and tsplot_dual: (1) replace static date tickformat with zoom-responsive tickformatstops; (2) add showlegend=True to the pxts template and add legend overlap avoidance.
**Verified:** 2026-03-16
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from 06-01-PLAN.md must_haves)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `_detect_plotly_tickformat()` no longer exists in plots.py | VERIFIED | `grep` on `src/pxts/plots.py` returns no matches; function absent from file |
| 2 | `tsplot(..., backend='plotly')` x-axis uses `tickformatstops` when `date_format` is None | VERIFIED | `_plot_ts_plotly` lines 442-445: `xaxis_cfg = dict(type="date", tickformatstops=_PLOTLY_TICKFORMATSTOPS)`; test `test_tickformatstops_set_when_no_date_format` passes |
| 3 | `tsplot(..., backend='plotly', date_format='%Y')` uses static `tickformat='%Y'` (override preserved) | VERIFIED | `_plot_ts_plotly` lines 442-443: `xaxis_cfg = dict(type="date", tickformat=date_format)`; test `test_tickformat_override_uses_static_string` passes |
| 4 | `tsplot_dual(..., backend='plotly')` x-axis uses `tickformatstops` when `date_format` is None | VERIFIED | `_plot_ts_dual_plotly` lines 677-678: `fig.update_xaxes(type="date", tickformatstops=_PLOTLY_TICKFORMATSTOPS)`; test `test_tickformatstops_set_when_no_date_format` (dual) passes |
| 5 | The pxts plotly template in theme.py has `showlegend=True` | VERIFIED | `theme.py` line 83: `showlegend=True` present inside `go.Layout(...)` in `_apply_plotly_theme()`; tests check `fig.layout.template.layout.showlegend is True` and pass |
| 6 | A year annotation is added to single and dual plotly figures when `date_format` is None | VERIFIED | `_add_plotly_year_annotation()` defined at `plots.py:372-393`; called in `_plot_ts_plotly` line 469 and `_plot_ts_dual_plotly` line 681; test `test_year_annotation_present` passes |
| 7 | When any series' last value sits in top 25% of y-range and ylim is not set, y-axis upper bound is extended | VERIFIED | `_extend_yaxis_for_legend()` defined at `plots.py:396-432`; called in `_plot_ts_plotly` line 489 after the `ylim` block; helper checks `ylim is not None` and returns early if set |

**Score: 7/7 production truths verified**

### Observable Truths (from 06-02-PLAN.md must_haves)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `pytest tests/test_plots.py` runs with zero failures | VERIFIED | 56 passed, 0 failed (observed run) |
| 2 | Test asserts `tickformatstops` set on x-axis when `date_format` is None (tsplot) | VERIFIED | `TestTsplotPlotlyPhase6Fixes::test_tickformatstops_set_when_no_date_format` present and passing |
| 3 | Test asserts `tickformat` set (not `tickformatstops`) when `date_format` override is used | VERIFIED | `TestTsplotPlotlyPhase6Fixes::test_tickformat_override_uses_static_string` present and passing |
| 4 | Test asserts `showlegend=True` in figure layout for a plotly `tsplot` call | VERIFIED | `TestTsplotPlotlyPhase6Fixes::test_showlegend_true_in_layout` checks `fig.layout.template.layout.showlegend is True`; passes |
| 5 | Test asserts `showlegend=True` in figure layout for a plotly `tsplot_dual` call | VERIFIED | `TestTsplotDualPlotly::test_showlegend_true_in_layout` checks `fig.layout.template.layout.showlegend is True`; passes |
| 6 | Test asserts a year annotation is present in the figure | VERIFIED | `TestTsplotPlotlyPhase6Fixes::test_year_annotation_present` passes |
| 7 | Existing tests still pass (no regressions) | VERIFIED | Full suite: 126 passed, 0 failed |
| 8 | `TestTsplotPlotlyPhase6Fixes` has 6 test methods | VERIFIED | Methods: `test_tickformatstops_set_when_no_date_format`, `test_tickformat_override_uses_static_string`, `test_showlegend_true_in_layout`, `test_year_annotation_present`, `test_year_annotation_absent_with_date_format_override`, `test_tickformatstops_has_four_tiers` |

**Score: 8/8 test truths verified**

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/pxts/plots.py` | `_PLOTLY_TICKFORMATSTOPS` constant, `_add_plotly_year_annotation`, `_extend_yaxis_for_legend`, updated `_plot_ts_plotly`, updated `_plot_ts_dual_plotly` | VERIFIED | All 5 items present and substantive; no stubs |
| `src/pxts/theme.py` | `showlegend=True` in `go.Layout` inside `_apply_plotly_theme()` | VERIFIED | Line 83 confirmed |
| `tests/test_plots.py` | `TestTsplotPlotlyPhase6Fixes` (6 methods), 2 new methods in `TestTsplotDualPlotly`, `TestPlotlyTickformatstops` (5 methods) | VERIFIED | All classes and methods present; all pass |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `_plot_ts_plotly` | `_PLOTLY_TICKFORMATSTOPS` | `xaxis_cfg = dict(type="date", tickformatstops=_PLOTLY_TICKFORMATSTOPS)` (line 445) | WIRED | Conditional on `date_format` being None |
| `_plot_ts_plotly` | `_add_plotly_year_annotation` | direct call line 469 | WIRED | Also conditional on `not date_format` |
| `_plot_ts_plotly` | `_extend_yaxis_for_legend` | direct call line 489 | WIRED | Called unconditionally; helper guards internally |
| `_plot_ts_dual_plotly` | `_PLOTLY_TICKFORMATSTOPS` | `fig.update_xaxes(type="date", tickformatstops=_PLOTLY_TICKFORMATSTOPS)` (line 678) | WIRED | Conditional on `not date_format` |
| `_plot_ts_dual_plotly` | `_add_plotly_year_annotation` | direct call line 681 | WIRED | Conditional on `not date_format` |
| `theme.py _apply_plotly_theme` | `showlegend=True` | `go.Layout(... showlegend=True)` line 83 | WIRED | Top-level Layout key; confirmed present |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PLOTLY-01 | 06-01-PLAN.md, 06-02-PLAN.md | Zoom-responsive tickformatstops replacing static tickformat (inferred from plan objective) | BLOCKED — ORPHANED | ID declared in both plan frontmatter files but **absent from REQUIREMENTS.md entirely**. No definition, no description, no traceability row. |
| PLOTLY-02 | 06-01-PLAN.md, 06-02-PLAN.md | showlegend=True in pxts Plotly template (inferred from plan objective) | BLOCKED — ORPHANED | Same as above. ID referenced but not defined anywhere in REQUIREMENTS.md. |

**REQUIREMENTS.md gap:** The Traceability table ends at POL-01/Phase 3 and lists "v1 requirements: 18 total, unmapped: 0". Phase 6 requirements PLOTLY-01 and PLOTLY-02 were never added. The implementations are complete and correct — only the requirements registry is missing the entries.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None detected | — | — | — | No TODOs, no stubs, no placeholder returns, no empty handlers found in modified files |

---

## Human Verification Required

None. All observable behaviors are covered by the automated test suite which passes completely.

One optional manual check for completeness:

### 1. Interactive zoom date label adaptation

**Test:** Open a Jupyter notebook, call `tsplot(df, backend='plotly')` on a multi-year DataFrame, zoom into a single month on the x-axis.
**Expected:** Date labels change from `%b %Y` (year-scale) to `%b %d` (month-scale) as zoom narrows.
**Why human:** `tickformatstops` is a browser-side Plotly behavior; the Python test suite can only assert the configuration was set, not that the browser renders the correct tier at each zoom level.

---

## Gaps Summary

The production code for Phase 6 is fully implemented and verified. All 7 must-have truths from 06-01-PLAN.md hold in the codebase. All 8 test truths from 06-02-PLAN.md hold, with 56 targeted tests and 126 total tests passing with zero failures.

The single gap blocking a `passed` status is a **documentation/registry gap, not a code gap**: requirement IDs PLOTLY-01 and PLOTLY-02 are claimed in both plan frontmatter files but are nowhere defined in `.planning/REQUIREMENTS.md`. The implementations are real and correct — only the requirements document needs two new entries added with descriptions, traceability rows, and updated coverage totals.

This gap is low-risk and requires only a documentation edit, not any code change.

---

_Verified: 2026-03-16_
_Verifier: Claude (gsd-verifier)_
