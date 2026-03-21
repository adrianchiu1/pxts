# pxts

Financial time series utilities for pandas — load, manipulate, and visualize with no boilerplate.

![Python >= 3.9](https://img.shields.io/badge/python-%3E%3D3.9-blue)
![pandas >= 2.0](https://img.shields.io/badge/pandas-%3E%3D2.0-blue)
[![MIT License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What it is

pxts is a Python library that wraps pandas for financial time series workflows. It provides:

- **Smart date parsing** — auto-detects ISO 8601, UK (`DD/MM/YYYY`), and US (`MM/DD/YYYY`) formats when reading CSVs
- **Dual-backend charting** — matplotlib for scripts, Plotly for Jupyter notebooks, selected automatically at import
- **FT-style chart layout** — accent line, title/subtitle framing, source attribution, Outfit font family, and a clean no-spine aesthetic inspired by Financial Times charts
- **Interactive Plotly features** — unified hover tooltip with vertical spike line, auto-detected date formatting based on data periodicity
- **End-of-line labels** — replace legends with series names placed at each line's last data point, with collision avoidance
- **Dual-axis support** — left/right y-axis via a single `tsplot()` call with `yaxis`/`yaxis2` dicts
- **Colorblind-safe palette** — Okabe-Ito colors applied to both backends at import

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

### Read and write CSVs

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

A single `tsplot()` function handles both single-axis and dual-axis charts:

```python
from pxts import tsplot

# Simple — plots all columns
tsplot(df, title={"main": "Equity Prices", "sub": "Daily close"})

# With end-of-line labels instead of a legend
tsplot(df,
       yaxis={"cols": ["AAPL", "MSFT"]},
       labels=True,
       source=["LSEG"])

# Dual-axis — left vs right y-axis
tsplot(df,
       yaxis={"cols": ["AAPL"], "name": "Price ($)"},
       yaxis2={"cols": ["10Y_YIELD"], "name": "Yield (%)"},
       title={"main": "Price vs Yield"},
       annotations={"hline": [100.0], "vline": ["2024-01-01"]})

# Column renaming via dict
tsplot(df,
       yaxis={"cols": {"Apple": "AAPL", "Microsoft": "MSFT"}},
       labels=True)
```

### Bloomberg BDH

Requires `pxts[bloomberg]` and a live Bloomberg Terminal connection.

```python
from pxts import read_bdh

df = read_bdh(
    tickers=["AAPL US Equity", "MSFT US Equity"],
    start="2023-01-01",
    end="2024-01-01",
    field="PX_LAST",
)
```

## The `.ts` accessor

Importing pxts registers a `.ts` accessor on `pd.DataFrame`:

```python
import pxts

df = df.ts.set_tz("UTC")
df = df.ts.to_dense(freq="D")
freq = df.ts.infer_freq()
```

## `tsplot()` parameters

| Parameter | Type | Description |
|---|---|---|
| `df` | DataFrame | Must have a DatetimeIndex |
| `xaxis` | dict | `range`, `name` |
| `yaxis` | dict | `cols` (list or dict), `range`, `name` |
| `yaxis2` | dict | Same as `yaxis` — triggers dual-axis mode |
| `title` | dict | `main` (str), `sub` (str) |
| `annotations` | dict | `hline` (list/dict), `vline` (list/dict) |
| `source` | list | e.g. `["LSEG", "Bloomberg"]` → rendered as `Source: LSEG, Bloomberg` |
| `labels` | bool | End-of-line labels instead of legend (single-axis only) |
| `font` | dict | `size`, `family` |
| `dimension` | dict | `width` (default 550), `aspect_ratio` (default 1.5) |
| `backend` | str | `"matplotlib"` or `"plotly"` — defaults to auto-detected backend |

## API reference

| Function | Description |
|---|---|
| `read_ts(path, *, tz, date_format)` | Read CSV with auto-detected date parsing |
| `write_ts(df, path, *, date_format)` | Write CSV in ISO 8601 format |
| `read_bdh(tickers, start, field, end)` | Fetch Bloomberg BDH historical data |
| `validate_ts(df)` | Assert DatetimeIndex; raises `pxtsValidationError` |
| `set_tz(df, tz)` | Localize or convert index timezone |
| `to_dense(df, freq, fill)` | Regularize sparse index to uniform frequency |
| `infer_freq(df)` | Infer minimum interval (`"B"`, `"D"`, `"W"`, `"M"`, etc.) |
| `tsplot(df, ...)` | Time series chart — single or dual axis |
| `get_backend()` | Returns `"plotly"` or `"matplotlib"` |
| `IS_JUPYTER` | `True` if running in Jupyter/IPython |
| `pxtsValidationError` | Exception for invalid DatetimeIndex |

## Date format behavior

ISO 8601 (`YYYY-MM-DD`) is unambiguous and detected automatically. For slash-delimited dates, pxts defaults to British format (`DD/MM/YYYY`) when ambiguous and emits a `UserWarning`. Override explicitly for US dates: `read_ts("prices.csv", date_format='%m/%d/%Y')`.

## Theme

pxts applies an FT-inspired visual theme at import time to both backends:

- **Plotly**: Outfit font, FT-style accent line, horizontal gridlines only, white background, unified hover tooltip with vertical spike line
- **matplotlib**: natural mpl defaults with title/subtitle/source framing, colorblind-safe palette

## Requirements

- Python >= 3.9
- pandas >= 2.0
- cycler
- Optional: `plotly >= 5.0`, `matplotlib >= 3.5`, `adjustText` — install with `pxts[plot]`
- Optional: `pdblp` — install with `pxts[bloomberg]` (requires Bloomberg Terminal)
