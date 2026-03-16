---
phase: 03-documentation-and-polish
plan: 02
subsystem: plotting
tags: [plotly, matplotlib, tick-format, docstring, numpy, pandas]

# Dependency graph
requires:
  - phase: 01-test-suite
    provides: test infrastructure for plots module
  - phase: 02-bug-fixes-and-dependencies
    provides: validated _manual_deconflict and _detect_plotly_tickformat functions
provides:
  - Corrected _manual_deconflict docstring clarifying data-unit spacing approximation
  - Updated _detect_plotly_tickformat using median consecutive-diff algorithm
  - 4 new regression tests for _detect_plotly_tickformat covering daily/monthly/annual/single-row
affects: [future plotly tick format consumers, end-label deconfliction callers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Use numpy median of consecutive diffs (not total span) for time-series interval detection"
    - "Single-row edge case guard before computing diffs"

key-files:
  created: []
  modified:
    - src/pxts/plots.py
    - tests/test_plots.py

key-decisions:
  - "Median-diff thresholds adjusted to >180 days for '%Y' and >25 days for '%b %Y' — plan's code snippet used >3*365 for '%Y' but that threshold doesn't work with median approach where annual data has ~365 day median; behavior spec is canonical"
  - "min_spacing_pt parameter name left unchanged (breaking change risk); docstring updated to document the misnomer"

patterns-established:
  - "Behavior spec in PLAN.md takes precedence over code snippets when they conflict"

requirements-completed: [DOC-04, POL-01]

# Metrics
duration: 3min
completed: 2026-03-16
---

# Phase 3 Plan 02: Documentation and Polish — Docstring and Tick Algorithm Fix Summary

**Fixed misleading _manual_deconflict docstring (data units vs. display points) and replaced span-based _detect_plotly_tickformat with numpy median-diff algorithm for correct sparse-dataset tick granularity**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-16T04:44:45Z
- **Completed:** 2026-03-16T04:47:18Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `_manual_deconflict` docstring now correctly states `min_spacing_pt` is in data units (not display points), is an approximation, and directs users to adjustText for accurate deconfliction
- `_detect_plotly_tickformat` now uses `numpy median of consecutive index diffs` so sparse datasets with clustered timestamps pick the right granularity (e.g. dense daily data spanning 5 years now returns `%b %d` not `%Y`)
- 4 new TDD tests cover daily, monthly, annual, and single-row edge cases — all passing; full 109-test suite passes with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix _manual_deconflict docstring** - `050424f` (docs)
2. **Task 2 RED: Add failing tests for _detect_plotly_tickformat** - `d0a324a` (test)
3. **Task 2 GREEN: Replace _detect_plotly_tickformat with median-diff algorithm** - `c76aa85` (feat)

## Files Created/Modified
- `src/pxts/plots.py` - Updated _manual_deconflict docstring; replaced _detect_plotly_tickformat implementation
- `tests/test_plots.py` - Added TestDetectPlotlyTickformat class with 4 tests

## Decisions Made
- **Threshold adjustment**: The plan's code snippet specified `median_days > 3 * 365` for `%Y`, but the behavior spec requires annual data (~365 day median) to return `%Y`. These are contradictory. The behavior spec (`<behavior>`) is canonical — thresholds were set to `> 180` for `%Y` and `> 25` for `%b %Y`, which satisfies all 4 behavior scenarios.
- **Parameter name preserved**: `min_spacing_pt` not renamed — would be a breaking API change; docstring update is sufficient per plan spec.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected thresholds in _detect_plotly_tickformat**
- **Found during:** Task 2 GREEN (implementation)
- **Issue:** Plan's code snippet used `median_days > 3 * 365` for `%Y` threshold, but with the median approach annual data (365-day median) is NOT > 1095 days. Plan's behavior spec says annual data → `%Y`. The code snippet and behavior spec are contradictory.
- **Fix:** Set thresholds to `> 180` for `%Y` and `> 25` for `%b %Y`, satisfying all behavior scenarios
- **Files modified:** src/pxts/plots.py
- **Verification:** All 4 tickformat tests pass; algorithm verification PASS
- **Committed in:** c76aa85 (Task 2 GREEN commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in plan's code snippet threshold)
**Impact on plan:** Auto-fix was necessary for correctness — behavior spec is the authoritative source and all behavior scenarios now pass.

## Issues Encountered
None beyond the threshold deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both DOC-04 and POL-01 requirements are complete
- No regressions introduced; full 109-test suite passes
- Ready for remaining phase 3 plans

---
*Phase: 03-documentation-and-polish*
*Completed: 2026-03-16*
