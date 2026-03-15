# Requirements: pxts v0.1 Hardening

**Defined:** 2026-03-15
**Core Value:** A researcher can `from pxts import *` and confidently load, manipulate, and visualize financial time series — with no hidden bugs and no surprises.

## v1 Requirements

Requirements for v0.1 release. Each maps to a roadmap phase.

### Testing

- [x] **TEST-01**: `tests/` directory exists with pytest-runnable unit tests
- [ ] **TEST-02**: `test_core.py` covers `validate_ts`, `set_tz`, `to_dense`, `infer_freq` — including edge cases
- [ ] **TEST-03**: `test_io.py` covers `read_ts` and `write_ts` — including ambiguous date format paths
- [ ] **TEST-04**: `test_plots.py` covers `tsplot` and `tsplot_dual` for both backends (mocked)
- [ ] **TEST-05**: `test_accessor.py` covers `.ts` accessor methods delegate correctly
- [ ] **TEST-06**: `test_theme.py` covers `apply_theme` without side-effects on other tests

### Dependencies

- [ ] **DEP-01**: `cycler` declared as explicit runtime dependency in `pyproject.toml`
- [ ] **DEP-02**: `adjustText` documented as optional install with clear user-facing message when absent

### Bug Fixes

- [ ] **FIX-01**: `_detect_date_format` emits `UserWarning` when slash-delimited date is ambiguous (both parts ≤ 12) instead of silently defaulting to US format
- [ ] **FIX-02**: `set_tz` uses proper timezone identity comparison (not string equality) to avoid spurious conversions between semantically equivalent timezones
- [ ] **FIX-03**: `infer_freq` emits `UserWarning` when a 1-day timedelta is detected, noting it cannot distinguish `'B'` from `'D'`
- [ ] **FIX-04**: `to_dense` normalizes the `freq` alias before the no-op string comparison (so `'1D'` and `'D'` are treated as equivalent)
- [ ] **FIX-05**: `tsplot` and `tsplot_dual` validate `hlines`, `vlines`, `title`, `subtitle`, and `date_format` parameter types with clear error messages

### Documentation Fixes

- [ ] **DOC-01**: `__init__.py` docstring removes Parquet mention from `read_ts`/`write_ts` description
- [ ] **DOC-02**: `_backend.py` documents `IS_JUPYTER` cached-at-import behavior and its implications
- [ ] **DOC-03**: `__init__.py` documents `apply_theme()` global side-effect at import time
- [ ] **DOC-04**: `_manual_deconflict` docstring notes the display-coordinate approximation limitation

### Polish

- [ ] **POL-01**: `_detect_plotly_tickformat` uses median index diff instead of first/last span for tick format selection

## v2 Requirements

### I/O

- **IO-01**: `read_ts` supports Parquet files via pyarrow
- **IO-02**: `write_ts` supports Parquet output

### Robustness

- **ROB-01**: Upper-bound version constraints on core dependencies (pandas, plotly, matplotlib)
- **ROB-02**: `_manual_deconflict` uses display coordinates for accurate label spacing

## Out of Scope

| Feature | Reason |
|---------|--------|
| Parquet I/O | Adds pyarrow dependency complexity; CSV sufficient for v0.1 |
| adjustText bundling | Intentionally optional with graceful fallback |
| Dependency upper bounds | Not a bug; opt-in policy deferred |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TEST-01 | Phase 1 | Complete |
| TEST-02 | Phase 1 | Pending |
| TEST-03 | Phase 1 | Pending |
| TEST-04 | Phase 1 | Pending |
| TEST-05 | Phase 1 | Pending |
| TEST-06 | Phase 1 | Pending |
| DEP-01 | Phase 2 | Pending |
| DEP-02 | Phase 2 | Pending |
| FIX-01 | Phase 2 | Pending |
| FIX-02 | Phase 2 | Pending |
| FIX-03 | Phase 2 | Pending |
| FIX-04 | Phase 2 | Pending |
| FIX-05 | Phase 2 | Pending |
| DOC-01 | Phase 3 | Pending |
| DOC-02 | Phase 3 | Pending |
| DOC-03 | Phase 3 | Pending |
| DOC-04 | Phase 3 | Pending |
| POL-01 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-15*
*Last updated: 2026-03-15 after initial definition*
