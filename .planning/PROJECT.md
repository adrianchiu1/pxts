# pxts — v0.1 Hardening

## What This Is

`pxts` is a Python library providing financial time series utilities for pandas — validation, timezone normalization, frequency inference, CSV I/O, and dual-backend (matplotlib/plotly) visualization via a clean `.ts` accessor interface. The goal of this milestone is to ship a production-ready v0.1 by resolving all known concerns from the codebase audit: adding a test suite, fixing silent bugs, and tightening edge cases.

## Core Value

A researcher can `from pxts import *` and confidently load, manipulate, and visualize financial time series — with no hidden bugs and no surprises.

## Requirements

### Validated

- ✓ DatetimeIndex validation (`validate_ts`) — existing
- ✓ Timezone normalization (`set_tz`) — existing
- ✓ Frequency inference (`infer_freq`) — existing
- ✓ Index densification (`to_dense`) — existing
- ✓ CSV read/write (`read_ts`, `write_ts`) — existing
- ✓ Dual-backend plotting (`tsplot`, `tsplot_dual`) — existing
- ✓ `.ts` accessor on pandas DataFrame — existing
- ✓ Okabe-Ito theme applied at import — existing
- ✓ Automatic Jupyter/script backend detection — existing

### Active

- [ ] Test suite: unit tests for all modules (test_core.py, test_io.py, test_plots.py, test_theme.py, test_accessor.py)
- [ ] Declare `cycler` as explicit runtime dependency in pyproject.toml
- [ ] Document `adjustText` as optional dependency; clarify fallback behavior in docs/type hints
- [ ] Fix silent US date default in `_detect_date_format` — emit UserWarning when format is ambiguous
- [ ] Fix timezone comparison fragility in `set_tz` — use proper tz identity check instead of string comparison
- [ ] Surface B-vs-D frequency ambiguity to user — emit warning from `infer_freq` when daily data detected
- [ ] Add input validation for `hlines`, `vlines`, `title`, `subtitle`, `date_format` in `tsplot`/`tsplot_dual`
- [ ] Fix `to_dense` no-op check — normalize freq alias before string comparison
- [ ] Fix `__init__.py` docstring — remove Parquet mention from `read_ts`/`write_ts` description
- [ ] Document `IS_JUPYTER` cached-at-import behavior in module docstring
- [ ] Document global theme side-effect (`apply_theme()`) in `__init__.py`
- [ ] Improve `_detect_plotly_tickformat` — use median diff instead of first/last span
- [ ] Improve `_manual_deconflict` — add note about display-coordinate limitation in docstring

### Out of Scope

- Parquet support for `read_ts`/`write_ts` — CSV-only for v0.1; Parquet deferred to v0.2
- Upper-bound version pinning on dependencies — opt-in policy; not a bug
- `adjustText` bundling — intentionally optional; graceful fallback exists

## Context

- Codebase map: `.planning/codebase/` (created 2026-03-13)
- Library uses `src/` layout with `pyproject.toml` for packaging
- Backend selection (`matplotlib` vs `plotly`) is automatic based on `IS_JUPYTER` constant
- `cycler` is a transitive matplotlib dependency — fragile to rely on implicitly
- No tests currently exist despite pytest being configured (`testpaths = ["tests"]`)

## Constraints

- **Python**: >= 3.9 — must maintain compatibility
- **pandas**: >= 2.0 — core dependency, no changes to minimum version
- **Test style**: Unit tests per module — fast, isolated, no heavy mocking of plot backends

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Fix docs over adding Parquet | CSV-only is sufficient for v0.1; Parquet adds pyarrow dep complexity | — Pending |
| Unit tests per module | Fast feedback, isolated failures, clear ownership | — Pending |
| Warn on ambiguous date format (not error) | Backward-compatible; silent corruption is worse than a warning | — Pending |

---
*Last updated: 2026-03-15 after initialization*
