# Testing

## Framework

- **pytest >= 7.0** (declared in `pyproject.toml` `[project.optional-dependencies] dev`)
- Test paths configured: `testpaths = ["tests"]` in `[tool.pytest.ini_options]`

## Current State

**No test files exist.** The `tests/` directory is absent from the repository. This is a critical gap — all functionality is untested.

The `pyproject.toml` declares pytest as a dev dependency and configures `testpaths = ["tests"]`, indicating tests are intended but not yet written.

## Expected Test Structure (when implemented)

```
tests/
├── conftest.py                 # Shared fixtures (sample DataFrames, tmp paths)
├── test_core.py                # validate_ts, set_tz, to_dense, infer_freq
├── test_io.py                  # read_ts, write_ts, _detect_date_format
├── test_plots.py               # plot_ts, plot_ts_dual (both backends)
├── test_backend.py             # get_backend, IS_JUPYTER detection
├── test_theme.py               # apply_theme, _apply_plotly_theme, _apply_matplotlib_theme
└── test_accessor.py            # TsAccessor delegation, AttributeError on non-DatetimeIndex
```

## Key Test Scenarios

### Core (`core.py`)
- `validate_ts` raises `pxtsValidationError` on non-DatetimeIndex
- `validate_ts` returns df unchanged on valid input
- `set_tz` localizes naive index silently
- `set_tz` returns same object when already at target tz (no-op)
- `set_tz` converts tz-aware index with UserWarning
- `to_dense` regularizes sparse index
- `to_dense` is no-op when already at target freq
- `infer_freq` raises ValueError for < 2 data points
- `infer_freq` returns correct offset alias for daily/hourly/monthly data

### I/O (`io.py`)
- `read_ts` parses ISO 8601 dates correctly
- `read_ts` parses US format (MM/DD/YYYY)
- `read_ts` parses UK format (DD/MM/YYYY) when day > 12
- `_detect_date_format` defaults to US for ambiguous slash dates (both parts ≤ 12)
- `write_ts` → `read_ts` round-trip preserves DatetimeIndex
- `write_ts` raises `pxtsValidationError` on non-DatetimeIndex df

### Backend (`_backend.py`)
- `get_backend` returns `'plotly'` in Jupyter with plotly installed
- `get_backend` falls back to `'matplotlib'` with UserWarning in Jupyter without plotly
- `get_backend` returns `'matplotlib'` outside Jupyter with matplotlib installed
- `get_backend` raises ImportError outside Jupyter without matplotlib
- Test with `monkeypatch` on `IS_JUPYTER` and module imports

### Plots (`plots.py`)
- `plot_ts` returns correct figure type per backend
- `plot_ts` raises ValueError for missing columns
- `plot_ts_dual` colors left/right axes correctly
- Both backends: title, subtitle, hlines, vlines, labels parameters
- `_detect_plotly_tickformat` returns correct format for short/medium/long spans

### Accessor (`accessor.py`)
- `TsAccessor` raises AttributeError on non-DatetimeIndex DataFrame
- `df.ts.set_tz()` delegates to `core.set_tz()`
- `df.ts.plot_ts()` delegates to `plots.plot_ts()`
- All accessor methods produce same result as standalone functions

## Mocking Strategy

- Use `monkeypatch` to set `pxts._backend.IS_JUPYTER` for backend tests
- Use `monkeypatch` on `sys.modules` to simulate missing plotly/matplotlib
- Use `tmp_path` pytest fixture for I/O round-trip tests
- Use `pytest.warns(UserWarning)` for tz conversion and backend fallback tests
- Parametrize backend tests to run the same assertions for both `'matplotlib'` and `'plotly'`
