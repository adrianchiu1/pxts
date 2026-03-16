---
gsd_state_version: 1.0
milestone: v0.1
milestone_name: milestone
status: unknown
last_updated: "2026-03-16T16:18:37.462Z"
progress:
  total_phases: 6
  completed_phases: 5
  total_plans: 14
  completed_plans: 14
---

---
gsd_state_version: 1.0
milestone: v0.1
milestone_name: milestone
status: unknown
last_updated: "2026-03-16T15:37:11.135Z"
progress:
  total_phases: 6
  completed_phases: 5
  total_plans: 14
  completed_plans: 14
---

---
gsd_state_version: 1.0
milestone: v0.1
milestone_name: milestone
status: in-progress
last_updated: "2026-03-16T08:28:50Z"
progress:
  total_phases: 6
  completed_phases: 5
  total_plans: 13
  completed_plans: 13
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-17)

**Core value:** A researcher can `from pxts import *` and confidently load, manipulate, and visualize financial time series — with no hidden bugs and no surprises.
**Current focus:** Planning next milestone — v0.1 shipped 2026-03-16

## Current Position

Phase: 6 of 6 (Plotly Rendering Fixes — Date Axis Autoformatting and Legend)
Plan: 2 of 2 in current phase
Status: Completed
Last activity: 2026-03-16 - Completed 06-02: Plotly Phase 6 regression tests (56 tests pass)

Progress: [██████████] ~100%

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
| Phase 03-documentation-and-polish P02 | 3 | 2 tasks | 2 files |
| Phase 04-process-closure P03 | 1 | 3 tasks | 2 files |
| Phase 04-process-closure P01 | 5 | 2 tasks | 1 files |
| Phase 04-process-closure P02 | 3 | 3 tasks | 1 files |
| Phase 05-bloomberg-bdh-historical-data-integration P01 | 2 | 2 tasks | 4 files |
| Phase 05-bloomberg-bdh-historical-data-integration P02 | 2 | 1 tasks | 1 files |
| Phase 06-plotly-rendering-fixes P01 | 6 | 2 tasks | 3 files |
| Phase 06-plotly-rendering-fixes PP02 | 5 | 1 tasks | 1 files |

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
- [03-02]: Median-diff thresholds use >180 for '%Y' and >25 for '%b %Y' — plan code snippet used >3*365 but that doesn't work with median approach; behavior spec is canonical
- [03-02]: min_spacing_pt parameter name preserved (breaking change risk); docstring updated to document the data-unit misnomer
- [Phase 04-process-closure]: numpy import removed from _detect_plotly_tickformat body — pd.Series.median() is sufficient; numpy not declared as dependency
- [Phase 04-process-closure]: tmp_csv fixture removed from conftest.py — all IO tests use tmp_path inline, no shared fixture needed
- [Phase 04-process-closure]: Retroactive VERIFICATION.md grounded in git history — all Phase 1 commits present and verifiable
- [Phase 04-process-closure]: Phase 2 VERIFICATION.md written retroactively from git history — all evidence preserved in commits
- [Phase 04-process-closure]: FIX-03 requirement wording already correct in REQUIREMENTS.md — confirmed, no change needed
- [05-01]: Lazy import of pdblp at call time — allows from pxts import read_bdh without pdblp installed; ImportError only raised when read_bdh() is actually called
- [05-01]: BCon try/finally pattern ensures con.stop() is always called even if con.bdh() raises an exception
- [05-01]: xs(field, axis=1, level=1) reshapes MultiIndex columns returned by pdblp.BCon.bdh() to wide-format with one column per Bloomberg ticker
- [Phase 05-bloomberg-bdh-historical-data-integration]: patch.dict(sys.modules) required for lazy-import mocks: patch('pxts.io.pdblp') fails because pdblp is imported inside the function body, not at module level
- [06-01]: tickformatstops replaces _detect_plotly_tickformat — zoom-responsive date labels instead of static format detection
- [06-01]: _extend_yaxis_for_legend not called in _plot_ts_dual_plotly — dual-axis charts have independent left/right y ranges
- [06-01]: Tests for deleted _detect_plotly_tickformat replaced with TestPlotlyTickformatstops covering new constant and integration
- [Phase 06-02]: showlegend assertion checks fig.layout.template.layout.showlegend: pxts sets showlegend in Plotly template, not top-level fig.layout — template values must be accessed via the template object

### Roadmap Evolution

- Phase 5 added: Bloomberg BDH historical data integration
- Phase 6 added: Plotly rendering fixes — date axis autoformatting and legend

### Pending Todos

None yet.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | clear all phase 2 bug fix records | 2026-03-16 | d854a75 | [1-clear-all-phase-2-bug-fix-records](./quick/1-clear-all-phase-2-bug-fix-records/) |
| 2 | change date default to DD/MM/YYYY (British) | 2026-03-16 | 74e97ea | [2-change-date-default-to-dd-mm-yyyy-britis](./quick/2-change-date-default-to-dd-mm-yyyy-britis/) |
| 3 | allow float or int for hlines/vlines in tsplot | 2026-03-16 | 3582058 | [3-allow-float-or-int-for-hlines-vlines-in-](./quick/3-allow-float-or-int-for-hlines-vlines-in-/) |
| 4 | add ylim/xlim/ylim_lhs/ylim_rhs to tsplot and tsplot_dual | 2026-03-16 | 29311dd | [4-add-ylim-xlim-to-tsplot-and-ylim-lhs-yli](./quick/4-add-ylim-xlim-to-tsplot-and-ylim-lhs-yli/) |
| 5 | commit manual changes to core.py and io.py | 2026-03-16 | 7df78c8 | [5-commit-manual-changes-to-core-py-and-io-](./quick/5-commit-manual-changes-to-core-py-and-io-/) |
| 6 | write README.md for pxts package | 2026-03-16 | d3fb2dd | [6-write-readme-md-for-pxts-package](./quick/6-write-readme-md-for-pxts-package/) |

### Blockers/Concerns

- Phase 1 test infrastructure in place; remaining test modules (01-02 through 01-05) needed before Phase 2 bug fixes can be verified
- `adjustText` is undeclared and graceful fallback is silent — must be addressed in Phase 2

## Session Continuity

Last session: 2026-03-16
Stopped at: Completed 06-02 — Plotly Phase 6 regression tests; 56 tests pass
Resume file: None
