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

# With Macrobond Data API support
pip install pxts[macrobond]
```

## Quick start

### Read and write CSVs

```python
from pxts import read_csv, write_csv

df = read_csv("prices.csv")            # date format auto-detected
df = read_csv("prices.csv", tz="UTC")  # localize to UTC
write_csv(df, "prices_out.csv")        # ISO 8601 round-trip
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

### Plot price against position

`posplot()` shows how an asset traded alongside how much of it the portfolio held.
Position is signed, on a −100 to +100 scale:

```python
from pxts import posplot, read_csv

pos = read_csv("positions.csv")["XYZ"]     # dated positions, -100..+100

# A Bloomberg ticker and a position are enough: prices and volume are downloaded
posplot("XYZ US Equity", position=pos)

# Volume candles: candle width scales with that day's volume
posplot("XYZ US Equity", position=pos, kind="vcandle",
        xaxis={"range": ["2026-06-01", "2026-11-25"]})

# Compact: position as a colour band, sized like a standard tsplot figure
posplot("XYZ US Equity", position=pos, layout="strip", trades=False)
```

The position only needs a row on the dates it changes; it is held between them and is
flat before the first date. The download starts at the first position date.

To reuse a download, or to plot data from elsewhere, pass a DataFrame instead. Columns
named `open`, `high`, `low`, `close`, `volume` and `position` are picked up automatically:

```python
from pxts import read_bdh_ohlcv

px = read_bdh_ohlcv("XYZ US Equity", start="2025-01-01")
posplot(px, position=pos, kind="vcandle")

# Other column names
posplot(df, price="px_last", position="weight")
```

Triangles mark every change in position (up for a buy, down for a sell, sized by the
change). The dotted line is the average entry price of the open position; it resets
when the position crosses zero or goes flat.

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

### Macrobond

Requires `pxts[macrobond]` and a valid Macrobond Data+ or Data Feed subscription.

```python
from pxts import read_mb

# List — columns named by Macrobond FullDescription metadata
df = read_mb(["hg_c1_cl", "hg_c2_cl", "hg_c3_cl"])

# Single series
df = read_mb("hg_c1_cl")

# Dict — keys become output column names
df = read_mb({"Copper 1M": "hg_c1_cl", "Copper 2M": "hg_c2_cl"})

# Full history is returned; slice as needed
df = read_mb(["hg_c1_cl"])["2020":]
```

Returns a wide-format DataFrame with a `DatetimeIndex`. Series with different
start/end dates are aligned on the union of all dates; missing observations are
filled with `NaN`.

## The `.ts` accessor

Importing pxts registers a `.ts` accessor on `pd.DataFrame`:

```python
import pxts

df = df.ts.set_tz("UTC")
df = df.ts.to_dense(freq="D")
freq = df.ts.infer_freq()
df.ts.posplot(price="close", position="position")
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

## `posplot()` parameters

| Parameter | Type | Description |
|---|---|---|
| `df` | DataFrame or str | DataFrame with a DatetimeIndex, or a Bloomberg ticker to download |
| `price` | str or dict | Price column, or `{"open", "high", "low", "close"}` → column names. Defaults to columns with those names |
| `position` | str, Series or DataFrame | Signed, −100 to +100. A column name of `df`, or a dated Series / one-column DataFrame (required with a ticker) |
| `volume` | str | Volume column — needed for `kind="vcandle"` and `volume_pane=True`. Defaults to `volume` |
| `kind` | str | `"line"` (default), `"candle"`, or `"vcandle"` (candle width scales with volume) |
| `layout` | str | `"panes"` (default, position in its own pane) or `"strip"` (thin colour band) |
| `trades` | bool | Mark position changes and overlay the average entry price (default `True`) |
| `volume_pane` | bool | Add a volume bar pane under the price |
| `xaxis` | dict | `range` — restricts the plotted window |
| `yaxis` | dict | `range`, `name` — applies to the price pane |
| `title`, `source`, `font`, `backend` | | Same as `tsplot()` |
| `dim` | dict | `width`, `height`, `aspect_ratio` — default 700×440 for panes, 450×300 for strip |

Volume candles need room: widths are scaled to the 95th-percentile volume of the plotted
window, and a warning is issued below about 4 pixels per candle. On plotly, weekends are
removed from the axis for daily data; on matplotlib they show as gaps.

With a ticker, if Bloomberg has no volume (indices, FX, rates) or no open/high/low, the
chart falls back to plain candles or a line and says so in a warning.

## API reference

| Function | Description |
|---|---|
| `read_csv(path, *, tz, date_format)` | Read CSV with auto-detected date parsing |
| `write_csv(df, path, *, date_format)` | Write CSV in ISO 8601 format |
| `read_bdh(tickers, start, field, end, timeout)` | Fetch Bloomberg BDH historical data |
| `read_bdh_ohlcv(ticker, start, end, timeout)` | Fetch Bloomberg open/high/low/close/volume for one ticker |
| `read_mb(series)` | Fetch Macrobond historical time series data |
| `validate_ts(df)` | Assert DatetimeIndex; raises `pxtsValidationError` |
| `set_tz(df, tz)` | Localize or convert index timezone |
| `to_dense(df, freq, fill)` | Regularize sparse index to uniform frequency |
| `infer_freq(df)` | Infer minimum interval (`"B"`, `"D"`, `"W"`, `"M"`, etc.) |
| `tsplot(df, ...)` | Time series chart — single or dual axis |
| `posplot(df, ...)` | Price (line, candles or volume candles) alongside portfolio position |
| `get_backend()` | Returns `"plotly"` or `"matplotlib"` |
| `IS_JUPYTER` | `True` if running in Jupyter/IPython |
| `pxtsValidationError` | Exception for invalid DatetimeIndex |

## Date format behavior

ISO 8601 (`YYYY-MM-DD`) is unambiguous and detected automatically. For slash-delimited dates, pxts defaults to British format (`DD/MM/YYYY`) when ambiguous and emits a `UserWarning`. Override explicitly for US dates: `read_csv("prices.csv", date_format='%m/%d/%Y')`.

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
- Optional: `macrobond-data-api` — install with `pxts[macrobond]` (requires Macrobond subscription)
