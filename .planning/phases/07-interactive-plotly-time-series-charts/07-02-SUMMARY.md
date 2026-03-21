---
phase: 07-interactive-plotly-time-series-charts
plan: 02
subsystem: ui
tags: [plotly, range-selector, rangeslider, dark-mode, dual-axis, axis-labels]

# Dependency graph
requires:
  - phase: 07-01
    provides: "DARK_*_COLOR constants in theme.py; tightened Plotly template margins"
provides:
  - "tsplot() accepts rangeslider, theme, annotations params; Plotly renderer has 6 range selector buttons and rangeslider"
  - "tsplot_dual() accepts rangeslider, theme, annotations, left_label, right_label params; Plotly renderer has range nav and colored axis titles"
  - "Dark theme applied to both Plotly renderers via theme='dark'"
affects:
  - "07-03-PLAN.md (annotations processing builds on signature established here)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Range selector buttons configured as xaxis_cfg dict extension before fig.update_layout"
    - "rangeslider dict(visible=bool) applied via xaxis_cfg in tsplot and via update_xaxes in tsplot_dual"
    - "Dark theme applied after fig.update_layout via conditional import from pxts.theme"
    - "Colored axis title text via fig.update_yaxes(title_text=..., title_font=dict(color=...))"

key-files:
  created:
    - tests/_verify_07_02.py
    - tests/_verify_07_02_dual.py
  modified:
    - src/pxts/plots.py

key-decisions:
  - "rangeslider=True default: interactive Plotly charts should show slider by default; opt-out via rangeslider=False"
  - "annotations param accepted as no-op in Plan 02 signatures; Plan 03 adds processing logic"
  - "Dark theme applied after fig.update_layout to avoid template overwriting dark color settings"
  - "left_label/right_label use title_font=dict(color=...) on update_yaxes, consistent with existing tickfont pattern"

patterns-established:
  - "Range nav pattern: xaxis_cfg dict extended with rangeselector + rangeslider before layout update in _plot_ts_plotly; update_xaxes call in _plot_ts_dual_plotly"
  - "Theme routing pattern: theme param forwarded explicitly from public API through to renderer; dark constants imported lazily inside conditional block"

requirements-completed:
  - PLT7-01
  - PLT7-02
  - PLT7-07

# Metrics
duration: 8min
completed: 2026-03-17
---

# Phase 7 Plan 02: Range Navigation, Axis Labels, and Dark Theme for Plotly Renderers Summary

**Range selector buttons (1M/3M/6M/YTD/1Y/All) and rangeslider added to tsplot and tsplot_dual Plotly renders, with colored axis labels via left_label/right_label and dark theme via theme="dark"**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-16T17:29:52Z
- **Completed:** 2026-03-16T17:37:00Z
- **Tasks:** 2
- **Files modified:** 1 (src/pxts/plots.py); 2 verify scripts created

## Accomplishments
- Added `rangeslider`, `theme`, `annotations` params to `tsplot()` and forwarded to `_plot_ts_plotly()`
- Added `rangeslider`, `theme`, `annotations`, `left_label`, `right_label` params to `tsplot_dual()` and forwarded to `_plot_ts_dual_plotly()`
- Both Plotly renderers now display 6 range selector buttons (1M, 3M, 6M, YTD, 1Y, All) by default
- `rangeslider=False` hides the slider on both renderers
- `theme="dark"` applies navy background, dark plot area, dark grid, and light font on both renderers
- `left_label`/`right_label` set colored axis title text (LEFT_COLOR/RIGHT_COLOR) on dual-axis charts
- Matplotlib backend receives new params without error and returns unchanged matplotlib.figure.Figure
- 126 tests pass (no regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1: Range nav and dark theme in _plot_ts_plotly, updated tsplot signature** - `5af6662` (feat)
2. **Task 2: Range nav, axis labels, dark theme in _plot_ts_dual_plotly, updated tsplot_dual signature** - `0c8f725` (feat)

**Plan metadata:** (pending — created in final commit)

## Files Created/Modified
- `src/pxts/plots.py` - Updated tsplot/tsplot_dual signatures; updated _plot_ts_plotly and _plot_ts_dual_plotly with range nav, dark theme, and axis label support
- `tests/_verify_07_02.py` - Verification script for tsplot range selector, rangeslider, dark theme, matplotlib compat
- `tests/_verify_07_02_dual.py` - Verification script for tsplot_dual range selector, rangeslider, left_label/right_label, dark theme, matplotlib compat

## Decisions Made
- `rangeslider=True` default: interactive charts show rangeslider by default; opt-out preserves backward compat
- `annotations` param accepted as no-op here; Plan 03 adds actual processing
- Dark theme applied after `fig.update_layout` to prevent the pxts template from overwriting custom colors
- `left_label`/`right_label` use `title_font=dict(color=...)` on `update_yaxes`, matching the existing `tickfont` pattern already in `_plot_ts_dual_plotly`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- System-installed pxts (miniconda) shadows local source during direct `python -c "exec(...)"` invocation. Resolved with `sys.path.insert(0, 'src')` in verification command. pytest runs correctly via editable install.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Range navigation and axis labels are live for both Plotly renderers
- Dark theme constants from Plan 01 successfully wired through to both renderers
- `annotations` param is in the public signature, ready for Plan 03 to add processing logic
- No blockers

---
*Phase: 07-interactive-plotly-time-series-charts*
*Completed: 2026-03-17*
