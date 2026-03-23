"""pxts: Financial time series utilities for pandas.

Core value: A researcher can `from pxts import *` and immediately
load, manipulate, and visualize financial time series — with no
boilerplate and no surprises.

Public API (all accessible via star import):
  validate_ts(df)                 — validate DatetimeIndex
  set_tz(df, tz='UTC')           — normalize timezone
  to_dense(df, freq, fill=None)  — regularize sparse index
  infer_freq(df)                  — infer minimum interval
  pxtsValidationError            — exception class
  read_ts(path)                   — read CSV into validated DataFrame
  write_ts(df, path)              — write DataFrame to CSV
  read_bdh(tickers, start, field='PX_LAST', end=None) — fetch Bloomberg BDH data
  read_mb(series_names, *, unified=False, ...) — fetch Macrobond time series data
  get_backend()                   — return active backend name ('plotly' or 'matplotlib')
  IS_JUPYTER                      — bool, True if running in a Jupyter/IPython kernel
  tsplot(df, cols=None, ...)      — plot time series (single or dual axis via yaxis2)

The .ts accessor is registered automatically on import of this module.
Usage: df.ts.set_tz() / df.ts.to_dense(freq='D') / df.ts.infer_freq()

The pxts visual theme (FT palette by default, white background, gray grid) is applied
automatically at import time to all installed backends (plotly and/or matplotlib).
The Okabe-Ito colorblind-safe palette is available as OKABE_ITO_COLORS.

Global side-effect: `apply_theme()` is called automatically at import time. This
registers the pxts Plotly template as the default template and updates matplotlib
rcParams. Import pxts before other libraries that set matplotlib styles if you want
pxts styles to take effect last, or after if you want them first.
"""
import pandas as pd

# Verify minimum pandas version
_PANDAS_MIN = (2, 0)
_pandas_version = tuple(int(x) for x in pd.__version__.split(".")[:2])
if _pandas_version < _PANDAS_MIN:
    raise ImportError(
        f"pxts requires pandas >= {'.'.join(str(x) for x in _PANDAS_MIN)}. "
        f"Found pandas {pd.__version__}."
    )

from pxts.exceptions import pxtsValidationError  # noqa: E402
from pxts.core import validate_ts, set_tz, to_dense, infer_freq  # noqa: E402
from pxts.accessor import TsAccessor  # noqa: E402, F401 — import registers .ts accessor
from pxts.io import read_ts, write_ts, read_bdh, read_mb  # noqa: E402
from pxts._backend import get_backend, IS_JUPYTER  # noqa: E402
from pxts.theme import apply_theme, FT_COLORS, OKABE_ITO_COLORS  # noqa: E402
from pxts.plots import tsplot  # noqa: E402

apply_theme()  # Runs once at import — registers plotly template + sets matplotlib rcParams

__all__ = [
    "validate_ts",
    "set_tz",
    "to_dense",
    "infer_freq",
    "pxtsValidationError",
    "read_ts",
    "write_ts",
    "read_bdh",
    "read_mb",
    "get_backend",
    "IS_JUPYTER",
    "tsplot",
    "FT_COLORS",
    "OKABE_ITO_COLORS",
]

__version__ = "0.1.0"
