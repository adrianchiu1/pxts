# Architecture

## Pattern

**Modular function-centric library with pandas accessor interface.**

The library is structured as a set of standalone public functions (in `core.py`, `io.py`, `plots.py`) that operate on pandas DataFrames with DatetimeIndex. A thin accessor class (`accessor.py`) wraps these functions and registers them as `df.ts.<method>()`. The theme and backend modules are cross-cutting concerns applied at import time.

## Layers

```
User Code
    ↓
Public API (pxts.__init__)         — star-importable functions + .ts accessor
    ↓
Domain Modules
├── core.py                        — validation + time series manipulation
├── io.py                          — CSV read/write with date format detection
└── plots.py                       — visualization (dispatches to backend)
    ↓
Support Modules
├── _backend.py                    — environment detection (Jupyter vs script)
├── theme.py                       — visual theming (plotly template + mpl rcParams)
└── exceptions.py                  — custom exception types
    ↓
accessor.py                        — pandas .ts accessor (delegates to domain modules)
```

## Data Flow

**Typical time series workflow:**

```
read_ts(path)
    → peek first row → _detect_date_format()
    → pd.read_csv() with detected format
    → returns pd.DataFrame with DatetimeIndex

validate_ts(df) / set_tz(df) / to_dense(df) / infer_freq(df)
    → pure transformation → returns new DataFrame (immutable)

plot_ts(df, cols, ...)
    → get_backend() → IS_JUPYTER check → 'plotly' or 'matplotlib'
    → _plot_ts_mpl() or _plot_ts_plotly()
    → returns Figure object
```

**Backend dispatch:**

```
get_backend()
    IS_JUPYTER=True  + plotly installed   → 'plotly'
    IS_JUPYTER=True  + plotly missing     → UserWarning → 'matplotlib'
    IS_JUPYTER=False + matplotlib installed → 'matplotlib'
    IS_JUPYTER=False + matplotlib missing  → ImportError
```

## Key Abstractions

- **`validate_ts(df)`** — gate function; raises `pxtsValidationError` (TypeError subclass) if no DatetimeIndex. Called at the start of every public function.
- **`IS_JUPYTER`** — module-level bool, evaluated once at `_backend` import time. Cached for zero per-call overhead. Trade-off: dynamic Jupyter entry mid-session won't re-detect.
- **`get_backend()`** — returns `'plotly'` or `'matplotlib'` string; checks library availability each call.
- **`pxtsValidationError`** — subclasses TypeError for dual catchability. Accessor raises AttributeError instead (pandas accessor protocol requirement).
- **`apply_theme()`** — idempotent, called once at `pxts` import. Registers `pio.templates['pxts']` for plotly; updates `plt.rcParams` for matplotlib. Silently skips missing backends.
- **`TsAccessor`** — pandas `@register_dataframe_accessor("ts")` wrapper. Pure delegation — no logic of its own.

## Entry Points

- **`from pxts import *`** — imports all public functions and registers the `.ts` accessor
- **`import pxts`** — same as above; `apply_theme()` is called automatically
- **`df.ts.<method>()`** — accessor interface, available after any pxts import
- **Standalone functions** — `pxts.plot_ts(df)`, `pxts.read_ts(path)`, etc.

## Cross-Cutting Concerns

- **Validation** — `validate_ts()` is the first call in every public function
- **Immutability** — all transformation functions return new DataFrames; never modify in-place
- **Backend abstraction** — `plots.py` calls `get_backend()` and dispatches; callers can override with `backend=` parameter
- **Error messaging** — errors include actionable fix hints (`"Use pd.DataFrame(..., index=pd.to_datetime(dates)) to fix."`)
