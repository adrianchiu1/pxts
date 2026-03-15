# Roadmap: pxts v0.1 Hardening

## Overview

The library works but is unverified and has several silent failure modes. This milestone hardens pxts for production use in three phases: first establish a test suite so every change can be validated, then fix the silent bugs and fragile runtime behaviors the audit surfaced, then clean up misleading documentation and improve one low-severity algorithm. When all three phases are complete a researcher can `from pxts import *` with confidence.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Test Suite** - Establish pytest-runnable unit tests for every module (completed 2026-03-15)
- [x] **Phase 2: Bug Fixes and Dependencies** - Fix all silent bugs and declare missing runtime dependencies (completed 2026-03-15)
- [ ] **Phase 3: Documentation and Polish** - Correct misleading docstrings and improve tick format selection

## Phase Details

### Phase 1: Test Suite
**Goal**: The library has a passing test suite that can detect regressions in every module
**Depends on**: Nothing (first phase)
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06
**Success Criteria** (what must be TRUE):
  1. `pytest` runs from the project root with zero collection errors and zero failures
  2. `test_core.py` exercises `validate_ts`, `set_tz`, `to_dense`, and `infer_freq` including their edge cases (bad index, ambiguous tz, alias normalization, B-vs-D)
  3. `test_io.py` exercises `read_ts` and `write_ts` including the ambiguous date format path
  4. `test_plots.py` exercises `tsplot` and `tsplot_dual` for both backends using mocked rendering
  5. `test_accessor.py` and `test_theme.py` confirm delegation and theme isolation respectively
**Plans**: 5 plans

Plans:
- [x] 01-01-PLAN.md — Pytest infrastructure: tests/__init__.py and conftest.py with shared fixtures
- [ ] 01-02-PLAN.md — test_core.py: validate_ts, set_tz, to_dense, infer_freq with edge cases
- [ ] 01-03-PLAN.md — test_io.py: read_ts, write_ts, _detect_date_format including ambiguous date path
- [x] 01-04-PLAN.md — test_plots.py: tsplot and tsplot_dual for both backends (mocked rendering)
- [ ] 01-05-PLAN.md — test_accessor.py and test_theme.py: delegation and theme isolation

### Phase 2: Bug Fixes and Dependencies
**Goal**: All silent bugs are fixed and runtime dependencies are correctly declared
**Depends on**: Phase 1
**Requirements**: DEP-01, DEP-02, FIX-01, FIX-02, FIX-03, FIX-04, FIX-05
**Success Criteria** (what must be TRUE):
  1. `cycler` is listed in `pyproject.toml` dependencies so a fresh install cannot import-fail on theme application
  2. Importing pxts without `adjustText` installed prints a clear message explaining the fallback, not a silent degradation
  3. Loading an ambiguous slash-delimited CSV (e.g., `01/02/2024`) emits a `UserWarning` naming the assumed format
  4. Calling `set_tz` with a semantically equivalent timezone (e.g., `"Etc/UTC"` when index is already `"UTC"`) does not trigger a spurious conversion or warning
  5. Calling `infer_freq` on daily data emits a `UserWarning` noting the B-vs-D ambiguity; calling `to_dense(df, freq="1D")` on a `"D"` index is a recognized no-op
**Plans**: TBD

### Phase 3: Documentation and Polish
**Goal**: All docstrings accurately describe behavior and the tick format algorithm is more robust
**Depends on**: Phase 2
**Requirements**: DOC-01, DOC-02, DOC-03, DOC-04, POL-01
**Success Criteria** (what must be TRUE):
  1. `__init__.py` docstring mentions only CSV (no Parquet) for `read_ts`/`write_ts`
  2. `_backend.py` module docstring explains that `IS_JUPYTER` is cached at import and what that means for reload scenarios
  3. `__init__.py` documents the `apply_theme()` global side-effect so users are not surprised when pxts changes their matplotlib style
  4. `_detect_plotly_tickformat` uses median index diff so sparse datasets select an appropriate tick granularity
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Test Suite | 5/5 | Complete   | 2026-03-15 |
| 2. Bug Fixes and Dependencies | 3/3 | Complete   | 2026-03-15 |
| 3. Documentation and Polish | 0/? | Not started | - |
