---
phase: 06-plotly-rendering-fixes-date-axis-autoformatting-and-legend
plan: 01
subsystem: ui
tags: [plotly, tickformatstops, legend, date-axis, tsplot]

# Dependency graph
requires: []
provides:
  - Plotly date axis uses zoom-responsive tickformatstops (4 tiers) replacing static tickformat detection
  - pxts Plotly template has showlegend=True so legend is visible in all Plotly output
  - Year annotation added at bottom-right for auto-formatted Plotly figures
  - _extend_yaxis_for_legend extends upper y-bound when last series value is in top 25% of y-range
affects: [plots, theme]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Use tickformatstops array instead of static tickformat for Plotly date axes"
    - "Module-level constants for multi-tier Plotly configuration arrays"
    - "Helper functions for figure post-processing (annotations, axis adjustments)"

key-files:
  created: []
  modified:
    - src/pxts/plots.py
    - src/pxts/theme.py
    - tests/test_plots.py

key-decisions:
  - "tickformatstops replaces _detect_plotly_tickformat: zoom-responsive rather than static single-format detection"
  - "4 tiers: %Y (decade+), %b %Y (year-scale), %b %d (month-scale), %d (day/sub-day)"
  - "_extend_yaxis_for_legend not called in _plot_ts_dual_plotly — dual-axis charts have independent left/right y ranges"
  - "Tests for deleted _detect_plotly_tickformat replaced with TestPlotlyTickformatstops covering new constant and integration"
  - "pip install -e . required to load source pxts rather than installed site-packages"

patterns-established:
  - "Module-level _PLOTLY_TICKFORMATSTOPS constant: single source of truth for all zoom-responsive date formatting"
  - "Year annotation via _add_plotly_year_annotation: mirrors ConciseDateFormatter offset label pattern"

requirements-completed: [PLOTLY-01, PLOTLY-02]

# Metrics
duration: 6min
completed: 2026-03-16
---

# Phase 06 Plan 01: Plotly Rendering Fixes Summary

**Plotly date axis replaced with 4-tier zoom-responsive tickformatstops and legend always-visible via showlegend=True in pxts template**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-03-16T08:22:38Z
- **Completed:** 2026-03-16T08:28:50Z
- **Tasks:** 2
- **Files modified:** 3 (plots.py, theme.py, test_plots.py)

## Accomplishments
- `_detect_plotly_tickformat()` deleted; replaced by `_PLOTLY_TICKFORMATSTOPS` module-level constant with 4 zoom tiers
- `showlegend=True` and aligned legend position added to pxts Plotly template in theme.py
- `_add_plotly_year_annotation()` added — appends year label at bottom-right of auto-formatted figures
- `_extend_yaxis_for_legend()` added — extends y-axis upper bound by 15% when last value sits in top 25% of range and ylim is not set
- All 48 tests pass (4 old `_detect_plotly_tickformat` tests replaced by 5 new `TestPlotlyTickformatstops` tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add showlegend=True to pxts Plotly template in theme.py** - `4c99522` (feat)
2. **Task 2: Replace _detect_plotly_tickformat with tickformatstops in plots.py** - `ef94d47` (feat)

## Files Created/Modified
- `src/pxts/theme.py` - Added `showlegend=True` and `xanchor="right", x=1` to `go.Layout` in `_apply_plotly_theme()`
- `src/pxts/plots.py` - Removed `_detect_plotly_tickformat`, added `_PLOTLY_TICKFORMATSTOPS`, `_add_plotly_year_annotation`, `_extend_yaxis_for_legend`; updated `_plot_ts_plotly` and `_plot_ts_dual_plotly`
- `tests/test_plots.py` - Replaced `TestDetectPlotlyTickformat` (4 tests) with `TestPlotlyTickformatstops` (5 tests)

## Decisions Made
- `tickformatstops` replaces `_detect_plotly_tickformat`: enables zoom-responsive date labels (Bloomberg/TradingView behaviour) vs. static format chosen at render time
- 4 tiers selected: %Y for decade+ view, %b %Y for year-scale, %b %d for month-scale, %d for day/sub-day
- `_extend_yaxis_for_legend` not applied to dual-axis charts — dual charts have independent left/right y ranges making overlap detection less meaningful (as noted in plan)
- Deleted function's tests replaced wholesale rather than patched; new tests verify the constant structure and integration behavior

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Installed package in editable mode to pick up source changes**
- **Found during:** Task 1 (verification)
- **Issue:** `pxts` was loading from `C:\Users\adria\miniconda3\lib\site-packages\pxts\theme.py` (stale installed copy) rather than from `src/`; verification always failed against old code
- **Fix:** `pip install -e .` to install package in editable mode; subsequent imports resolved to `src/pxts/`
- **Files modified:** none (environment change only)
- **Verification:** `python -c "import pxts.theme; print(pxts.theme.__file__)"` confirmed source path
- **Committed in:** 4c99522 (Task 1 commit, environment fix is implicit)

**2. [Rule 1 - Bug] Replaced stale test class testing deleted function**
- **Found during:** Task 2 (full test suite run)
- **Issue:** `TestDetectPlotlyTickformat` tried to import `_detect_plotly_tickformat` which was intentionally deleted; 4 tests failed with `ImportError`
- **Fix:** Replaced `TestDetectPlotlyTickformat` with `TestPlotlyTickformatstops` (5 tests) covering `_PLOTLY_TICKFORMATSTOPS` constant and its integration
- **Files modified:** `tests/test_plots.py`
- **Verification:** `pytest tests/test_plots.py` — 48 passed, 0 failed
- **Committed in:** ef94d47 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 environment/blocking, 1 stale test/bug)
**Impact on plan:** Both fixes necessary — one to load source correctly, one to align tests with deleted function. No scope creep.

## Issues Encountered
- Stale site-packages installation masked source changes until `pip install -e .` was run. Resolved cleanly.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plotly rendering now matches Bloomberg/TradingView interactive behaviour: date labels adapt on zoom, legend always visible, year context annotation present
- No blockers for subsequent phases

---
*Phase: 06-plotly-rendering-fixes-date-axis-autoformatting-and-legend*
*Completed: 2026-03-16*
