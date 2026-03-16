# Structure

## Directory Layout

```
pxts/
├── src/
│   ├── pxts/                       # Main package source
│   │   ├── __init__.py             # Public API, star imports, apply_theme() call
│   │   ├── core.py                 # Validation + time series manipulation functions
│   │   ├── io.py                   # CSV read/write, date format auto-detection
│   │   ├── plots.py                # Visualization (matplotlib + plotly backends)
│   │   ├── _backend.py             # Environment detection (IS_JUPYTER, get_backend)
│   │   ├── theme.py                # Visual theming (Okabe-Ito palette, rcParams)
│   │   ├── accessor.py             # pandas .ts accessor (delegates to other modules)
│   │   └── exceptions.py           # pxtsValidationError exception class
│   └── pxts.egg-info/              # Build metadata (auto-generated)
├── pyproject.toml                  # Build config, dependencies, pytest config
└── .planning/
    └── codebase/                   # GSD codebase map (this directory)
```

## Key File Locations

| Concern | File |
|---------|------|
| Public API surface | `src/pxts/__init__.py` |
| DatetimeIndex validation | `src/pxts/core.py:12` — `validate_ts()` |
| Timezone normalization | `src/pxts/core.py:27` — `set_tz()` |
| Frequency inference | `src/pxts/core.py:84` — `infer_freq()` |
| CSV I/O + date detection | `src/pxts/io.py` |
| Date format heuristic | `src/pxts/io.py:31` — `_detect_date_format()` |
| Jupyter detection | `src/pxts/_backend.py:20` — `_detect_jupyter()` |
| Backend dispatch | `src/pxts/_backend.py:45` — `get_backend()` |
| Plot public API | `src/pxts/plots.py:481` — `plot_ts()`, `:520` — `plot_ts_dual()` |
| matplotlib plot impl | `src/pxts/plots.py:184` — `_plot_ts_mpl()` |
| plotly plot impl | `src/pxts/plots.py:234` — `_plot_ts_plotly()` |
| Dual-axis matplotlib | `src/pxts/plots.py:332` — `_plot_ts_dual_mpl()` |
| Dual-axis plotly | `src/pxts/plots.py:408` — `_plot_ts_dual_plotly()` |
| Color palette | `src/pxts/theme.py:20` — `pxts_COLORS` |
| Plotly theme registration | `src/pxts/theme.py:49` — `_apply_plotly_theme()` |
| Matplotlib theme application | `src/pxts/theme.py:89` — `_apply_matplotlib_theme()` |
| pandas .ts accessor | `src/pxts/accessor.py:14` — `TsAccessor` |
| Custom exception | `src/pxts/exceptions.py:4` — `pxtsValidationError` |

## Naming Conventions

- **Files**: `snake_case.py`; private/internal modules prefixed with `_` (e.g., `_backend.py`)
- **Public functions**: `snake_case` (e.g., `validate_ts`, `read_ts`, `plot_ts_dual`)
- **Private helpers**: leading underscore (e.g., `_detect_date_format`, `_plot_ts_mpl`, `_apply_sorted_legend_mpl`)
- **Constants**: `SCREAMING_SNAKE_CASE` (e.g., `IS_JUPYTER`, `BACKGROUND_COLOR`, `DEFAULT_FONT_SIZE`)
- **Classes**: `PascalCase` (e.g., `TsAccessor`) — exception: `pxtsValidationError` (lowercase prefix matches package name)
- **`__all__`** declared in `__init__.py` — explicit star import surface

## Where to Add New Features

| Feature type | Location |
|---|---|
| New time series transformation | `src/pxts/core.py` + expose in `__init__.py` + add to `TsAccessor` |
| New I/O format (e.g., Parquet) | `src/pxts/io.py` + expose in `__init__.py` + add to `TsAccessor` |
| New plot type | `src/pxts/plots.py` — add `_plot_<name>_mpl()`, `_plot_<name>_plotly()`, public `plot_<name>()` |
| New backend support | `src/pxts/_backend.py` — extend `get_backend()` logic |
| New exception type | `src/pxts/exceptions.py` |
| Theme changes | `src/pxts/theme.py` |
