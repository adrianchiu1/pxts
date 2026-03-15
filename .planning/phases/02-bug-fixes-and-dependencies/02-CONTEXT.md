# Phase 2: Bug Fixes and Dependencies - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix 5 silent bugs and declare 2 missing runtime dependencies. Scope is entirely within existing functions — no new capabilities. When complete, `from pxts import *` works correctly without hidden failure modes.

Requirements: DEP-01, DEP-02, FIX-01, FIX-02, FIX-03, FIX-04, FIX-05

</domain>

<decisions>
## Implementation Decisions

### Warning message style (FIX-01)
- `_detect_date_format` ambiguous date warning should be actionable: include the assumed format AND the override parameter hint
- Example: `"pxts: ambiguous date '01/02/2024' — assumed MM/DD/YYYY (US). Pass date_format='%d/%m/%Y' to override."`
- Standard `warnings.warn(..., UserWarning, stacklevel=2)` — filterable by user

### B-vs-D frequency detection (FIX-03 — behavior change)
- `infer_freq` should auto-detect 'B' vs 'D' intelligently, not just warn
- Logic: if minimum diff is 1 day AND no Saturday or Sunday exists in the DatetimeIndex → return `'B'` (business day)
- If weekends are present (or ambiguous) → return `'D'` (calendar day)
- No UserWarning needed — the function is now smart enough to distinguish the two cases

### Timezone identity comparison (FIX-02)
- `set_tz` must use semantic timezone comparison, not string equality
- Normalize both timezone names via pytz or zoneinfo to a canonical key before comparing
- Handles equivalences like `'UTC'` vs `'Etc/UTC'` vs `'pytz.UTC'`
- No warning emitted when zones are semantically identical

### adjustText missing message (DEP-02)
- Warn at **first call** to `tsplot`/`tsplot_dual`, not at import time
- Use `warnings.warn(UserWarning)` — suppressible via `warnings.filterwarnings`
- Fire only **once per session** — use a module-level flag (`_ADJUSTTEXT_WARNED = False`)
- After first warning, silently fall back to `_manual_deconflict` on subsequent calls

### Parameter validation error type (FIX-05)
- Use `ValueError` for bad parameter types in `tsplot` and `tsplot_dual`
- Validate **type only**: `hlines`/`vlines` must be `list | None`, `title`/`subtitle`/`date_format` must be `str | None`
- No value-range checks — just catch the wrong-type cases that currently produce confusing deep errors

### Claude's Discretion
- Exact canonical timezone key format (pytz vs zoneinfo vs `pd.DatetimeTZDtype` — choose what's most compatible with the existing pandas version constraint)
- Error message phrasing for FIX-05 (as long as it names the parameter and expected type)
- FIX-04 (`to_dense` freq alias normalization) — use `to_offset(freq).freqstr` for normalization before the no-op comparison; implementation is straightforward

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `validate_ts(df)`: already called at the top of every public function — parameter validation (FIX-05) should follow the same entry-point pattern
- `pxtsValidationError` (TypeError subclass): exists in `exceptions.py` — but user decided FIX-05 should raise plain `ValueError` instead
- `warnings` module: already imported in `core.py` — pattern exists for `warnings.warn`
- `to_offset()` from `pandas.tseries.frequencies`: already imported in `core.py` — usable for FIX-04 freq normalization

### Established Patterns
- All public functions call `validate_ts(df)` first, then do their work — FIX-05 validation should go immediately after `validate_ts`
- `_manual_deconflict` fallback: already implemented in `plots.py` — DEP-02 should wire the module-level flag to trigger before this fallback runs
- `warnings.warn(..., UserWarning, stacklevel=2)` pattern already used in `set_tz` for tz-conversion warnings

### Integration Points
- `pyproject.toml`: DEP-01 adds `cycler` to `[project].dependencies`
- `plots.py` top-level: module-level `_ADJUSTTEXT_WARNED` flag for DEP-02 once-per-session behavior
- `core.py:infer_freq()`: FIX-03 logic change (weekend detection) goes inside the 1-day timedelta branch
- `core.py:set_tz()`: FIX-02 replaces the fragile string comparison at lines 42-44
- `core.py:to_dense()`: FIX-04 normalizes `freq` via `to_offset(freq).freqstr` before the `freqstr == freq` guard at line 79
- `io.py:_detect_date_format()`: FIX-01 adds `warnings.warn` in the ambiguous branch at line 61-62

</code_context>

<specifics>
## Specific Ideas

- `infer_freq` B-vs-D: check `any(ts.weekday() >= 5 for ts in df.index)` — if no weekend timestamps → return `'B'`
- adjustText once-per-session: `global _ADJUSTTEXT_WARNED` pattern, set to True after first warning

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-bug-fixes-and-dependencies*
*Context gathered: 2026-03-15*
