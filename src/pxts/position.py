"""pxts position module: market price alongside portfolio position.

Public API:
    posplot(df, *, price="close", position="position", volume=None,
            kind="line", layout="panes", trades=True, volume_pane=False,
            xaxis=None, yaxis=None, font=None, dim=None, title=None,
            source=None, backend=None)

The chart answers "how did the asset trade, and how much of it did we hold?".
Price is drawn as a line, candlesticks or volume candles (candle width scales
with that period's volume). Position is a signed step on a fixed -100..+100
scale: either its own pane under the price (layout="panes") or a thin colour
band (layout="strip"). With trades=True, every change in position is marked
on the price and the average entry price of the open position is overlaid.

Candles are drawn by hand (a bar from open to close plus a low-high wick)
because neither backend offers per-candle widths. Ordinary candles use the
same code path with a constant width, so both backends render identically
and no extra dependency is needed.

Layout (top to bottom): accent line, title, subtitle, legend, price pane,
optional volume pane, position pane or strip, source.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from pxts._backend import get_backend
from pxts.core import validate_ts
from pxts.plots import (
    LayoutMetrics,
    _draw_accent_line_plotly,
    _draw_source_plotly,
    _draw_title_plotly,
    _estimate_legend_h_px,
    _infer_df_name,
    _infer_hover_date_format,
    _validate_axis_range,
)
from pxts.theme import (
    DOWN_COLOR,
    FT_FONT_COLOR,
    GRID_COLOR,
    POSITION_COLOR,
    STRIP_FLAT_COLOR,
    STRIP_LONG_COLOR,
    STRIP_SHORT_COLOR,
    UP_COLOR,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_KINDS = ("line", "candle", "vcandle")
_LAYOUTS = ("panes", "strip")
_OHLC_KEYS = ("open", "high", "low", "close")

# Default chart-area size (px) per layout. "panes" needs height for three
# stacked panes; "strip" fits the standard pxts figure.
_DEFAULT_DIM = {
    "panes": {"width": 700, "aspect_ratio": 700 / 440},
    "strip": {"width": 450, "aspect_ratio": 1.5},
}

_PANE_GAP_PX: int = 30         # gap between panes; holds the pane label
_STRIP_H_PX: int = 14          # exposure strip height
_STRIP_GAP_PX: int = 8         # gap between the strip and the pane above
_POS_PANE_FRAC: float = 0.22   # position pane share of the chart height
_POS_PANE_MIN_PX: int = 70
_VOL_PANE_FRAC: float = 0.12   # volume pane share of the chart height
_VOL_PANE_MIN_PX: int = 40

_CANDLE_WIDTH: float = 0.62    # ordinary candle width, fraction of one slot
_VCANDLE_MAX: float = 0.92     # widest volume candle, fraction of one slot
_VCANDLE_MIN: float = 0.12     # narrowest volume candle, relative to the widest
_VCANDLE_REF_Q: float = 0.95   # volume quantile that maps to the widest candle
_VCANDLE_MIN_SLOT_PX: float = 4.0  # below this, width differences are unreadable

_POS_LIMIT: float = 100.0
_POS_AXIS_PAD: float = 12.0    # headroom beyond +/-100 on the position axis

_MARKER_BASE_PX: float = 8.0   # trade marker size for a zero-size change
_MARKER_PER_UNIT: float = 0.12  # extra px per unit of position change

# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------


def _position_trades(price: pd.Series, position: pd.Series):
    """Derive trades and the average entry price from a signed position series.

    A trade is any row where the position differs from the previous row. The
    average entry price follows the open position:

    - adding to a position (same sign, larger size) moves it to the
      size-weighted average of the old entry and the current price;
    - reducing a position leaves it unchanged;
    - crossing zero resets it to the current price;
    - a flat position has no entry price (NaN).

    The position held on the first row is assumed to have been entered at the
    first price, since its true entry is unknown.

    Returns
    -------
    trades : pd.DataFrame
        Indexed by trade date with columns ``change`` (signed size of the
        trade), ``position`` (position after the trade) and ``price``.
    avg_entry : pd.Series
        Average entry price of the open position, NaN while flat.
    """
    px = price.to_numpy(dtype=float)
    pos = position.to_numpy(dtype=float)
    avg_entry = np.full(len(pos), np.nan)
    rows = []
    avg = px[0] if len(pos) and pos[0] != 0 else np.nan
    for i in range(len(pos)):
        prev = pos[i - 1] if i else pos[i]
        change = pos[i] - prev
        if change != 0:
            if pos[i] == 0:
                avg = np.nan
            elif prev == 0 or np.sign(pos[i]) != np.sign(prev):
                avg = px[i]
            elif abs(pos[i]) > abs(prev):
                avg = (avg * abs(prev) + px[i] * abs(change)) / abs(pos[i])
            rows.append((position.index[i], change, pos[i], px[i]))
        avg_entry[i] = avg
    trades = pd.DataFrame(
        [r[1:] for r in rows],
        index=pd.DatetimeIndex([r[0] for r in rows], name=position.index.name),
        columns=["change", "position", "price"],
        dtype=float,
    )
    return trades, pd.Series(avg_entry, index=position.index, name="avg_entry")


def _candle_width_fracs(volume, kind: str) -> np.ndarray:
    """Return each candle's width as a fraction of one time slot.

    kind="candle" gives a constant width. kind="vcandle" scales width linearly
    with volume: the 95th-percentile volume of the plotted window maps to the
    widest candle, anything above it is capped, and a floor keeps quiet
    periods visible.
    """
    n = len(volume) if volume is not None else 0
    if kind != "vcandle":
        return np.full(n, _CANDLE_WIDTH)
    v = np.nan_to_num(np.asarray(volume, dtype=float), nan=0.0)
    ref = np.quantile(v, _VCANDLE_REF_Q) if n else 0.0
    if not ref > 0:
        return np.full(n, _CANDLE_WIDTH)
    rel = np.clip(v / ref, 0.0, 1.0)
    return _VCANDLE_MAX * (_VCANDLE_MIN + (1 - _VCANDLE_MIN) * rel)


def _infer_slot(idx: pd.DatetimeIndex) -> pd.Timedelta:
    """Return the width of one time slot: the smallest gap between rows."""
    if len(idx) < 2:
        return pd.Timedelta(days=1)
    diffs = idx.to_series().diff().dropna()
    diffs = diffs[diffs > pd.Timedelta(0)]
    return diffs.min() if len(diffs) else pd.Timedelta(days=1)


def _position_text(pos: float) -> str:
    """Format a signed position for hover text, e.g. '+75 long'."""
    if pos == 0:
        return "flat"
    return f"{pos:+g} {'long' if pos > 0 else 'short'}".replace("-", "−")


@dataclass
class _PosData:
    """Arrays ready for drawing, restricted to the visible window."""
    idx: pd.DatetimeIndex
    open: Optional[np.ndarray]
    high: Optional[np.ndarray]
    low: Optional[np.ndarray]
    close: np.ndarray
    volume: Optional[np.ndarray]
    pos: np.ndarray
    avg_entry: np.ndarray
    trades: pd.DataFrame          # change, position, price, y
    up: np.ndarray                # bool per row: close >= open
    width_fracs: np.ndarray       # candle width, fraction of a slot
    slot: pd.Timedelta
    y_range: tuple                # price-pane y range
    kind: str


def _validate_posplot_params(df, price, position, volume, kind, layout,
                             xaxis, yaxis, font, dim, title, source) -> None:
    """Validate posplot arguments, raising ValueError with a fix hint."""
    if kind not in _KINDS:
        raise ValueError(f"kind must be one of {_KINDS}, got {kind!r}")
    if layout not in _LAYOUTS:
        raise ValueError(f"layout must be one of {_LAYOUTS}, got {layout!r}")

    if isinstance(price, dict):
        missing = [k for k in _OHLC_KEYS if k not in price]
        if kind != "line" and missing:
            raise ValueError(
                f"price dict is missing keys {missing}; kind={kind!r} needs "
                f"all of {list(_OHLC_KEYS)}."
            )
        if "close" not in price:
            raise ValueError("price dict must include a 'close' key.")
        price_cols = [price[k] for k in _OHLC_KEYS if k in price]
    elif isinstance(price, str):
        if kind != "line":
            raise ValueError(
                f"kind={kind!r} needs open/high/low/close columns. Pass "
                "price={'open': ..., 'high': ..., 'low': ..., 'close': ...}."
            )
        price_cols = [price]
    else:
        raise ValueError(
            f"price must be a column name or dict, got {type(price).__name__}")

    if kind == "vcandle" and volume is None:
        raise ValueError("kind='vcandle' needs a volume column. Pass volume='<column>'.")

    needed = price_cols + [position] + ([volume] if volume is not None else [])
    unknown = [c for c in needed if c not in df.columns]
    if unknown:
        raise ValueError(f"Columns not found in df: {unknown}. Available: {list(df.columns)}")

    for name, value in (("xaxis", xaxis), ("yaxis", yaxis), ("font", font),
                        ("dim", dim), ("title", title)):
        if value is not None and not isinstance(value, dict):
            raise ValueError(f"{name} must be dict or None, got {type(value).__name__}")
    if source is not None and not isinstance(source, (list, tuple)):
        raise ValueError(f"source must be a list of strings or None, got {type(source).__name__}")
    if xaxis and xaxis.get("range") is not None:
        _validate_axis_range(xaxis["range"], "xaxis['range']", is_date=True)
    if yaxis and yaxis.get("range") is not None:
        _validate_axis_range(yaxis["range"], "yaxis['range']")


def _prepare(df, price, position, volume, kind, xaxis, yaxis,
             show_trades=True) -> _PosData:
    """Clean inputs, derive trades and slice everything to the visible window."""
    close_col = price["close"] if isinstance(price, dict) else price
    work = df.sort_index()
    work = work[work[close_col].notna()]
    if work.empty:
        raise ValueError(f"No rows with a non-missing {close_col!r} price to plot.")

    pos = work[position].astype(float).ffill().fillna(0.0)
    if (pos.abs() > _POS_LIMIT).any():
        raise ValueError(
            f"position must lie within -100..+100, found range "
            f"[{pos.min():g}, {pos.max():g}]. Rescale it first, e.g. "
            "df['position'] / df['position'].abs().max() * 100."
        )

    # Trades and entry price use the full history so the entry price is right
    # even when the visible window starts mid-position.
    trades, avg_entry = _position_trades(work[close_col], pos)

    if xaxis and xaxis.get("range"):
        start, end = (pd.Timestamp(v) for v in xaxis["range"])
        if work.index.tz is not None:
            start = start.tz_localize(work.index.tz) if start.tzinfo is None else start
            end = end.tz_localize(work.index.tz) if end.tzinfo is None else end
        keep = (work.index >= start) & (work.index <= end)
        if not keep.any():
            raise ValueError("xaxis['range'] selects no rows of df.")
        work, pos, avg_entry = work[keep], pos[keep], avg_entry[keep]
        trades = trades[(trades.index >= start) & (trades.index <= end)]

    arr = lambda col: work[col].to_numpy(dtype=float)  # noqa: E731
    close = arr(close_col)
    if kind == "line":
        o = h = l = None
        up = np.ones(len(close), dtype=bool)
        if isinstance(price, dict) and "open" in price:
            up = close >= arr(price["open"])
        lo, hi = np.nanmin(close), np.nanmax(close)
    else:
        o, h, l = arr(price["open"]), arr(price["high"]), arr(price["low"])
        up = close >= o
        lo, hi = np.nanmin(l), np.nanmax(h)
    vol = arr(volume) if volume is not None else None

    span = (hi - lo) or abs(hi) or 1.0
    marker_offset = span * 0.035
    if show_trades and avg_entry.notna().any():
        # Keep the entry line on screen even when price has moved far from it.
        lo, hi = min(lo, avg_entry.min()), max(hi, avg_entry.max())
        span = (hi - lo) or abs(hi) or 1.0
    trades = trades.copy()
    if kind == "line" or trades.empty:
        trades["y"] = trades["price"]
    else:
        # Sit markers just outside the candle so they never cover it.
        offset = marker_offset
        low_s = pd.Series(l, index=work.index).reindex(trades.index)
        high_s = pd.Series(h, index=work.index).reindex(trades.index)
        trades["y"] = np.where(trades["change"] > 0, low_s - offset, high_s + offset)

    if yaxis and yaxis.get("range"):
        y_range = tuple(yaxis["range"])
    else:
        y_range = (lo - span * 0.07, hi + span * 0.07)

    return _PosData(
        idx=work.index, open=o, high=h, low=l, close=close, volume=vol,
        pos=pos.to_numpy(dtype=float), avg_entry=avg_entry.to_numpy(dtype=float),
        trades=trades, up=up,
        width_fracs=_candle_width_fracs(vol if kind == "vcandle" else close, kind),
        slot=_infer_slot(work.index), y_range=y_range, kind=kind,
    )


def _pane_heights(chart_h_px: float, layout: str, volume_pane: bool) -> list:
    """Return [(key, height_px, gap_above_px), ...] top to bottom."""
    panes = []
    if volume_pane:
        panes.append(("volume", max(_VOL_PANE_MIN_PX, chart_h_px * _VOL_PANE_FRAC), _PANE_GAP_PX))
    if layout == "strip":
        panes.append(("position", _STRIP_H_PX, _STRIP_GAP_PX))
    else:
        panes.append(("position", max(_POS_PANE_MIN_PX, chart_h_px * _POS_PANE_FRAC), _PANE_GAP_PX))
    used = sum(h + gap for _, h, gap in panes)
    return [("price", max(chart_h_px - used, chart_h_px * 0.3), 0)] + panes


def _pane_domains(panes: list) -> dict:
    """Convert pane heights to {key: (bottom, top)} fractions of the stack."""
    total = sum(h + gap for _, h, gap in panes)
    domains, y = {}, total
    for key, h, gap in panes:
        y -= gap
        domains[key] = (max(0.0, (y - h) / total), y / total)
        y -= h
    return domains


def _price_label(d: _PosData, yaxis) -> str:
    name = yaxis.get("name") if yaxis else None
    if d.kind == "vcandle":
        return f"{name or 'Price'} (candle width = volume)"
    return name or ("Close" if d.kind == "line" else "Price")


def _marker_px(change) -> np.ndarray:
    return _MARKER_BASE_PX + np.abs(np.asarray(change, dtype=float)) * _MARKER_PER_UNIT


def _use_weekend_breaks(d: _PosData) -> bool:
    """True for daily data with no weekend rows, where weekends can be skipped."""
    one_day = pd.Timedelta(days=1)
    return (len(d.idx) >= 6 and one_day <= d.slot < 2 * one_day
            and d.idx.dayofweek.max() < 5)


def _rgba(hex_color: str, alpha: float) -> str:
    n = int(hex_color.lstrip("#"), 16)
    return f"rgba({n >> 16 & 255},{n >> 8 & 255},{n & 255},{alpha})"


# ---------------------------------------------------------------------------
# Plotly backend
# ---------------------------------------------------------------------------

def _posplot_plotly(d: _PosData, layout, trades, volume_pane, yaxis,
                    font, dim, title, source):
    """plotly implementation: stacked panes on a shared x-axis, unified hover."""
    import plotly.graph_objects as go

    show_trades = trades
    is_strip = layout == "strip"
    legend_labels = (
        (["Buy", "Sell", "Average entry"] if show_trades else []) + ["Long", "Short"]
    )
    m = LayoutMetrics.from_params(dim, font, title, source, use_labels=True, idx=d.idx)
    label_h_px = m.font_size + 8
    legend_h_px = _estimate_legend_h_px(legend_labels, m.font_size, m.chart_w_px)
    m.legend_h_px = legend_h_px + label_h_px

    domains = _pane_domains(_pane_heights(m.chart_h_px, layout, volume_pane))
    slot_ms = d.slot / pd.Timedelta(milliseconds=1)
    x = d.idx
    fig = go.Figure()

    # --- price pane -------------------------------------------------------
    if d.kind == "line":
        fig.add_trace(go.Scatter(
            x=x, y=d.close, mode="lines", name="Close", yaxis="y",
            line=dict(color=UP_COLOR, width=2), showlegend=False,
            hovertemplate="Close: %{y:.4g}<extra></extra>",
        ))
    else:
        for is_up, color in ((True, UP_COLOR), (False, DOWN_COLOR)):
            wx, wy = [], []
            for i in np.flatnonzero(d.up == is_up):
                wx += [x[i], x[i], None]
                wy += [d.low[i], d.high[i], None]
            fig.add_trace(go.Scatter(
                x=wx, y=wy, mode="lines", yaxis="y", hoverinfo="skip",
                line=dict(color=color, width=1), showlegend=False,
            ))
        hover = ("Open %{customdata[0]:.4g} · High %{customdata[1]:.4g}<br>"
                 "Low %{customdata[2]:.4g} · Close %{customdata[3]:.4g}")
        custom = np.column_stack([d.open, d.high, d.low, d.close])
        if d.kind == "vcandle" and not volume_pane:
            hover += "<br>Volume %{customdata[4]:.3s}"
            custom = np.column_stack([custom, d.volume])
        fig.add_trace(go.Bar(
            x=x, yaxis="y", name="Price", showlegend=False,
            base=np.minimum(d.open, d.close),
            # A floor keeps open == close candles visible as a thin dash.
            y=np.maximum(np.abs(d.close - d.open), np.abs(d.close) * 0.0006),
            width=d.width_fracs * slot_ms,
            marker=dict(color=np.where(d.up, UP_COLOR, DOWN_COLOR), line=dict(width=0)),
            customdata=custom, hovertemplate=hover + "<extra></extra>",
        ))

    # --- volume pane ------------------------------------------------------
    if volume_pane:
        fig.add_trace(go.Bar(
            x=x, y=d.volume, name="Volume", yaxis="y2", showlegend=False,
            width=_CANDLE_WIDTH * slot_ms,
            marker=dict(
                color=[_rgba(UP_COLOR if u else DOWN_COLOR, 0.55) for u in d.up],
                line=dict(width=0)),
            hovertemplate="Volume: %{y:.3s}<extra></extra>",
        ))

    # --- position ---------------------------------------------------------
    pos_text = [_position_text(p) for p in d.pos]
    if is_strip:
        # Each band cell runs past its slot so weekends and holidays, which
        # carry the prior position, leave no gaps; the next cell paints over it.
        widths = np.full(len(x), 1.5 * slot_ms)
        widths[-1] = slot_ms
        fig.add_trace(go.Bar(
            x=x, y=np.ones(len(x)), offset=-slot_ms / 2, width=widths,
            name="Position", yaxis="y3", showlegend=False,
            marker=dict(
                color=d.pos, cmin=-_POS_LIMIT, cmax=_POS_LIMIT, line=dict(width=0),
                colorscale=[[0, STRIP_SHORT_COLOR], [0.5, STRIP_FLAT_COLOR],
                            [1, STRIP_LONG_COLOR]]),
            customdata=pos_text, hovertemplate="Position: %{customdata}<extra></extra>",
        ))
        for name, color in (("Long", STRIP_LONG_COLOR), ("Short", STRIP_SHORT_COLOR)):
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode="markers", name=name, yaxis="y3",
                marker=dict(symbol="square", size=11, color=color), hoverinfo="skip",
            ))
    else:
        for name, side, color in (("Long", np.maximum(d.pos, 0), POSITION_COLOR),
                                  ("Short", np.minimum(d.pos, 0), DOWN_COLOR)):
            fig.add_trace(go.Scatter(
                x=x, y=side, mode="lines", name=name, yaxis="y3", hoverinfo="skip",
                line=dict(color=color, width=0, shape="hv"),
                fill="tozeroy", fillcolor=_rgba(color, 0.5),
            ))
        fig.add_trace(go.Scatter(
            x=x, y=d.pos, mode="lines", name="Position", yaxis="y3", showlegend=False,
            line=dict(color=FT_FONT_COLOR, width=1.5, shape="hv"),
            customdata=pos_text, hovertemplate="Position: %{customdata}<extra></extra>",
        ))

    # --- trades and average entry ----------------------------------------
    if show_trades:
        for name, mask, symbol, color in (
            ("Buy", d.trades["change"] > 0, "triangle-up", POSITION_COLOR),
            ("Sell", d.trades["change"] < 0, "triangle-down", DOWN_COLOR),
        ):
            t = d.trades[mask]
            text = [f"{name} {abs(c):g}, now {_position_text(p)}"
                    for c, p in zip(t["change"], t["position"])]
            fig.add_trace(go.Scatter(
                x=t.index, y=t["y"], mode="markers", name=name, yaxis="y",
                cliponaxis=False, customdata=text,
                marker=dict(symbol=symbol, color=color, size=_marker_px(t["change"]),
                            opacity=1, line=dict(color="#FFFFFF", width=2)),
                hovertemplate="%{customdata}<extra></extra>",
            ))
        fig.add_trace(go.Scatter(
            x=x, y=d.avg_entry, mode="lines", name="Average entry", yaxis="y",
            connectgaps=False,
            line=dict(color=FT_FONT_COLOR, width=1.5, dash="dot", shape="hv"),
            hovertemplate="Average entry: %{y:.4g}<extra></extra>",
        ))

    # --- layout -----------------------------------------------------------
    tick_font = dict(family=m.font_family, size=m.font_size - 1, color=FT_FONT_COLOR)

    def y_axis(key, **extra):
        axis = dict(domain=list(domains[key]), showgrid=True, gridcolor=GRID_COLOR,
                    zeroline=False, ticksuffix="  ", tickfont=tick_font)
        axis.update(extra)
        return axis

    x_axis = dict(
        type="date", anchor="y3", showgrid=False, zeroline=False,
        range=[x[0] - d.slot, x[-1] + d.slot],
        hoverformat=_infer_hover_date_format(d.idx),
        showspikes=True, spikemode="across", spikesnap="cursor",
        spikedash="dot", spikethickness=1, spikecolor="#999999",
        rangeslider=dict(visible=False), tickfont=tick_font,
    )
    if _use_weekend_breaks(d):
        x_axis["rangebreaks"] = [dict(bounds=["sat", "mon"])]

    layout_kwargs = dict(
        template="pxts",
        hovermode="x unified", barmode="overlay",
        hoverlabel=dict(
            bgcolor="white", bordercolor="#cccccc",
            font=dict(size=m.font_size - 3, family=m.font_family, color=FT_FONT_COLOR)),
        width=int(m.total_w_px), height=int(m.total_h_px),
        margin=dict(l=m.left_margin_px, r=m.right_margin_px,
                    t=int(m.top_space_px), b=int(m.bottom_space_px)),
        font=dict(family=m.font_family, size=m.font_size - 1, color=FT_FONT_COLOR),
        xaxis=x_axis,
        yaxis=y_axis("price", range=list(d.y_range)),
        legend=dict(
            orientation="h", x=0, xanchor="left",
            y=1 + label_h_px / m.chart_h_px, yanchor="bottom",
            bgcolor="rgba(0,0,0,0)", font=tick_font, itemsizing="constant"),
    )
    if volume_pane:
        layout_kwargs["yaxis2"] = y_axis("volume", nticks=3, tickformat=".2s",
                                         rangemode="tozero")
    if is_strip:
        layout_kwargs["yaxis3"] = y_axis("position", range=[0, 1], showgrid=False,
                                         showticklabels=False, fixedrange=True)
    else:
        layout_kwargs["yaxis3"] = y_axis(
            "position", fixedrange=True,
            range=[-_POS_LIMIT - _POS_AXIS_PAD, _POS_LIMIT + _POS_AXIS_PAD],
            tickvals=[-100, 0, 100], ticktext=["−100", "0", "+100"])
        layout_kwargs["yaxis3"].update(zeroline=True, zerolinecolor="#999999",
                                       zerolinewidth=1)

    _draw_title_plotly(fig, m, layout_kwargs)
    fig.update_layout(**layout_kwargs)
    _draw_accent_line_plotly(fig, m)
    _draw_source_plotly(fig, m)

    # Pane labels sit in the gap above each pane, left-aligned to the plot.
    labels = [("price", _price_label(d, yaxis))]
    if volume_pane:
        labels.append(("volume", "Volume"))
    if not is_strip:
        labels.append(("position", "Position, −100 to +100"))
    for key, text in labels:
        fig.add_annotation(
            text=f"<b>{text}</b>", x=0, y=domains[key][1], xref="paper", yref="paper",
            xanchor="left", yanchor="bottom", yshift=4, showarrow=False,
            font=dict(family=m.font_family, size=m.font_size - 2, color=FT_FONT_COLOR),
        )
    return fig


# ---------------------------------------------------------------------------
# Matplotlib backend
# ---------------------------------------------------------------------------

def _posplot_mpl(d: _PosData, layout, trades, volume_pane, yaxis,
                 font, dim, title, source):
    """matplotlib implementation: GridSpec panes sharing the date axis."""
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.ticker import EngFormatter

    is_strip = layout == "strip"
    m = LayoutMetrics.from_params(dim, font, title, source, use_labels=True, idx=d.idx)
    font_size = m.font_size
    small = font_size - 3
    panes = _pane_heights(m.chart_h_px, layout, volume_pane)

    fig = plt.figure(figsize=(m.total_w_px / 100, (m.total_h_px + 40) / 100),
                     layout="constrained")
    grid = fig.add_gridspec(len(panes), 1, height_ratios=[h for _, h, _ in panes])
    axes, first = {}, None
    for row, (key, _, _) in enumerate(panes):
        axes[key] = fig.add_subplot(grid[row, 0], sharex=first)
        first = first or axes[key]
    ax_price, ax_pos = axes["price"], axes["position"]

    x = mdates.date2num(d.idx.to_pydatetime())
    slot_days = d.slot / pd.Timedelta(days=1)

    def style(ax, label=None):
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", length=0, labelsize=small, labelcolor=FT_FONT_COLOR)
        if label:
            ax.set_title(label, loc="left", fontsize=small, fontweight="bold",
                         color=FT_FONT_COLOR)

    # --- price pane -------------------------------------------------------
    if d.kind == "line":
        ax_price.plot(x, d.close, color=UP_COLOR, linewidth=2)
    else:
        colors = np.where(d.up, UP_COLOR, DOWN_COLOR)
        ax_price.vlines(x, d.low, d.high, colors=colors, linewidth=1, zorder=2)
        ax_price.bar(
            x, np.maximum(np.abs(d.close - d.open), np.abs(d.close) * 0.0006),
            bottom=np.minimum(d.open, d.close), width=d.width_fracs * slot_days,
            color=colors, linewidth=0, zorder=3,
        )
    ax_price.set_ylim(*d.y_range)
    style(ax_price, _price_label(d, yaxis))

    # --- volume pane ------------------------------------------------------
    if volume_pane:
        ax_vol = axes["volume"]
        ax_vol.bar(x, d.volume, width=_CANDLE_WIDTH * slot_days, linewidth=0, alpha=0.55,
                   color=np.where(d.up, UP_COLOR, DOWN_COLOR))
        ax_vol.locator_params(axis="y", nbins=3)
        ax_vol.yaxis.set_major_formatter(EngFormatter(sep=""))
        style(ax_vol, "Volume")

    # --- position ---------------------------------------------------------
    if is_strip:
        cmap = LinearSegmentedColormap.from_list(
            "pxts_position", [STRIP_SHORT_COLOR, STRIP_FLAT_COLOR, STRIP_LONG_COLOR])
        # Cell edges at each row's left boundary, so gaps in the dates are
        # filled with the position that was held across them.
        edges = np.append(x - slot_days / 2, x[-1] + slot_days / 2)
        ax_pos.pcolormesh(edges, [0, 1], d.pos[None, :], cmap=cmap,
                          vmin=-_POS_LIMIT, vmax=_POS_LIMIT, shading="flat")
        ax_pos.set_yticks([])
        style(ax_pos)
        ax_pos.grid(False)
    else:
        ax_pos.fill_between(x, d.pos, 0, where=d.pos > 0, step="post", interpolate=True,
                            color=POSITION_COLOR, alpha=0.5, linewidth=0)
        ax_pos.fill_between(x, d.pos, 0, where=d.pos < 0, step="post", interpolate=True,
                            color=DOWN_COLOR, alpha=0.5, linewidth=0)
        ax_pos.step(x, d.pos, where="post", color=FT_FONT_COLOR, linewidth=1.5)
        ax_pos.axhline(0, color="#999999", linewidth=1, zorder=1)
        ax_pos.set_ylim(-_POS_LIMIT - _POS_AXIS_PAD, _POS_LIMIT + _POS_AXIS_PAD)
        ax_pos.set_yticks([-100, 0, 100], ["−100", "0", "+100"])
        style(ax_pos, "Position, −100 to +100")

    # --- trades and average entry ----------------------------------------
    handles = []
    if trades:
        tx = mdates.date2num(d.trades.index.to_pydatetime()) if len(d.trades) else []
        for name, mask, marker, color in (
            ("Buy", d.trades["change"] > 0, "^", POSITION_COLOR),
            ("Sell", d.trades["change"] < 0, "v", DOWN_COLOR),
        ):
            t = d.trades[mask]
            if len(t):
                # scatter sizes are areas in points^2; 1 px = 0.72 pt at 100 dpi
                sizes = (_marker_px(t["change"]) * 0.72) ** 2
                ax_price.scatter(np.asarray(tx)[mask.to_numpy()], t["y"], s=sizes,
                                 marker=marker, color=color, edgecolors="white",
                                 linewidths=1, zorder=5, clip_on=False)
            handles.append(Line2D([], [], linestyle="none", marker=marker, color=color,
                                  markersize=7, label=name))
        ax_price.step(x, d.avg_entry, where="post", color=FT_FONT_COLOR,
                      linewidth=1.3, linestyle=":", zorder=4)
        handles.append(Line2D([], [], color=FT_FONT_COLOR, linewidth=1.3, linestyle=":",
                              label="Average entry"))
    long_color = STRIP_LONG_COLOR if is_strip else POSITION_COLOR
    handles += [Patch(color=long_color, alpha=1 if is_strip else 0.5, label="Long"),
                Patch(color=DOWN_COLOR, alpha=1 if is_strip else 0.5, label="Short")]
    legend_kwargs = dict(handles=handles, frameon=False, fontsize=small, handlelength=1.4,
                         ncol=len(handles), columnspacing=1.0, handletextpad=0.5)
    title_text = "\n".join(t for t in (m.title_main, m.title_sub) if t)
    try:
        # A row above the panes, like the plotly legend, with the chart title
        # as the legend title so the two stack cleanly. Needs matplotlib >= 3.7.
        fig.legend(loc="outside upper left", alignment="left",
                   title=title_text or None,
                   title_fontproperties={"weight": "bold", "size": font_size},
                   **legend_kwargs)
    except (ValueError, TypeError):
        legend_kwargs.update(ncol=1, frameon=True)
        ax_price.legend(loc="best", **legend_kwargs)
        if title_text:
            fig.suptitle(title_text, x=0.01, ha="left", fontweight="bold",
                         fontsize=font_size, color=FT_FONT_COLOR)

    # --- shared date axis -------------------------------------------------
    for key, ax in axes.items():
        if ax is not ax_pos:
            ax.tick_params(axis="x", labelbottom=False)
            ax.spines["bottom"].set_visible(False)
    ax_pos.xaxis_date()
    locator = mdates.AutoDateLocator()
    ax_pos.xaxis.set_major_locator(locator)
    ax_pos.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax_pos.set_xlim(x[0] - slot_days, x[-1] + slot_days)

    # --- source -----------------------------------------------------------
    if m.source_text:
        fig.supxlabel(m.source_text, x=0.01, ha="left", fontsize=small,
                      color=FT_FONT_COLOR)
    return fig


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def posplot(df, *,
            price="close", position="position", volume=None,
            kind="line", layout="panes", trades=True, volume_pane=False,
            xaxis=None, yaxis=None, font=None, dim=None, title=None,
            source=None, backend=None):
    """Plot an asset's price alongside the portfolio's position in it.

    Layout (top to bottom): accent line, title, subtitle, legend, price pane,
    optional volume pane, position pane or strip, source.

    Args:
        df: pandas DataFrame with a DatetimeIndex.
        price: column name of the price, or a dict
            {"open": col, "high": col, "low": col, "close": col}. The dict
            form is required for kind="candle" and kind="vcandle".
        position: column name of the position, signed, on a -100..+100 scale
            (+100 fully long, 0 flat, -100 fully short). Missing values are
            forward-filled; the position is treated as constant between rows.
        volume: column name of traded volume. Required for kind="vcandle"
            and for volume_pane=True.
        kind: how to draw the price.
            "line": close as a line.
            "candle": candlesticks of equal width.
            "vcandle": volume candles. Each candle's width scales with its
            volume, relative to the 95th-percentile volume of the plotted
            window. Time slots stay equal, so dates remain aligned with the
            position pane. Needs room: a warning is issued when there are
            fewer than about 4 pixels per candle.
        layout: how to draw the position.
            "panes": a filled step in its own pane (default chart area
            700x440). "strip": a thin colour band under the price, for
            small figures and grids of many assets (default 450x300).
        trades: if True, mark each change in position on the price (triangle
            up for a buy, down for a sell, sized by the change) and overlay
            the average entry price of the open position. The entry price
            resets when the position crosses zero or goes flat.
        volume_pane: if True, add a volume bar pane under the price.
        xaxis: dict with optional key: range ([start, end]). Restricts the
            plotted window; trades and entry price still use the full history.
        yaxis: dict with optional keys: range, name. Applies to the price pane.
        font: dict with optional keys: size, family.
        dim: dict with optional keys: width, height, aspect_ratio. Governs
            the chart area (all panes together), not the title or source.
        title: dict with optional keys: main (str), sub (str).
        source: list of source strings, e.g. ['Bloomberg'].
        backend: 'matplotlib' or 'plotly'. Defaults to get_backend().

    Returns:
        matplotlib.figure.Figure or plotly.graph_objects.Figure

    Raises:
        pxtsValidationError: if df does not have a DatetimeIndex.
        ValueError: if columns are missing, the position leaves -100..+100,
            kind/layout are unknown, or candles are requested without
            open/high/low/close (or volume, for volume candles).

    Notes:
        On plotly, weekends are removed from the axis for daily data. On
        matplotlib the date axis is continuous, so weekends show as gaps.
    """
    if title is None:
        df_name = _infer_df_name(df)
        if df_name:
            title = {"main": df_name}
    if source is None:
        source = ["Own calculations"]

    validate_ts(df)
    _validate_posplot_params(df, price, position, volume, kind, layout,
                             xaxis, yaxis, font, dim, title, source)
    if volume_pane and volume is None:
        raise ValueError("volume_pane=True needs a volume column. Pass volume='<column>'.")

    d = _prepare(df, price, position, volume, kind, xaxis, yaxis, show_trades=trades)
    dim = {**_DEFAULT_DIM[layout], **(dim or {})}

    if kind == "vcandle" and dim["width"] / max(len(d.idx), 1) < _VCANDLE_MIN_SLOT_PX:
        warnings.warn(
            f"posplot: {len(d.idx)} volume candles across {dim['width']}px leaves "
            "too little room to read candle widths. Narrow the window with "
            "xaxis={'range': [...]}, widen the chart with dim={'width': ...}, "
            "or use kind='candle'.",
            UserWarning, stacklevel=2,
        )

    if backend is None:
        backend = get_backend()
    draw = _posplot_mpl if backend == "matplotlib" else _posplot_plotly
    return draw(d, layout, trades, volume_pane, yaxis, font, dim, title, source)
