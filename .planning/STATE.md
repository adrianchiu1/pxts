---
gsd_state_version: 1.0
milestone: v0.1
milestone_name: milestone
status: unknown
last_updated: "2026-03-16T04:47:30.253Z"
progress:
  total_phases: 3
  completed_phases: 1
  total_plans: 7
  completed_plans: 6
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-15)

**Core value:** A researcher can `from pxts import *` and confidently load, manipulate, and visualize financial time series — with no hidden bugs and no surprises.
**Current focus:** Phase 3 — Documentation and Polish

## Current Position

Phase: 3 of 3 (Documentation and Polish)
Plan: 0 of ? in current phase
Status: Phase 3 not started
Last activity: 2026-03-16 - Completed quick task 4: add ylim/xlim/ylim_lhs/ylim_rhs axis limit parameters to tsplot and tsplot_dual

Progress: [█░░░░░░░░░] ~10%

## Performance Metrics

**Velocity:**
- Total plans completed: 1
- Average duration: 2 min
- Total execution time: 2 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-test-suite | 1 | 2 min | 2 min |

**Recent Trend:**
- Last 5 plans: 01-01 (2 min)
- Trend: -

*Updated after each plan completion*
| Phase 01-test-suite P02 | 2 | 1 tasks | 1 files |
| Phase 01-test-suite P03 | 3 | 1 tasks | 1 files |
| Phase 01-test-suite P05 | 1 | 1 tasks | 2 files |
| Phase 03-documentation-and-polish P01 | 2 | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: Warn on ambiguous date format rather than error — backward-compatible, silent corruption is worse
- [Init]: Unit tests per module — fast feedback, isolated failures, clear ownership
- [Init]: CSV-only for v0.1, Parquet deferred to v0.2
- [01-01]: Session scope for ts_df and bad_df — read-only fixtures safe to share across session, avoid redundant construction
- [01-01]: No pxts imports in conftest.py — prevents side-effects during fixture collection
- [Phase 01-test-suite]: Inline helper functions for test-local DataFrames rather than fixtures — tz-aware and sparse DataFrames needed only in test_core.py
- [Phase 01-test-suite]: validate_ts gate tested once per function to confirm pxtsValidationError propagation without duplicating error assertions
- [Phase 01-test-suite]: Assert current ambiguous date behavior (silent US default) without pytest.warns — TODO(Phase-2) marks update point for FIX-01 (resolved: quick-2 switched to British default)
- [quick-2]: British (DD/MM/YYYY) is now the default for ambiguous slash-delimited dates — US users must pass date_format='%m/%d/%Y' explicitly
- [Phase 01-test-suite]: Import pxts.accessor at module level — idempotent registration, safe as module-level side effect
- [Phase 01-test-suite]: Import from pxts.theme directly (not import pxts) in test_theme.py to avoid apply_theme() triggering before restore_rcparams fixture
- [01-04]: Use explicit backend= parameter in plot tests — bypasses get_backend() entirely, no patching needed, simpler and more reliable
- [01-04]: matplotlib.use("Agg") at module level in test_plots.py — required for headless CI environments
- [Phase 02-bug-fixes-and-dependencies]: UTC offset comparison at two reference points (winter+summer) for _tz_equal — handles pytz/zoneinfo/datetime.timezone heterogeneity correctly
- [Phase 02-bug-fixes-and-dependencies]: stacklevel=3 in warnings.warn: call chain user->read_ts->_detect_date_format, points warning at user call site
- [Phase 02-bug-fixes-and-dependencies]: hlines/vlines accept list, dict, or None in _validate_plot_params — dicts used for labeled reference lines, must not be rejected
- [Phase 02-bug-fixes-and-dependencies]: Use warnings.catch_warnings(record=True) for no-warning assertions: pytest.warns(None) removed in pytest 7+
- [Phase 02-bug-fixes-and-dependencies]: stacklevel=2 in warnings.warn points UserWarning at tsplot/tsplot_dual call site (user-visible location)
- [Phase 02-bug-fixes-and-dependencies]: _ADJUSTTEXT_WARNED mutated via global declaration inside _add_mpl_end_labels — module-level persistence across calls
- [quick-4]: Reject bare int/float for xlim — pd.Timestamp accepts them as nanoseconds but they are not meaningful date-like user inputs; require str, pd.Timestamp, or datetime objects
- [Phase 03-01]: Parquet removed from read_ts/write_ts descriptions to match CSV-only v0.1 reality
- [Phase 03-01]: apply_theme() import side-effect documented in __init__.py module docstring with order-of-import note
- [Phase 03-01]: IS_JUPYTER cached-at-import behavior documented in _backend.py with reload scenario and manual override workaround

### Pending Todos

None yet.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | clear all phase 2 bug fix records | 2026-03-16 | d854a75 | [1-clear-all-phase-2-bug-fix-records](./quick/1-clear-all-phase-2-bug-fix-records/) |
| 2 | change date default to DD/MM/YYYY (British) | 2026-03-16 | 74e97ea | [2-change-date-default-to-dd-mm-yyyy-britis](./quick/2-change-date-default-to-dd-mm-yyyy-britis/) |
| 3 | allow float or int for hlines/vlines in tsplot | 2026-03-16 | 3582058 | [3-allow-float-or-int-for-hlines-vlines-in-](./quick/3-allow-float-or-int-for-hlines-vlines-in-/) |
| 4 | add ylim/xlim/ylim_lhs/ylim_rhs to tsplot and tsplot_dual | 2026-03-16 | 29311dd | [4-add-ylim-xlim-to-tsplot-and-ylim-lhs-yli](./quick/4-add-ylim-xlim-to-tsplot-and-ylim-lhs-yli/) |

### Blockers/Concerns

- Phase 1 test infrastructure in place; remaining test modules (01-02 through 01-05) needed before Phase 2 bug fixes can be verified
- `adjustText` is undeclared and graceful fallback is silent — must be addressed in Phase 2

## Session Continuity

Last session: 2026-03-16
Stopped at: Quick task 4 complete — ylim/xlim/ylim_lhs/ylim_rhs axis limit parameters added to tsplot and tsplot_dual
Resume file: None
