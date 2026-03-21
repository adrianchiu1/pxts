---
phase: 07-interactive-plotly-time-series-charts
plan: 01
subsystem: ui
tags: [plotly, theme, dark-mode, margins]

# Dependency graph
requires: []
provides:
  - "Tightened Plotly template margins (l=60 r=40 t=50 b=50) eliminating excessive whitespace"
  - "Dark-theme color constants (DARK_BACKGROUND_COLOR, DARK_PLOT_COLOR, DARK_GRID_COLOR, DARK_FONT_COLOR) exported from theme.py"
  - "autosize=True in pxts Plotly template for responsive chart sizing"
affects:
  - "07-02-PLAN.md (tsplot dark theme — imports dark constants from theme.py)"
  - "07-03-PLAN.md (tsplot_dual dark theme — imports dark constants from theme.py)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dark theme colors defined centrally in theme.py and imported by plot renderers"
    - "Plotly template margins set at template registration time in _apply_plotly_theme"

key-files:
  created: []
  modified:
    - src/pxts/theme.py

key-decisions:
  - "margin=dict(l=60, r=40, t=50, b=50): l=60 accommodates y-axis tick labels, r=40 minimal right padding, t=50 accommodates title, b=50 accommodates x-axis labels"
  - "autosize=True added alongside margins to ensure fully responsive chart sizing"
  - "Dark theme constants defined in theme.py (not plots.py) so plot renderers import a single source of truth"

patterns-established:
  - "Dark-theme constants pattern: DARK_*_COLOR naming convention in theme.py, consumed by plots.py"

requirements-completed:
  - PLT7-03
  - PLT7-04

# Metrics
duration: 4min
completed: 2026-03-17
---

# Phase 7 Plan 01: Plotly Template Margins and Dark-Theme Constants Summary

**Plotly template margin tightened to (l=60 r=40 t=50 b=50) with autosize=True, and four DARK_*_COLOR constants exported from theme.py for use by Plans 02/03**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-16T17:24:39Z
- **Completed:** 2026-03-16T17:28:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added `DARK_BACKGROUND_COLOR`, `DARK_PLOT_COLOR`, `DARK_GRID_COLOR`, `DARK_FONT_COLOR` constants to theme.py
- Set `margin=dict(l=60, r=40, t=50, b=50)` in the pxts Plotly template to eliminate excessive whitespace
- Set `autosize=True` for responsive chart sizing
- 126 tests pass (no regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1: Tighten Plotly template margins and add dark-theme constants** - `d50e47d` (feat)

**Plan metadata:** (pending — created in final commit)

## Files Created/Modified
- `src/pxts/theme.py` - Added dark-theme color constants after GRID_ALPHA; added margin and autosize to go.Layout in _apply_plotly_theme

## Decisions Made
- `margin=dict(l=60, r=40, t=50, b=50)`: l=60 gives room for y-axis tick labels, r=40 is minimal right padding, t=50 accommodates a title, b=50 accommodates x-axis labels (matching plan rationale exactly)
- `autosize=True` ensures the chart is fully responsive — no fixed width/height
- Dark theme constants defined in theme.py (not in plots.py) so Plans 02/03 can import them from a single source of truth

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- The system-installed pxts package in miniconda shadowed the local source during initial verification; resolved by prepending `src/` to `sys.path` in the verification command. Tests run correctly via pytest (which uses the installed editable package).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Dark-theme constants are ready for Plans 02 and 03 to import
- Plotly template margin fix is live for all chart renders
- No blockers

---
*Phase: 07-interactive-plotly-time-series-charts*
*Completed: 2026-03-17*
