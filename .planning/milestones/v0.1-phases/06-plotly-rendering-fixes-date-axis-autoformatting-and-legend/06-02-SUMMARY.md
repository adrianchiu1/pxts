---
phase: 06-plotly-rendering-fixes-date-axis-autoformatting-and-legend
plan: 02
subsystem: testing
tags: [plotly, tickformatstops, legend, date-axis, tsplot, pytest]

# Dependency graph
requires:
  - phase: 06-01
    provides: "tickformatstops constant, showlegend template, year annotation, _extend_yaxis_for_legend"
provides:
  - Regression tests for Plotly date axis zoom-responsive formatting (tickformatstops)
  - Regression tests for Plotly legend visibility (showlegend in pxts template)
  - Regression tests for year annotation on auto-formatted Plotly figures
  - Phase 6 behaviors cemented in test suite — future regressions caught immediately
affects: [tests]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Assert showlegend in fig.layout.template.layout (not fig.layout) — Plotly template values live in template, not top-level layout"

key-files:
  created: []
  modified:
    - tests/test_plots.py

key-decisions:
  - "showlegend assertion checks fig.layout.template.layout.showlegend, not fig.layout.showlegend — pxts sets the value in the template, Plotly does not copy it to top-level layout"

patterns-established:
  - "Template-sourced Plotly layout values (showlegend, colorway, etc.) accessed via fig.layout.template.layout.* in tests"

requirements-completed: [PLOTLY-01, PLOTLY-02]

# Metrics
duration: 5min
completed: 2026-03-16
---

# Phase 06 Plan 02: Plotly Phase 6 Regression Tests Summary

**8 new regression tests cement Phase 6 Plotly behaviors: zoom-responsive tickformatstops, template-driven showlegend, year annotation, and dual-axis coverage**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-16T08:30:00Z
- **Completed:** 2026-03-16T08:35:00Z
- **Tasks:** 1
- **Files modified:** 1 (tests/test_plots.py)

## Accomplishments
- `TestTsplotPlotlyPhase6Fixes` class added with 6 test methods covering: tickformatstops default, tickformat override, showlegend in template, year annotation present, year annotation absent with override, 4-tier count
- 2 new methods added to `TestTsplotDualPlotly`: `test_showlegend_true_in_layout` and `test_tickformatstops_set_when_no_date_format`
- Test count grew from 48 to 56 (all passing)
- Auto-fixed showlegend assertions to target `fig.layout.template.layout.showlegend` (correct location for template-sourced values)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Plotly date axis and legend tests to test_plots.py** - `1519ca0` (feat)

## Files Created/Modified
- `tests/test_plots.py` - Added `TestTsplotPlotlyPhase6Fixes` (6 tests) and 2 new methods in `TestTsplotDualPlotly`

## Decisions Made
- `showlegend` assertion checks `fig.layout.template.layout.showlegend` rather than `fig.layout.showlegend` — Plotly only stores template-derived values inside the template object, not at the figure layout's top level; asserting `fig.layout.showlegend` would always return `None` even when the template correctly sets `True`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed showlegend assertions to check template layout, not top-level layout**
- **Found during:** Task 1 (verification — 2 test failures)
- **Issue:** Plan's test spec asserted `fig.layout.showlegend is True` but `showlegend=True` is set inside the pxts Plotly template (`go.layout.Template`); `fig.layout.showlegend` always returns `None` regardless of the template value
- **Fix:** Updated both `test_showlegend_true_in_layout` assertions to check `fig.layout.template.layout.showlegend`
- **Files modified:** `tests/test_plots.py`
- **Verification:** Both tests now pass; assertion correctly validates template-configured value
- **Committed in:** `1519ca0` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in test assertion targeting wrong layout level)
**Impact on plan:** Fix essential for correctness — tests now verify the actual mechanism by which showlegend is applied. No scope creep.

## Issues Encountered
- Plotly template layout properties are not reflected in `fig.layout.*` at the top level; they remain inside `fig.layout.template.layout.*`. This is standard Plotly behavior but not obvious from the API surface.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All Phase 6 Plotly behaviors are now regression-tested
- 56 tests pass, zero failures
- No blockers for subsequent work

---
*Phase: 06-plotly-rendering-fixes-date-axis-autoformatting-and-legend*
*Completed: 2026-03-16*
