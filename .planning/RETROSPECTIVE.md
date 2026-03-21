# Retrospective

Living document — updated after each milestone.

---

## Milestone: v0.1 — Hardening

**Shipped:** 2026-03-16
**Phases:** 6 | **Plans:** 14 | **Commits:** ~90
**Timeline:** 2 days (2026-03-15 → 2026-03-16)

### What Was Built

- **Phase 1:** Complete pytest infrastructure — conftest.py fixtures, 5 test modules, 126 passing tests total
- **Phase 2:** 5 silent bug fixes (date warning, tz identity, B/D weekday, freq alias, param validation) + 2 dep declarations
- **Phase 3:** Accurate docstrings across __init__.py, _backend.py, _manual_deconflict; median-diff tick algorithm (later superseded)
- **Phase 4:** Retroactive VERIFICATION.md files for phases 1-3; dead code removal (numpy import, tmp_csv fixture)
- **Phase 5:** Bloomberg BDH integration — read_bdh() with lazy pdblp, optional dep group, TsAccessor delegation, 8 mocked tests
- **Phase 6:** Zoom-responsive Plotly date axis (4-tier tickformatstops); showlegend=True in template; legend overlap avoidance

### What Worked

- **Phase verification loop** — planner → checker → revision caught the showlegend assertion issue (template vs layout) before execution, saving a debug cycle
- **Retroactive verification pattern** (Phase 4) — writing VERIFICATION.md from git evidence was clean and factually grounded; no loss of traceability
- **Optional dep pattern** — `patch.dict(sys.modules)` for lazy-imported modules is the right approach; the Phase 5 executor auto-corrected the naive `@patch("pxts.io.pdblp")` attempt
- **Planning with CONTEXT.md** — discuss-phase locked decisions before planning prevented rework on axis/legend behavior choices
- **tickformatstops approach** — replacing the function entirely (not keeping as fallback) was the right call; clean removal with zero dead references

### What Was Inefficient

- **Phase 3 → Phase 6 supersession** — POL-01 improved `_detect_plotly_tickformat` in Phase 3, then Phase 6 removed it entirely. The Phase 3 work was not wasted (it clarified the algorithm before removing it) but the intermediate state existed only briefly.
- **Retroactive verification (Phase 4)** — VERIFICATION.md files should ideally be created during execute-phase, not retroactively. The process is now in place for future phases.
- **ROADMAP.md plan checkbox inconsistency** — some plans showed `[x]` in progress table but `[ ]` in detail sections; tooling didn't keep them in sync perfectly.

### Patterns Established

- `patch.dict(sys.modules, {'pdblp': mock_pdblp})` for lazy optional dependency mocking
- `fig.layout.template.layout.showlegend` (not `fig.layout.showlegend`) for asserting Plotly template values
- `requirements: []` in plan frontmatter for enhancement phases not tied to formal requirements
- Year annotation at bottom-right using `xref='paper', yref='paper'` for stable placement independent of data range
- `_extend_yaxis_for_legend` skip on dual-axis charts (discretionary, by design)

### Key Lessons

- When a function is superseded, remove it entirely rather than keeping it as a fallback — zero references is cleaner than conditional dispatch
- Docstring-only changes don't need test assertions — they're correctly verified by code inspection
- Bloomberg integration with lazy imports requires `sys.modules` patching, not attribute patching — document this pattern in project conventions
- Retroactive VERIFICATION.md is valid when evidence is in git history — the key is grounding every claim in a commit hash

### Cost Observations

- Model mix: sonnet throughout (researcher disabled, planner/checker/executor all sonnet)
- Sessions: ~4-5 context windows across the milestone
- Notable: yolo mode + auto-advance eliminated most confirmation gates; milestone completed in 2 days

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Tests | Requirements | Duration |
|-----------|--------|-------|-------|--------------|----------|
| v0.1 Hardening | 6 | 14 | 126 | 20/20 | 2 days |

