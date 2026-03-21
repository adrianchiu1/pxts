---
phase: 08-simplify-plotting-api-remove-subtitle-rangeslider-theme-date-format-and-annotation-arguments-from-matplotlib-and-plotly-charts
plan: "01"
subsystem: plots
tags: [matplotlib, plotly, api-simplification, plots.py]

# Dependency graph
requires:
  - phase: 07-interactive-plotly-time-series-charts
    provides: rangeslider, theme, annotations, subtitle params added in phase 7
provides:
  - Simplified tsplot/tsplot_dual public API without subtitle, annotations, rangeslider, theme
  - add_annotation() and _apply_plotly_annotations() fully removed from codebase
  - Matplotlib renderers always use ConciseDateFormatter (no date_format passthrough)
  - Plotly rangeslider hardcoded to visible=False
affects:
  - 08-02 (test updates to remove calls using removed params)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Hardcoded visible=False for rangeslider in both Plotly renderers
    - ConciseDateFormatter always applied in matplotlib (no conditional branch)

key-files:
  created: []
  modified:
    - src/pxts/plots.py
    - src/pxts/__init__.py

key-decisions:
  - "rangeslider always hidden in Plotly (hardcoded visible=False) — cleaner default, no parameter needed"
  - "date_format kept in tsplot/tsplot_dual public API and Plotly renderers; removed only from matplotlib renderers"
  - "rangeselector (1M/3M/6M/YTD/1Y/All buttons) preserved unchanged"

patterns-established:
  - "Removed params: subtitle, annotations, rangeslider, theme from public API and all backend renderers"

requirements-completed: []

# Metrics
duration: 6min
completed: 2026-03-17
---

# Phase 8 Plan 01: Remove subtitle, rangeslider, theme, and annotations from plots.py and __init__.py Summary

**Simplified tsplot/tsplot_dual API by removing subtitle, annotations, rangeslider, and theme params; deleted add_annotation() and _apply_plotly_annotations() entirely; matplotlib renderers now always use ConciseDateFormatter**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-17T02:28:26Z
- **Completed:** 2026-03-17T02:34:05Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Removed subtitle, annotations, rangeslider, and theme from `tsplot` and `tsplot_dual` public signatures
- Removed subtitle and date_format from `_plot_ts_mpl` and `_plot_ts_dual_mpl`; ConciseDateFormatter is now always used
- Removed subtitle, annotations, rangeslider, and theme from `_plot_ts_plotly` and `_plot_ts_dual_plotly`; rangeslider hardcoded to visible=False
- Removed subtitle, date_format, and annotations from `_validate_plot_params` signature and body
- Deleted `_apply_plotly_annotations()` helper and `add_annotation()` public function from plots.py
- Removed `add_annotation` from `__init__.py` import, `__all__`, and module docstring

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove subtitle, rangeslider, theme, annotations from plots.py** - `a61bbce` (feat)
2. **Task 2: Remove add_annotation from __init__.py** - `0529e2f` (feat)

## Files Created/Modified
- `src/pxts/plots.py` - Removed 5 parameter groups from 7 function signatures, deleted 2 functions (214 net lines removed)
- `src/pxts/__init__.py` - Removed add_annotation import, __all__ entry, and docstring mention

## Decisions Made
- rangeslider hardcoded to `visible=False` in both `_plot_ts_plotly` and `_plot_ts_dual_plotly` — cleaner default, no parameter needed
- date_format param kept in `tsplot`/`tsplot_dual` public API and both Plotly renderer signatures — removed only from matplotlib renderers which don't use it
- rangeselector (1M/3M/6M/YTD/1Y/All navigation buttons) preserved unchanged in both Plotly renderers

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Stale miniconda system-installed `pxts` package shadowed local source during verification. Resolved by running `pip install -e .` to switch to editable install (same pattern noted in Phase 7 decisions). The editable install failed on the first attempt because `__init__.py` still imported `add_annotation` before Task 2 was complete — completed Task 2 first, then re-verified both tasks together successfully.

## Next Phase Readiness
- Plan 08-01 complete: public API and internal helpers are cleaned up
- Plan 08-02 needed: update test suite to remove calls using removed params (tests currently pass subtitle/annotations/etc. that no longer exist)

---
*Phase: 08-simplify-plotting-api*
*Completed: 2026-03-17*
