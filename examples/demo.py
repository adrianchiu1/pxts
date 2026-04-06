"""pxts plotting demo
===================
Quick-start script that exercises the main tsplot() features.

Install
-------
    pip install pxts[plot]          # includes plotly + matplotlib

Or, from a local clone of the repo:
    pip install -e ".[plot]"

Expected CSV format (examples/data/sample.csv)
----------------------------------------------
The CSV must have a date column (any name) as the first column, followed by
one or more numeric columns.  Example layout::

    Date,Price_A,Price_B,Price_C,Volume
    2020-01-02,100.0,200.0,50.0,1500000
    2020-01-03,101.5,198.3,51.2,1320000
    ...

*Date* — parseable by pandas (ISO 8601 recommended: YYYY-MM-DD).
*Price_A / Price_B / Price_C* — series that share a common y-axis scale.
*Volume* — series on a different scale, used in the dual-axis examples below.

Adjust the column names in the section "--- column names ---" to match your
actual CSV before running.
"""

from pathlib import Path

import pandas as pd

import pxts
from pxts import tsplot

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

DATA_PATH = Path(__file__).parent / "data" / "sample.csv"

df = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
df.index = pd.DatetimeIndex(df.index)   # ensure DatetimeIndex

# --- column names -----------------------------------------------------------
# Edit these to match the actual columns in your CSV.
PRICE_COLS  = df.columns[:3].tolist()   # first 3 cols → left axis
VOLUME_COL  = df.columns[-1]            # last col      → right axis (dual)
# ---------------------------------------------------------------------------

print(f"Loaded {len(df):,} rows × {len(df.columns)} columns from {DATA_PATH.name}")
print(f"  Date range : {df.index[0].date()} → {df.index[-1].date()}")
print(f"  Columns    : {df.columns.tolist()}\n")

# ---------------------------------------------------------------------------
# 1. Minimal — all columns, Plotly (interactive)
# ---------------------------------------------------------------------------

fig = tsplot(df, backend="plotly")
fig.show()

# ---------------------------------------------------------------------------
# 2. Title + subtitle + source
# ---------------------------------------------------------------------------

fig = tsplot(
    df,
    title={"main": "Asset Prices", "sub": "Daily closing prices"},
    source=["Internal data"],
    backend="plotly",
)
fig.show()

# ---------------------------------------------------------------------------
# 3. Select specific columns, custom y-axis label
# ---------------------------------------------------------------------------

fig = tsplot(
    df,
    yaxis={"cols": PRICE_COLS, "name": "Price (USD)"},
    title={"main": "Selected Series"},
    backend="plotly",
)
fig.show()

# ---------------------------------------------------------------------------
# 4. End-of-line labels instead of legend
# ---------------------------------------------------------------------------

fig = tsplot(
    df,
    yaxis={"cols": PRICE_COLS},
    title={"main": "FT-style line labels"},
    labels=True,
    backend="plotly",
)
fig.show()

# ---------------------------------------------------------------------------
# 5. Dual axis (price left, volume right)
# ---------------------------------------------------------------------------

fig = tsplot(
    df,
    yaxis={"cols": PRICE_COLS,  "name": "Price (USD)"},
    yaxis2={"cols": [VOLUME_COL], "name": "Volume"},
    title={"main": "Price & Volume", "sub": "Dual-axis chart"},
    source=["Internal data"],
    backend="plotly",
)
fig.show()

# ---------------------------------------------------------------------------
# 6. Annotations — horizontal and vertical reference lines
# ---------------------------------------------------------------------------

fig = tsplot(
    df,
    yaxis={"cols": PRICE_COLS},
    title={"main": "With Annotations"},
    annotations={
        "hline": {"Support": df[PRICE_COLS[0]].min() * 1.05},
        "vline": [str(df.index[len(df) // 2].date())],   # midpoint marker
    },
    backend="plotly",
)
fig.show()

# ---------------------------------------------------------------------------
# 7. Custom dimensions and font
# ---------------------------------------------------------------------------

fig = tsplot(
    df,
    yaxis={"cols": PRICE_COLS},
    title={"main": "Wide format"},
    dimension={"width": 900, "aspect_ratio": 2.5},
    font={"size": 12},
    backend="plotly",
)
fig.show()

# ---------------------------------------------------------------------------
# 8. Matplotlib backend (returns a Figure — call fig.show() or fig.savefig())
# ---------------------------------------------------------------------------

import matplotlib.pyplot as plt

fig = tsplot(
    df,
    yaxis={"cols": PRICE_COLS},
    title={"main": "Matplotlib backend", "sub": "Static / publication output"},
    source=["Internal data"],
    backend="matplotlib",
)
plt.show()
