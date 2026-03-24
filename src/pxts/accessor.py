"""pxts TsAccessor — pandas DataFrame accessor registered as .ts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from pxts.core import infer_freq, set_tz, to_dense, validate_ts  # noqa: F401
from pxts.io import write_ts as _write_ts, read_bdh as _read_bdh
from pxts.plots import tsplot as _plot


@pd.api.extensions.register_dataframe_accessor("ts")
class TsAccessor:
    """Accessor providing pxts methods on pandas DataFrames via df.ts.<method>().

    Registered as the 'ts' accessor. Requires a DatetimeIndex — raises
    AttributeError (pandas accessor protocol) if the index is not datetime.

    All methods delegate to the corresponding standalone functions in pxts.core
    and return new DataFrames (immutable).
    """

    def __init__(self, pandas_obj: pd.DataFrame) -> None:
        if not isinstance(pandas_obj.index, pd.DatetimeIndex):
            raise AttributeError(
                f"pxts .ts accessor requires a DatetimeIndex. "
                f"Got {type(pandas_obj.index).__name__}. "
                f"Use pd.DataFrame(..., index=pd.to_datetime(dates)) to fix."
            )
        self._obj = pandas_obj

    def set_tz(self, tz: str = "UTC") -> pd.DataFrame:
        """Normalize the DatetimeIndex timezone. See pxts.core.set_tz for details."""
        return set_tz(self._obj, tz=tz)

    def to_dense(self, freq: str | None = None, fill: str | None = None) -> pd.DataFrame:
        """Regularize a sparse DatetimeIndex to equal intervals. See pxts.core.to_dense."""
        return to_dense(self._obj, freq=freq, fill=fill)

    def infer_freq(self) -> str:
        """Infer minimum observed interval as a pandas offset alias. See pxts.core.infer_freq."""
        return infer_freq(self._obj)

    def write_ts(self, path: str | Path, *, date_format: str | None = None) -> None:
        """Write this DataFrame to CSV. See pxts.io.write_ts for details."""
        _write_ts(self._obj, path, date_format=date_format)

    def read_bdh(self, tickers, start, field: str = "PX_LAST", end=None) -> pd.DataFrame:
        """Fetch Bloomberg BDH historical data. See pxts.io.read_bdh for details."""
        return _read_bdh(tickers, start, field=field, end=end)

    def plot(
        self,
        *,
        xaxis=None,
        yaxis=None,
        yaxis2=None,
        font=None,
        dimension=None,
        title=None,
        annotations=None,
        source=None,
        backend=None,
        **kwargs: Any,
    ):
        """Plot time series columns as line charts. See pxts.plots.tsplot for details."""
        return _plot(
            self._obj,
            xaxis=xaxis,
            yaxis=yaxis,
            yaxis2=yaxis2,
            font=font,
            dimension=dimension,
            title=title,
            annotations=annotations,
            source=source,
            backend=backend,
            **kwargs,
        )
