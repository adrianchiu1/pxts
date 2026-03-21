# Milestones

## v0.1 Hardening (Shipped: 2026-03-16)

**Phases:** 6 | **Plans:** 14 | **Requirements:** 20/20 | **Tests:** 126 passing
**Timeline:** 2026-03-15 → 2026-03-16 (2 days)
**Git range:** Initial commit → docs(v0.1): complete milestone audit
**LOC:** 2,849 Python across src/ and tests/

**Key accomplishments:**
- Complete pytest suite with 126 tests across 6 modules (test_core, test_io, test_plots, test_accessor, test_theme, test_bdh)
- 5 silent bugs fixed: ambiguous date warning, tz identity comparison, B/D weekday detection, freq alias normalization, parameter type validation
- Declared `cycler` as runtime dep; `adjustText` as optional with graceful UserWarning
- Accurate docstrings for CSV-only I/O, IS_JUPYTER caching, apply_theme() side-effect, _manual_deconflict approximation
- Zoom-responsive Plotly date axis: 4-tier tickformatstops replaces static _detect_plotly_tickformat; showlegend=True in template
- Bloomberg BDH integration: read_bdh() with optional pdblp, TsAccessor delegation, full mock-based test coverage

**Archive:** `.planning/milestones/v0.1-ROADMAP.md`, `.planning/milestones/v0.1-REQUIREMENTS.md`

---

