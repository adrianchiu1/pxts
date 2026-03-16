# pxts

Financial time series utilities for pandas — load, manipulate, and visualize with no boilerplate.

![Python >= 3.9](https://img.shields.io/badge/python-%3E%3D3.9-blue)
![pandas >= 2.0](https://img.shields.io/badge/pandas-%3E%3D2.0-blue)

## What it is

pxts is a Python library that wraps pandas for financial time series workflows. It auto-detects date formats (ISO 8601, UK DD/MM/YYYY, US MM/DD/YYYY) when reading CSVs, so you spend less time debugging date parsing. It provides dual-backend visualization — matplotlib for scripts, plotly for Jupyter notebooks — selected automatically at import time. The Okabe-Ito colorblind-safe palette and a clean white/gray-grid style are applied to both backends at import.

## Installation

```bash
# Core (validation, I/O, no plotting)
pip install pxts

# With plotting backends
pip install pxts[plot]

# With Bloomberg BDH support (requires Bloomberg Terminal + API)
pip install pxts[bloomberg]
```

## Quick start

### Read a CSV

```python
from pxts import read_ts, write_ts

df = read_ts("prices.csv")            # date format auto-detected
df = read_ts("prices.csv", tz="UTC")  # localize to UTC
write_ts(df, "prices_out.csv")        # ISO 8601 round-trip
```

### Core utilities

```python
from pxts import validate_ts, set_tz, to_dense, infer_freq

validate_ts(df)                      # raises pxtsValidationError if no DatetimeIndex
df = set_tz(df, tz="US/Eastern")     # normalize timezone
df = to_dense(df, freq="B")          # fill to business-day frequency
freq = infer_freq(df)                # returns "B", "D", "W", etc.
```

### Plot time series

```python
from pxts import tsplot, tsplot_dual

# Single-axis: all columns or a subset
tsplot(df, title="Equity Prices")
tsplot(df, cols=["AAPL", "MSFT"], hlines=[100.0], labels=True)

# Dual-axis: left vs right y-axis
tsplot_dual(df, left=["AAPL"], right=["10Y_YIELD"],
            title="Price vs Yield", ylim_lhs=[80, 200], ylim_rhs=[0, 5])
```

### Bloomberg BDH

Requires `pxts[bloomberg]` and a live Bloomberg Terminal connection.

```python
from pxts import read_bdh

df = read_bdh(
    tickers=["AAPL US Equity", "MSFT US Equity"],
    start="2023-01-01",
    end="2024-01-01",
    field="PX_LAST",          # default
)
# Returns wide-format DataFrame: rows = dates, columns = tickers
```

## The .ts accessor

Importing pxts registers a `.ts` accessor on `pd.DataFrame`. This lets you chain core operations directly on a DataFrame without repeated imports.

```python
import pxts  # registers .ts on pd.DataFrame

df = df.ts.set_tz("UTC")
df = df.ts.to_dense(freq="D")
freq = df.ts.infer_freq()
```

## API reference

| Function / Name | Description | Notes |
|---|---|---|
| `read_ts(path, *, tz, date_format)` | Read CSV into DatetimeIndex DataFrame | Auto-detects ISO/UK/US dates |
| `write_ts(df, path, *, date_format)` | Write DataFrame to CSV | Defaults to ISO 8601 |
| `read_bdh(tickers, start, field, end)` | Fetch Bloomberg BDH historical data | Requires `pxts[bloomberg]` |
| `validate_ts(df)` | Assert DatetimeIndex; raises `pxtsValidationError` | Also returns `df` for chaining |
| `set_tz(df, tz)` | Localize or convert index timezone | `tz='UTC'`, `'US/Eastern'`, etc. |
| `to_dense(df, freq, fill)` | Regularize sparse index to uniform freq | `fill=None` → forward-fill |
| `infer_freq(df)` | Infer minimum interval of index | Returns `'B'`, `'D'`, `'W'`, `'M'`, etc. |
| `tsplot(df, cols, ...)` | Single-axis time series line chart | Auto-selects matplotlib/plotly |
| `tsplot_dual(df, left, right, ...)` | Dual y-axis line chart | `left`/`right` are column lists |
| `pxtsValidationError` | Exception raised on invalid DatetimeIndex | Subclass of `ValueError` |
| `get_backend()` | Returns active backend: `'plotly'` or `'matplotlib'` | Auto-detected from environment |
| `IS_JUPYTER` | `True` if running in Jupyter/IPython | Cached at import time |

## Date format behavior

ISO 8601 (`YYYY-MM-DD`) is detected automatically and is unambiguous. For slash-delimited dates (`DD/MM/YYYY` or `MM/DD/YYYY`), pxts defaults to British format (`DD/MM/YYYY`) when the input is ambiguous and emits a `UserWarning`. US users with `MM/DD/YYYY` data should override explicitly: `read_ts("prices.csv", date_format='%m/%d/%Y')`.

## Theme

pxts applies the Okabe-Ito colorblind-safe palette and a clean white/gray-grid style to both matplotlib and plotly at import time.

## Requirements

- Python >= 3.9
- pandas >= 2.0
- cycler (listed as an explicit dependency; bundled with matplotlib)
- Optional: plotly >= 5.0, matplotlib >= 3.5 — install with `pxts[plot]`
- Optional: pdblp — install with `pxts[bloomberg]`; requires a Bloomberg Terminal
