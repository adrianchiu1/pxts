# Conventions

## Code Style

- **Python version target**: `>=3.9` (pyproject.toml)
- **`from __future__ import annotations`** used in `core.py`, `io.py`, `accessor.py` for postponed evaluation of annotations
- **Type hints**: used throughout public functions; NumPy-style docstrings with `Parameters`, `Returns`, `Raises` sections
- **Imports**: standard library first, then third-party (`pandas`, `matplotlib`, `plotly`), then local (`pxts.*`)
- **Lazy imports**: `matplotlib`, `plotly` imported inside functions/methods (not at module level) to avoid hard import-time failures when optional backends not installed

## Naming

| Entity | Convention | Example |
|--------|-----------|---------|
| Modules | `snake_case` | `core.py`, `_backend.py` |
| Public functions | `snake_case` | `validate_ts`, `plot_ts_dual` |
| Private helpers | `_snake_case` | `_detect_date_format`, `_plot_ts_mpl` |
| Constants | `SCREAMING_SNAKE_CASE` | `IS_JUPYTER`, `BACKGROUND_COLOR` |
| Classes | `PascalCase` | `TsAccessor` |
| Exception class | `pxts` prefix + `PascalCase` | `pxtsValidationError` |
| Regex patterns | `_NAME_RE` | `_ISO_RE`, `_SLASH_RE` |

## Function Design

- **Immutability**: all transformation functions return new DataFrames, never modify in place
- **Validate first**: every public function calls `validate_ts(df)` as its first operation
- **Keyword-only args**: I/O and plot functions use `*` to force keyword-only after required positional args
  ```python
  def read_ts(path, *, tz=None, date_format=None): ...
  def write_ts(df, path, *, date_format=None): ...
  ```
- **`**kwargs` forwarding**: `plot_ts` and `plot_ts_dual` accept `**kwargs` forwarded to the underlying backend call (e.g., `linewidth`, `alpha`)
- **No-op guards**: functions check if work is needed before doing it (e.g., `to_dense` returns `df` unchanged if already at target freq)
- **`backend=` override**: all plot functions accept explicit `backend='matplotlib'` or `backend='plotly'` to override auto-detection

## Error Handling

- **`pxtsValidationError(TypeError)`** — raised by standalone functions when input lacks DatetimeIndex
- **`AttributeError`** — raised by `TsAccessor.__init__` (required by pandas accessor protocol)
- **`ValueError`** — raised for logic errors (e.g., column not found, fewer than 2 data points for `infer_freq`)
- **`UserWarning`** — issued for non-fatal issues (e.g., timezone conversion, plotly fallback to matplotlib)
- **`ImportError`** — raised when required backend is missing (e.g., matplotlib not installed in non-Jupyter env)
- **Silent `pass`** on `ImportError` in `theme.py` — `apply_theme()` skips backends that aren't installed
- **Error messages include fix hints**: `"Use pd.DataFrame(..., index=pd.to_datetime(dates)) to fix."`

## Module Design

- **`__all__`** explicitly declared in `__init__.py` — defines the star import surface
- **`apply_theme()`** called once at `pxts` import time (module-level side effect)
- **`IS_JUPYTER`** set once at `_backend.py` import time (module-level side effect)
- **Barrel-style `__init__.py`**: re-exports from all submodules; `TsAccessor` imported for its registration side effect
- **`# noqa` comments** used in `__init__.py` for imports that are side-effect-only (e.g., `F401` for accessor registration)

## Comments and Docstrings

- Module-level docstrings describe public API and design decisions
- Function docstrings use NumPy style with `Parameters`, `Returns`, `Raises` sections
- Section separators: `# ---... # Section Name # ---...` with 75-char dashes
- Inline comments explain non-obvious decisions, cross-reference "Pitfalls" from research docs
  ```python
  ax2.grid(False)  # Pitfall 2: avoid double-gridlines on right axis
  ```
- Design rationale comments document tradeoffs: `# No per-call overhead. Accepted trade-off: ...`
