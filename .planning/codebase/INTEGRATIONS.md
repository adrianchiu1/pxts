# External Integrations

**Analysis Date:** 2026-03-13

## APIs & External Services

**Not Applicable** - pxts does not integrate with external APIs or cloud services.

## Data Storage

**Databases:**
- Not integrated - pxts operates entirely on in-memory pandas DataFrames

**File Storage:**
- Local filesystem only
  - CSV file I/O via pandas
  - Functions: `read_ts()` and `write_ts()` in `src/pxts/io.py`
  - Date format auto-detection and explicit format support
  - ISO 8601, US (MM/DD/YYYY), and UK (DD/MM/YYYY) format support

**Caching:**
- None - pxts performs no caching

## Authentication & Identity

**Auth Provider:**
- Not applicable - pxts contains no authentication mechanisms

## Monitoring & Observability

**Error Tracking:**
- None - pxts raises standard Python exceptions without external reporting

**Logs:**
- Standard Python logging via `warnings` module only
  - UserWarning when plotly not installed in Jupyter (via `src/pxts/_backend.py`)
  - UserWarning when DatetimeIndex timezone is converted (via `src/pxts/core.py`)
  - No dedicated logging framework

## CI/CD & Deployment

**Hosting:**
- Not applicable - pxts is a library, not a deployed service

**CI Pipeline:**
- Not detected - No GitHub Actions, CircleCI, or other CI configuration found

**Package Distribution:**
- Standard PyPI distribution expected (via setuptools)

## Environment Configuration

**Required env vars:**
- None - pxts operates without environment variables

**Secrets location:**
- Not applicable - pxts contains no secrets or API keys

## Visualization Backends

**plotly Integration:**
```
Package: plotly >= 5.0 (optional)
Location: src/pxts/plots.py
Usage:
  - go.Figure() - figure creation
  - go.Scatter() - line traces
  - plotly.graph_objects - layout and annotation objects
  - plotly.subplots.make_subplots - dual-axis subplot creation
Theme Integration:
  - pio.templates for custom theme registration
  - pio.templates.default for setting default template
Config: src/pxts/theme.py applies custom "pxts" template
```

**matplotlib Integration:**
```
Package: matplotlib >= 3.5 (required for non-Jupyter)
Location: src/pxts/plots.py
Usage:
  - plt.subplots() - figure/axis creation
  - ax.plot() - line rendering
  - mdates.AutoDateLocator - date axis locator
  - mdates.DateFormatter - date axis formatting
  - ax.annotate() - text annotations
Theme Integration:
  - plt.rcParams.update() for global styling
  - cycler package for color cycle management
Config: src/pxts/theme.py applies rcParams globally
```

**Environment Detection:**
```
Package: IPython (optional, for Jupyter detection only)
Location: src/pxts/_backend.py
Usage:
  - get_ipython() - Jupyter/IPython kernel detection
  - IS_JUPYTER module-level constant
Purpose: Determines plotly vs matplotlib backend selection
Failure mode: ImportError caught; returns False if IPython not installed
```

## Pandas Integration

**Core Dependency:**
```
Package: pandas >= 2.0
Location: Used throughout codebase
Key integrations:
  - pd.DataFrame - primary data structure
  - pd.DatetimeIndex - required for all pxts operations
  - pd.to_datetime() - datetime parsing with auto-format detection (src/pxts/io.py)
  - pd.tseries.frequencies.to_offset() - frequency alias mapping (src/pxts/core.py)
  - pd.api.extensions.register_dataframe_accessor() - .ts accessor registration (src/pxts/accessor.py)
  - df.asfreq() - sparse-to-dense conversion (src/pxts/core.py)
  - df.index.tz_localize() / tz_convert() - timezone operations (src/pxts/core.py)
  - df.to_csv() - CSV writing (src/pxts/io.py)
  - pd.read_csv() - CSV reading (src/pxts/io.py)
```

## Webhooks & Callbacks

**Incoming:**
- Not applicable - pxts is a library without network listeners

**Outgoing:**
- Not applicable - pxts does not call external services

---

*Integration audit: 2026-03-13*
