"""pxts plots module: time series line charts for matplotlib and plotly backends.

Public API:
    tsplot(df, ...) -> matplotlib.figure.Figure | plotly.graph_objects.Figure
    tsplot_dual(df, left, right, ...) -> matplotlib.figure.Figure | plotly.graph_objects.Figure

Both functions dispatch to backend-specific helpers based on the `backend` parameter
or the active backend returned by get_backend().
"""

import pandas as pd

from pxts._backend import get_backend
from pxts.core import validate_ts
from pxts.theme import (
    pxts_COLORS,
    BACKGROUND_COLOR,
    GRID_COLOR,
    DEFAULT_FONT_SIZE,
    FONT_FAMILY,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LEFT_COLOR: str = pxts_COLORS[0]   # '#0072B2' Blue
RIGHT_COLOR: str = pxts_COLORS[1]  # '#E69F00' Orange


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _normalize_lines(value, name: str):
    """Normalize a scalar int/float hlines/vlines value to a single-element list.

    If value is an int or float (but NOT a bool, since bool is a subclass of int),
    return [value]. Otherwise return value unchanged so it is passed as-is to
    _validate_plot_params (which accepts list, dict, or None).

    Args:
        value: the raw hlines or vlines argument.
        name: parameter name, used only for context (not raised here).

    Returns:
        [value] if value is a non-bool numeric scalar, else value unchanged.
    """
    if not isinstance(value, bool) and isinstance(value, (int, float)):
        return [value]
    return value


def _validate_cols(df, cols, param_name: str = "cols") -> None:
    """Raise ValueError if any col in cols is not in df.columns.

    Args:
        df: pandas DataFrame to validate against.
        cols: sequence of column names to check.
        param_name: name of the parameter (for error message).

    Raises:
        ValueError: if any column name is not found in df.columns.
    """
    available = list(df.columns)
    bad = [c for c in cols if c not in df.columns]
    if bad:
        raise ValueError(
            f"Column(s) {bad!r} not in DataFrame. "
            f"Available: {available}"
        )


def _validate_axis_limit(value, name: str, is_date: bool = False) -> None:
    """Validate an axis limit parameter (ylim, xlim, ylim_lhs, ylim_rhs).

    Rules:
    - None: valid, no limit applied.
    - Must be list or tuple of exactly 2 elements.
    - If is_date=True, each element must be convertible via pd.Timestamp.

    Raises:
        ValueError: with the parameter name in the message.
    """
    if value is None:
        return
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"{name} must be list or tuple of 2 values, got {type(value).__name__}"
        )
    if len(value) != 2:
        raise ValueError(
            f"{name} must have exactly 2 elements, got {len(value)}"
        )
    if is_date:
        import datetime
        for element in value:
            # Reject plain int/float — pd.Timestamp accepts them as nanoseconds,
            # but they are not meaningful date-like user inputs.
            if isinstance(element, bool) or isinstance(element, (int, float)):
                raise ValueError(
                    f"{name} values must be date-like (e.g., pd.Timestamp, str date), "
                    f"got {type(element).__name__}"
                )
            try:
                pd.Timestamp(element)
            except Exception:
                raise ValueError(
                    f"{name} values must be date-like (e.g., pd.Timestamp, str date), "
                    f"got {type(element).__name__}"
                )


def _validate_plot_params(
    hlines, vlines, title, caller: str,
    ylim=None, xlim=None, ylim_lhs=None, ylim_rhs=None,
) -> None:
    """Validate parameter types for tsplot and tsplot_dual.

    hlines/vlines accept list, dict, or None (dict is used for labeled reference lines).
    Scalar int/float values are normalized upstream by _normalize_lines before reaching
    this function, so they will already be wrapped in a list when validated here.
    title accepts str or None.
    ylim, ylim_lhs, ylim_rhs: list or tuple of 2 numeric values, or None.
    xlim: list or tuple of 2 date-like values, or None.

    Raises ValueError with a clear message naming the parameter and expected type.
    """
    if not isinstance(hlines, (list, dict, type(None))):
        raise ValueError(
            f"{caller}: hlines must be list or None, got {type(hlines).__name__}"
        )
    if not isinstance(vlines, (list, dict, type(None))):
        raise ValueError(
            f"{caller}: vlines must be list or None, got {type(vlines).__name__}"
        )
    if not isinstance(title, (str, type(None))):
        raise ValueError(
            f"{caller}: title must be str or None, got {type(title).__name__}"
        )
    _validate_axis_limit(ylim, "ylim")
    _validate_axis_limit(xlim, "xlim", is_date=True)
    _validate_axis_limit(ylim_lhs, "ylim_lhs")
    _validate_axis_limit(ylim_rhs, "ylim_rhs")


def _sorted_cols_by_last_value(df, cols) -> list:
    """Return cols sorted by their last value in df (descending)."""
    last_vals = {c: df[c].iloc[-1] for c in cols}
    return sorted(cols, key=lambda c: last_vals[c], reverse=True)


# ---------------------------------------------------------------------------
# Matplotlib helpers
# ---------------------------------------------------------------------------

def _apply_sorted_legend_mpl(ax, df, cols) -> None:
    """Sort legend handles/labels by last value descending, then set legend."""
    sorted_cols = _sorted_cols_by_last_value(df, cols)
    handles_dict = {l.get_label(): l for l in ax.get_lines()
                    if l.get_label() in cols}
    handles = [handles_dict[c] for c in sorted_cols if c in handles_dict]
    labels = [c for c in sorted_cols if c in handles_dict]
    ax.legend(handles, labels)


def _draw_hlines_mpl(ax, hlines) -> None:
    """Draw horizontal lines on ax from hlines (list or dict)."""
    import matplotlib.pyplot as plt

    if isinstance(hlines, dict):
        items = hlines.items()
    else:
        items = [(None, y) for y in hlines]

    x_min, x_max = ax.get_xlim()
    label_x = x_min + 0.97 * (x_max - x_min)

    for label, y_val in items:
        line = ax.axhline(y=y_val, linestyle="--", color="gray", linewidth=1)
        if label is not None:
            ax.text(
                label_x, y_val, str(label),
                color=line.get_color(),
                fontsize=DEFAULT_FONT_SIZE - 2,
                va="bottom",
                ha="right",
            )


def _draw_vlines_mpl(ax, vlines) -> None:
    """Draw vertical lines on ax from vlines (list or dict)."""
    if isinstance(vlines, dict):
        items = vlines.items()
    else:
        items = [(None, x) for x in vlines]

    y_min, y_max = ax.get_ylim()
    label_y = y_min + 0.97 * (y_max - y_min)

    for label, x_val in items:
        line = ax.axvline(x=x_val, linestyle=":", color="gray", linewidth=1)
        if label is not None:
            ax.text(
                x_val, label_y, str(label),
                color=line.get_color(),
                fontsize=DEFAULT_FONT_SIZE - 2,
                va="top",
                ha="center",
                rotation=90,
            )


def _plot_ts_mpl(df, cols, title, hlines, vlines,
                 ylim=None, xlim=None, **kwargs):
    """matplotlib implementation of plot_ts."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    fig, ax = plt.subplots()

    for col in cols:
        ax.plot(df.index, df[col], label=col, **kwargs)

    # Sorted legend
    _apply_sorted_legend_mpl(ax, df, cols)

    # Title
    if title:
        fig.suptitle(title, fontsize=DEFAULT_FONT_SIZE + 1)

    # Reference lines
    if hlines:
        _draw_hlines_mpl(ax, hlines)
    if vlines:
        _draw_vlines_mpl(ax, vlines)

    fig.tight_layout()

    if ylim is not None:
        ax.set_ylim(ylim[0], ylim[1])
    if xlim is not None:
        ax.set_xlim(pd.Timestamp(xlim[0]), pd.Timestamp(xlim[1]))

    return fig


def _plot_ts_dual_mpl(df, left, right, title, hlines, vlines,
                      ylim_lhs=None, ylim_rhs=None, xlim=None, **kwargs):
    """matplotlib implementation of plot_ts_dual."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax2.grid(False)  # Avoid double-gridlines on right axis

    # Plot left series on ax1
    for col in left:
        ax1.plot(df.index, df[col], label=col, color=LEFT_COLOR, **kwargs)

    # Plot right series on ax2
    for col in right:
        ax2.plot(df.index, df[col], label=col, color=RIGHT_COLOR, **kwargs)

    # Color left axis
    ax1.spines["left"].set_edgecolor(LEFT_COLOR)
    ax1.tick_params(axis="y", labelcolor=LEFT_COLOR)

    # Color right axis
    ax2.spines["right"].set_edgecolor(RIGHT_COLOR)
    ax2.tick_params(axis="y", labelcolor=RIGHT_COLOR)

    # Combined sorted legend from both axes
    all_lines = list(ax1.get_lines()) + list(ax2.get_lines())
    all_cols = left + right
    combined_handles = {l.get_label(): l for l in all_lines}
    last_vals = {c: df[c].iloc[-1] for c in all_cols}
    sorted_labels = sorted(all_cols, key=lambda c: last_vals[c], reverse=True)
    handles = [combined_handles[c] for c in sorted_labels if c in combined_handles]
    ax1.legend(handles, sorted_labels)

    # Title
    if title:
        fig.suptitle(title, fontsize=DEFAULT_FONT_SIZE + 1)

    if hlines:
        _draw_hlines_mpl(ax1, hlines)
    if vlines:
        _draw_vlines_mpl(ax1, vlines)

    fig.tight_layout()

    if ylim_lhs is not None:
        ax1.set_ylim(ylim_lhs[0], ylim_lhs[1])
    if ylim_rhs is not None:
        ax2.set_ylim(ylim_rhs[0], ylim_rhs[1])
    if xlim is not None:
        ax1.set_xlim(pd.Timestamp(xlim[0]), pd.Timestamp(xlim[1]))

    return fig


# ---------------------------------------------------------------------------
# Plotly helpers
# ---------------------------------------------------------------------------

def _draw_hlines_plotly(fig, hlines, secondary_y: bool = False) -> None:
    """Add horizontal reference lines to a plotly figure."""
    if isinstance(hlines, dict):
        items = hlines.items()
    else:
        items = [(None, y) for y in hlines]

    for label, y_val in items:
        fig.add_hline(y=y_val, line_dash="dash", line_color="gray", line_width=1)
        if label is not None:
            fig.add_annotation(
                text=str(label),
                x=1,
                xref="paper",
                y=y_val,
                yref="y",
                showarrow=False,
                font=dict(size=DEFAULT_FONT_SIZE - 2),
                xanchor="right",
            )


def _draw_vlines_plotly(fig, vlines, secondary_y: bool = False) -> None:
    """Add vertical reference lines to a plotly figure."""
    if isinstance(vlines, dict):
        items = vlines.items()
    else:
        items = [(None, x) for x in vlines]

    for label, x_val in items:
        fig.add_vline(x=x_val, line_dash="dot", line_color="gray", line_width=1)
        if label is not None:
            fig.add_annotation(
                text=str(label),
                x=x_val,
                xref="x",
                y=1,
                yref="paper",
                showarrow=False,
                font=dict(size=DEFAULT_FONT_SIZE - 2),
                yanchor="top",
            )


def _plot_ts_plotly(df, cols, title, hlines, vlines,
                    ylim=None, xlim=None, **kwargs):
    """plotly implementation of plot_ts."""
    import plotly.graph_objects as go

    sorted_cols = _sorted_cols_by_last_value(df, cols)

    xaxis_cfg = dict(type="date")

    # Range selector buttons (rangeslider always hidden)
    xaxis_cfg["rangeselector"] = dict(
        buttons=list([
            dict(count=1,  label="1M",  step="month", stepmode="backward"),
            dict(count=3,  label="3M",  step="month", stepmode="backward"),
            dict(count=6,  label="6M",  step="month", stepmode="backward"),
            dict(count=1,  label="YTD", step="year",  stepmode="todate"),
            dict(count=1,  label="1Y",  step="year",  stepmode="backward"),
            dict(step="all", label="All"),
        ]),
        bgcolor="rgba(255,255,255,0.8)",
        activecolor="#0072B2",
        x=0, y=1.02, xanchor="left", yanchor="bottom",
    )
    xaxis_cfg["rangeslider"] = dict(visible=False)

    fig = go.Figure()

    for col in sorted_cols:
        hovertemplate = f"<b>{col}</b><br>Date: %{{x}}<br>Value: %{{y:.4g}}<extra></extra>"
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[col],
            mode="lines",
            name=col,
            hovertemplate=hovertemplate,
        ))

    layout_kwargs = dict(
        template="pxts",
        xaxis=xaxis_cfg,
    )
    if title:
        layout_kwargs["title_text"] = title
    fig.update_layout(**layout_kwargs)

    if hlines:
        _draw_hlines_plotly(fig, hlines)
    if vlines:
        _draw_vlines_plotly(fig, vlines)

    if ylim is not None:
        fig.update_layout(yaxis=dict(range=list(ylim)))
    if xlim is not None:
        fig.update_xaxes(range=[str(pd.Timestamp(xlim[0])), str(pd.Timestamp(xlim[1]))])

    return fig


# ---------------------------------------------------------------------------
# plotly dual-axis helpers
# ---------------------------------------------------------------------------

def _plot_ts_dual_plotly(df, left, right, title, hlines, vlines,
                         ylim_lhs=None, ylim_rhs=None, xlim=None,
                         left_label=None, right_label=None, **kwargs):
    """plotly implementation of plot_ts_dual."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Apply template IMMEDIATELY after make_subplots
    fig.update_layout(template="pxts")

    for col in left:
        hovertemplate = f"<b>{col}</b><br>Date: %{{x}}<br>Value: %{{y:.4g}}<extra></extra>"
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[col],
                mode="lines",
                name=col,
                hovertemplate=hovertemplate,
                line=dict(color=LEFT_COLOR),
            ),
            secondary_y=False,
        )

    for col in right:
        hovertemplate = f"<b>{col}</b><br>Date: %{{x}}<br>Value: %{{y:.4g}}<extra></extra>"
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[col],
                mode="lines",
                name=col,
                hovertemplate=hovertemplate,
                line=dict(color=RIGHT_COLOR),
            ),
            secondary_y=True,
        )

    # Color axis labels and ticks
    fig.update_yaxes(tickfont=dict(color=LEFT_COLOR), secondary_y=False)
    fig.update_yaxes(tickfont=dict(color=RIGHT_COLOR), secondary_y=True)

    # Colored axis title text
    if left_label:
        fig.update_yaxes(title_text=left_label,
                         title_font=dict(color=LEFT_COLOR),
                         secondary_y=False)
    if right_label:
        fig.update_yaxes(title_text=right_label,
                         title_font=dict(color=RIGHT_COLOR),
                         secondary_y=True)

    # Set x-axis type=date
    fig.update_xaxes(type="date")

    # Range selector buttons (rangeslider always hidden)
    rangeselector_cfg = dict(
        buttons=list([
            dict(count=1,  label="1M",  step="month", stepmode="backward"),
            dict(count=3,  label="3M",  step="month", stepmode="backward"),
            dict(count=6,  label="6M",  step="month", stepmode="backward"),
            dict(count=1,  label="YTD", step="year",  stepmode="todate"),
            dict(count=1,  label="1Y",  step="year",  stepmode="backward"),
            dict(step="all", label="All"),
        ]),
        bgcolor="rgba(255,255,255,0.8)",
        activecolor="#0072B2",
        x=0, y=1.02, xanchor="left", yanchor="bottom",
    )
    fig.update_xaxes(rangeselector=rangeselector_cfg, rangeslider=dict(visible=False))

    if title:
        fig.update_layout(title_text=title)

    if hlines:
        _draw_hlines_plotly(fig, hlines)
    if vlines:
        _draw_vlines_plotly(fig, vlines)

    if ylim_lhs is not None:
        fig.update_layout(yaxis=dict(range=list(ylim_lhs)))
    if ylim_rhs is not None:
        fig.update_layout(yaxis2=dict(range=list(ylim_rhs)))
    if xlim is not None:
        fig.update_xaxes(range=[str(pd.Timestamp(xlim[0])), str(pd.Timestamp(xlim[1]))])

    return fig


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def tsplot(df, cols=None, title: str = "",
           hlines=None, vlines=None,
           ylim=None, xlim=None,
           backend=None, **kwargs):
    """Plot one or more time series columns from a DataFrame as line charts.

    Args:
        df: pandas DataFrame with a DatetimeIndex.
        cols: list of column names to plot. Defaults to all columns.
        title: figure title (suptitle for matplotlib, title_text for plotly).
        hlines: horizontal reference lines. List[float] or Dict[str, float].
        vlines: vertical reference lines. List[timestamp] or Dict[str, timestamp].
        ylim: y-axis limits as [lo, hi] or (lo, hi), or None for default.
        xlim: x-axis limits as [date1, date2] (date-like), or None for default.
        backend: 'matplotlib' or 'plotly'. Defaults to get_backend().
        **kwargs: forwarded to the underlying plot call (e.g., linewidth, alpha).

    Returns:
        matplotlib.figure.Figure or plotly.graph_objects.Figure

    Raises:
        pxtsValidationError: if df does not have a DatetimeIndex.
        ValueError: if any value in cols is not in df.columns, or if axis
            limit parameters have invalid types/lengths.
    """
    validate_ts(df)
    hlines = _normalize_lines(hlines, "hlines")
    vlines = _normalize_lines(vlines, "vlines")
    _validate_plot_params(hlines, vlines, title, caller="tsplot",
                          ylim=ylim, xlim=xlim)
    if cols is None:
        cols = list(df.columns)
    _validate_cols(df, cols)

    if backend is None:
        backend = get_backend()

    if backend == "matplotlib":
        return _plot_ts_mpl(df, cols, title, hlines, vlines,
                            ylim=ylim, xlim=xlim, **kwargs)
    else:
        return _plot_ts_plotly(df, cols, title, hlines, vlines,
                               ylim=ylim, xlim=xlim, **kwargs)


def tsplot_dual(df, left, right, title: str = "",
                hlines=None, vlines=None,
                ylim_lhs=None, ylim_rhs=None, xlim=None,
                left_label: str = None, right_label: str = None,
                backend=None, **kwargs):
    """Plot time series with two y-axes (left and right).

    Args:
        df: pandas DataFrame with a DatetimeIndex.
        left: list of column names to plot on the left (primary) y-axis.
        right: list of column names to plot on the right (secondary) y-axis.
        title: figure title.
        hlines: horizontal reference lines. List[float] or Dict[str, float].
        vlines: vertical reference lines. List[timestamp] or Dict[str, timestamp].
        ylim_lhs: y-axis limits for the left (primary) axis as [lo, hi], or None.
        ylim_rhs: y-axis limits for the right (secondary) axis as [lo, hi], or None.
        xlim: x-axis limits as [date1, date2] (date-like), or None.
        left_label: axis title text for the left (primary) y-axis, colored LEFT_COLOR.
            None (default) means no axis title.
        right_label: axis title text for the right (secondary) y-axis, colored RIGHT_COLOR.
            None (default) means no axis title.
        backend: 'matplotlib' or 'plotly'. Defaults to get_backend().
        **kwargs: forwarded to the underlying plot call.

    Returns:
        matplotlib.figure.Figure or plotly.graph_objects.Figure

    Raises:
        pxtsValidationError: if df does not have a DatetimeIndex.
        ValueError: if any value in left or right is not in df.columns, or if
            axis limit parameters have invalid types/lengths.
    """
    validate_ts(df)
    hlines = _normalize_lines(hlines, "hlines")
    vlines = _normalize_lines(vlines, "vlines")
    _validate_plot_params(hlines, vlines, title, caller="tsplot_dual",
                          xlim=xlim, ylim_lhs=ylim_lhs, ylim_rhs=ylim_rhs)
    _validate_cols(df, left, param_name="left")
    _validate_cols(df, right, param_name="right")

    if backend is None:
        backend = get_backend()

    if backend == "matplotlib":
        return _plot_ts_dual_mpl(df, left, right, title,
                                 hlines, vlines,
                                 ylim_lhs=ylim_lhs, ylim_rhs=ylim_rhs, xlim=xlim,
                                 **kwargs)
    else:
        return _plot_ts_dual_plotly(df, left, right, title,
                                    hlines, vlines,
                                    ylim_lhs=ylim_lhs, ylim_rhs=ylim_rhs, xlim=xlim,
                                    left_label=left_label, right_label=right_label,
                                    **kwargs)
