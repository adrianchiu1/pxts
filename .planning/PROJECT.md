# pxts — Project Reference

## What This Is

`pxts` is a production-ready Python library providing financial time series utilities for pandas — validation, timezone normalization, frequency inference, CSV I/O, optional Bloomberg BDH integration, and dual-backend (matplotlib/plotly) visualization via a clean `.ts` accessor interface. v0.1 shipped with a complete test suite (126 tests), 5 silent bug fixes, accurate documentation, and zoom-responsive Plotly rendering.

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
- ✓ Test suite: 126 tests across 6 modules — v0.1
- ✓ `cycler` declared as explicit runtime dep; `adjustText` optional with warning — v0.1
- ✓ 5 silent bug fixes (date warning, tz identity, B/D weekday, freq alias, param validation) — v0.1
- ✓ Accurate docstrings (CSV-only, IS_JUPYTER, apply_theme side-effect, _manual_deconflict) — v0.1
- ✓ Zoom-responsive Plotly date axis (tickformatstops) + legend visibility — v0.1
- ✓ Bloomberg BDH integration (`read_bdh()`) via optional `pdblp` — v0.1

### Active

*(empty — planning next milestone)*

### Out of Scope

- Parquet support for `read_ts`/`write_ts` — deferred to v0.2; pyarrow dep adds complexity
- Upper-bound version pinning on dependencies — opt-in policy
- `adjustText` bundling — intentionally optional; graceful fallback exists
- `_manual_deconflict` display-coordinate spacing — deferred; current approximation documented

## Context

**Current state (as of v0.1):**
- Library: `src/pxts/` — core.py, io.py, plots.py, theme.py, _backend.py, accessor.py
- Test suite: `tests/` — 6 modules, 126 passing tests, fully CI-ready
- Optional Bloomberg extra: `pip install pxts[bloomberg]` → adds pdblp
- Plotly date axes use 4-tier tickformatstops (decade/year/month/day)
- `apply_theme()` called at import — registers pxts Plotly template and sets matplotlib style

**Tech debt from v0.1:**
- `TsAccessor.read_bdh()` ignores `self._obj` — Bloomberg pull is ticker-driven; consider docstring clarification
- `read_bdh()` cannot be exercised without a live Bloomberg terminal (unit tests mock BCon)
- `_manual_deconflict` uses data-unit spacing (approximation) — display-coordinate version deferred

**Codebase map:** `.planning/codebase/` (created 2026-03-13)

## Constraints

- **Python**: >= 3.9 — must maintain compatibility
- **pandas**: >= 2.0 — core dependency, no changes to minimum version
- **Test style**: Unit tests per module — fast, isolated, mocked backends

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Fix docs over adding Parquet | CSV-only is sufficient for v0.1; Parquet adds pyarrow dep complexity | ✓ Good — scope stayed manageable |
| Unit tests per module | Fast feedback, isolated failures, clear ownership | ✓ Good — 126 tests, all fast |
| Warn on ambiguous date format (not error) | Backward-compatible; silent corruption is worse | ✓ Good — UserWarning on ambiguous slash dates |
| Remove `_detect_plotly_tickformat` entirely | tickformatstops is cleaner and zoom-responsive | ✓ Good — no fallback needed |
| showlegend=True in template (not per-function) | Single point of control, consistent across all Plotly output | ✓ Good — theme.py is the right place |
| Bloomberg as optional dep (not core) | Keeps base install lightweight; most users don't have Bloomberg | ✓ Good — `pip install pxts[bloomberg]` pattern |
| patch.dict(sys.modules) for lazy-import mocking | pdblp imported lazily inside read_bdh; no module-level attribute to patch | ✓ Good — correct pattern for optional deps |

---
*Last updated: 2026-03-17 after v0.1 milestone*
