# Phase 5: Bloomberg BDH Historical Data Integration - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a `read_bdh()` function to pxts that fetches historical time series data from Bloomberg using the pdblp wrapper and returns a validated pandas DataFrame with DatetimeIndex — ready to pass directly into pxts's existing transform and plot functions.

</domain>

<decisions>
## Implementation Decisions

### Connection method
- Use `pdblp` wrapper library (not raw `blpapi`) — simplicity wins, io function is ~10s of lines to reshape data
- pxts opens and closes its own pdblp `BCon` connection per `read_bdh()` call (open + fetch + close)
- No module-level cached connection — stateless, clean, no lifecycle management burden

### API function design
- Lives in `src/pxts/io.py` alongside `read_ts()` and `write_ts()` — consistent with STRUCTURE.md convention ("New I/O format → io.py")
- Exposed in `__init__.py` and added to `TsAccessor` (same pattern as all other public functions)
- Signature: `read_bdh(tickers, start, field='PX_LAST', end=None)`
  - `tickers`: always a list of Bloomberg ticker strings (e.g., `['AAPL US Equity', 'MSFT US Equity']`)
  - `field`: single string, defaults to `'PX_LAST'`
  - `start`: required, flexible format (str, datetime, pd.Timestamp) — pxts converts to `'YYYYMMDD'` internally
  - `end`: optional, defaults to today when `None`

### Multi-ticker output shape
- Wide format: DatetimeIndex rows, one column per ticker (column names = raw Bloomberg ticker strings)
- Single-ticker list returns a single-column DataFrame (same structure, not special-cased)
- Drops directly into `plot_ts(df)` — each ticker becomes a line
- Return data as-is from Bloomberg (trading days only, no auto-fill) — user calls `to_dense()` explicitly if needed
- `validate_ts()` called on output before returning — returned DataFrame is guaranteed to be a pxts-standard DataFrame

### Missing dependency handling
- `pdblp` import attempted inside `read_bdh()` at call time (not at module level)
- If not installed: raises `ImportError` with `"pdblp required: pip install pxts[bloomberg]"` hint
- `pdblp` added to `pyproject.toml` as optional dependency group named `bloomberg`
- Connection errors (terminal not running, BCon() failure): let pdblp exceptions propagate unwrapped — trust pdblp's own error messages

### Claude's Discretion
- Exact pdblp `BCon` parameters (port, timeout)
- How `'YYYYMMDD'` string conversion handles edge cases in date parsing
- Test approach for read_bdh (mocking pdblp connection similar to how plot tests mock backends)

</decisions>

<specifics>
## Specific Ideas

- "The io function is merely 10s of lines of code to reshape the data into the pxts standard format" — keep it minimal, no over-engineering
- User preference: simplicity over feature completeness (same philosophy as existing io.py functions)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `validate_ts(df)` — must be called on output before returning, same as every other public function
- `read_ts()` / `write_ts()` in `io.py` — structural template: function at module level, exposed via `__init__.__all__`, delegated via `TsAccessor`
- `pxtsValidationError` — available if needed for custom errors, but decision is to let pdblp errors propagate unwrapped

### Established Patterns
- Optional dependency: import inside function body, raise `ImportError` with install hint if missing (plotly pattern in `_backend.py`)
- Flexible date input: `pd.to_datetime()` already used in `io.py` for format-flexible date parsing
- Immutability: all public functions return new DataFrames, never modify in-place
- `__all__` in `__init__.py` is the explicit star import surface — `read_bdh` must be added there

### Integration Points
- `src/pxts/io.py` — add `read_bdh()` here
- `src/pxts/__init__.py` — add to `__all__` and import
- `src/pxts/accessor.py` — add `read_bdh()` method to `TsAccessor` (delegation only, no logic)
- `pyproject.toml` — add `[project.optional-dependencies]` bloomberg group with `pdblp`

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-bloomberg-bdh-historical-data-integration*
*Context gathered: 2026-03-16*
