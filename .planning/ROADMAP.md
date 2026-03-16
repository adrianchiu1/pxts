# Roadmap: pxts

## Milestones

- ✅ **v0.1 Hardening** — Phases 1-6 (shipped 2026-03-16)

## Phases

<details>
<summary>✅ v0.1 Hardening (Phases 1-6) — SHIPPED 2026-03-16</summary>

- [x] Phase 1: Test Suite (5/5 plans) — completed 2026-03-15
- [x] Phase 2: Bug Fixes and Dependencies (retroactive) — completed 2026-03-15
- [x] Phase 3: Documentation and Polish (2/2 plans) — completed 2026-03-16
- [x] Phase 4: Process Closure and Cleanup (3/3 plans) — completed 2026-03-16
- [x] Phase 5: Bloomberg BDH Integration (2/2 plans) — completed 2026-03-16
- [x] Phase 6: Plotly Rendering Fixes — date axis and legend (2/2 plans) — completed 2026-03-16

See full archive: `.planning/milestones/v0.1-ROADMAP.md`

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Test Suite | v0.1 | 5/5 | Complete | 2026-03-15 |
| 2. Bug Fixes and Dependencies | v0.1 | — | Complete | 2026-03-15 |
| 3. Documentation and Polish | v0.1 | 2/2 | Complete | 2026-03-16 |
| 4. Process Closure and Cleanup | v0.1 | 3/3 | Complete | 2026-03-16 |
| 5. Bloomberg BDH Integration | v0.1 | 2/2 | Complete | 2026-03-16 |
| 6. Plotly Rendering Fixes | v0.1 | 2/2 | Complete | 2026-03-16 |
| 7. Interactive Plotly Time Series Charts | 2/4 | In Progress|  | — |


### Phase 7: Interactive Plotly Time Series Charts

**Goal:** Upgrade the Plotly backend of tsplot and tsplot_dual with range navigation (1M/3M/6M/YTD/1Y/All buttons + rangeslider), data point annotations (annotations= parameter + add_annotation() helper), colored dual-axis labels, and tighter visual margins with dark/light theme support.
**Requirements**: PLT7-01, PLT7-02, PLT7-03, PLT7-04, PLT7-05, PLT7-06, PLT7-07
**Depends on:** Phase 6
**Plans:** 2/4 plans executed

Plans:
- [ ] 07-01-PLAN.md — Tighten Plotly template margins and add dark-theme color constants to theme.py (wave 1)
- [ ] 07-02-PLAN.md — Range nav (buttons + rangeslider), dual-axis labels, and theme wiring in plots.py (wave 2, depends on 07-01)
- [ ] 07-03-PLAN.md — Annotation processing helper, add_annotation() public function, __init__.py export (wave 3, depends on 07-02)
- [ ] 07-04-PLAN.md — Phase 7 regression tests for all new Plotly features (wave 4, depends on 07-01/02/03)
