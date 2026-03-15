"""pxts plots module: time series line charts for matplotlib and plotly backends.

Public API:
    tsplot(df, ...) -> matplotlib.figure.Figure | plotly.graph_objects.Figure
    tsplot_dual(df, left, right, ...) -> matplotlib.figure.Figure | plotly.graph_objects.Figure

Both functions dispatch to backend-specific helpers based on the `backend` parameter
or the active backend returned by get_backend().
"""

import warnings

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

# Once-per-session flag for missing adjustText warning (DEP-02)
_ADJUSTTEXT_WARNED: bool = False


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

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


def _validate_plot_params(
    hlines, vlines, title, subtitle, date_format, caller: str
) -> None:
    """Validate parameter types for tsplot and tsplot_dual.

    hlines/vlines accept list, dict, or None (dict is used for labeled reference lines).
    title, subtitle, date_format accept str or None.

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
    if not isinstance(subtitle, (str, type(None))):
        raise ValueError(
            f"{caller}: subtitle must be str or None, got {type(subtitle).__name__}"
        )
    if not isinstance(date_format, (str, type(None))):
        raise ValueError(
            f"{caller}: date_format must be str or None, got {type(date_format).__name__}"
        )


def _detect_plotly_tickformat(df) -> str:
    """Return a d3 tickformat string based on the DatetimeIndex span.

    Thresholds:
        - span > 3 years (3*365 days): '%Y'
        - span > 180 days: '%b %Y'
        - else: '%b %d'
    """
    span_days = (df.index[-1] - df.index[0]).days
    if span_days > 3 * 365:
        return "%Y"
    elif span_days > 180:
        return "%b %Y"
    else:
        return "%b %d"


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


def _manual_deconflict(texts, min_spacing_pt: float = 12) -> None:
    """Manually deconflict text annotations by applying minimum vertical spacing.

    Sorts texts by y-value and applies at least min_spacing_pt points between them.
    Used as fallback when adjustText is not installed.
    """
    if not texts:
        return
    sorted_texts = sorted(texts, key=lambda t: t.get_position()[1])
    prev_y = None
    for text in sorted_texts:
        x, y = text.get_position()
        if prev_y is not None:
            # Ensure minimum vertical spacing (approximate — y is in data units)
            if abs(y - prev_y) < min_spacing_pt:
                y = prev_y + min_spacing_pt
                text.set_position((x, y))
        prev_y = y


def _add_mpl_end_labels(ax, df, cols, lines) -> None:
    """Add end-of-line text annotations for each series.

    Tries adjustText for deconfliction; falls back to _manual_deconflict.
    """
    texts = []
    for col, line in zip(cols, lines):
        x_last = df.index[-1]
        y_last = df[col].iloc[-1]
        ann = ax.annotate(
            col,
            xy=(x_last, y_last),
            xytext=(6, 0),
            textcoords="offset points",
            color=line.get_color(),
            fontsize=DEFAULT_FONT_SIZE - 2,
            va="center",
            annotation_clip=False,
        )
        texts.append(ann)

    try:
        from adjustText import adjust_text
        adjust_text(texts, ax=ax)
    except ImportError:
        global _ADJUSTTEXT_WARNED
        if not _ADJUSTTEXT_WARNED:
            warnings.warn(
                "pxts: adjustText is not installed — using basic label deconfliction. "
                "Install it for better label placement: pip install adjustText",
                UserWarning,
                stacklevel=2,
            )
            _ADJUSTTEXT_WARNED = True
        _manual_deconflict(texts)


def _plot_ts_mpl(df, cols, title, subtitle, labels, hlines, vlines,
                 date_format, **kwargs):
    """matplotlib implementation of plot_ts."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    fig, ax = plt.subplots()

    lines = []
    for col in cols:
        (line,) = ax.plot(df.index, df[col], label=col, **kwargs)
        lines.append(line)

    # Date axis
    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    if date_format:
        ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    else:
        formatter = mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_formatter(formatter)

    # Sorted legend
    _apply_sorted_legend_mpl(ax, df, cols)

    # Title and subtitle
    if title:
        fig.suptitle(title, fontsize=DEFAULT_FONT_SIZE + 1)
    if subtitle:
        ax.text(
            0, 1.02, subtitle,
            transform=ax.transAxes,
            fontsize=DEFAULT_FONT_SIZE - 2,
            va="bottom",
        )

    # Reference lines (BEFORE end labels — labels go LAST per Pitfall 3)
    if hlines:
        _draw_hlines_mpl(ax, hlines)
    if vlines:
        _draw_vlines_mpl(ax, vlines)

    # End labels — LAST, after legend and reference lines (Pitfall 3)
    if labels:
        _add_mpl_end_labels(ax, df, cols, lines)

    fig.tight_layout()
    return fig


def _plot_ts_plotly(df, cols, title, subtitle, labels, hlines, vlines,
                    date_format, **kwargs):
    """plotly implementation of plot_ts."""
    import plotly.graph_objects as go

    sorted_cols = _sorted_cols_by_last_value(df, cols)
    tickformat = date_format if date_format else _detect_plotly_tickformat(df)

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
        xaxis=dict(type="date", tickformat=tickformat),
    )
    if title:
        layout_kwargs["title_text"] = title
    fig.update_layout(**layout_kwargs)

    if subtitle:
        fig.add_annotation(
            text=subtitle,
            xref="paper",
            yref="paper",
            x=0,
            y=1.06,
            showarrow=False,
            font=dict(size=DEFAULT_FONT_SIZE - 2),
        )

    if hlines:
        _draw_hlines_plotly(fig, hlines)
    if vlines:
        _draw_vlines_plotly(fig, vlines)

    # labels=True on plotly: hover-only — traces already have hovertemplate set
    # No text traces added per must_haves spec

    return fig


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


# ---------------------------------------------------------------------------
# matplotlib dual-axis helpers
# ---------------------------------------------------------------------------

def _plot_ts_dual_mpl(df, left, right, title, subtitle, labels, hlines, vlines,
                      date_format, **kwargs):
    """matplotlib implementation of plot_ts_dual."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.colors as mcolors

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax2.grid(False)  # Pitfall 2: avoid double-gridlines on right axis

    # Plot left series on ax1
    left_lines = []
    for col in left:
        (line,) = ax1.plot(df.index, df[col], label=col, color=LEFT_COLOR, **kwargs)
        left_lines.append(line)

    # Plot right series on ax2 with RIGHT_COLOR
    right_lines = []
    for col in right:
        (line,) = ax2.plot(df.index, df[col], label=col, color=RIGHT_COLOR, **kwargs)
        right_lines.append(line)

    # Color left axis
    ax1.spines["left"].set_edgecolor(LEFT_COLOR)
    ax1.tick_params(axis="y", labelcolor=LEFT_COLOR)

    # Color right axis
    ax2.spines["right"].set_edgecolor(RIGHT_COLOR)
    ax2.tick_params(axis="y", labelcolor=RIGHT_COLOR)

    # Date axis on ax1
    locator = mdates.AutoDateLocator()
    ax1.xaxis.set_major_locator(locator)
    if date_format:
        ax1.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    else:
        ax1.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))

    # Combined sorted legend from both axes
    all_lines = left_lines + right_lines
    all_cols = left + right
    combined_handles = {l.get_label(): l for l in all_lines}
    last_vals = {c: df[c].iloc[-1] for c in all_cols}
    sorted_labels = sorted(all_cols, key=lambda c: last_vals[c], reverse=True)
    handles = [combined_handles[c] for c in sorted_labels if c in combined_handles]
    ax1.legend(handles, sorted_labels)

    # Title and subtitle
    if title:
        fig.suptitle(title, fontsize=DEFAULT_FONT_SIZE + 1)
    if subtitle:
        ax1.text(
            0, 1.02, subtitle,
            transform=ax1.transAxes,
            fontsize=DEFAULT_FONT_SIZE - 2,
            va="bottom",
        )

    if hlines:
        _draw_hlines_mpl(ax1, hlines)
    if vlines:
        _draw_vlines_mpl(ax1, vlines)

    if labels:
        _add_mpl_end_labels(ax1, df, left, left_lines)
        _add_mpl_end_labels(ax2, df, right, right_lines)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# plotly dual-axis helpers
# ---------------------------------------------------------------------------

def _plot_ts_dual_plotly(df, left, right, title, subtitle, labels, hlines, vlines,
                         date_format, **kwargs):
    """plotly implementation of plot_ts_dual."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Apply template IMMEDIATELY after make_subplots (Pitfall 4)
    fig.update_layout(template="pxts")

    tickformat = date_format if date_format else _detect_plotly_tickformat(df)

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

    # Set x-axis type=date (Pitfall 5: must be done via update_xaxes after traces)
    fig.update_xaxes(type="date", tickformat=tickformat)

    if title:
        fig.update_layout(title_text=title)
    if subtitle:
        fig.add_annotation(
            text=subtitle,
            xref="paper",
            yref="paper",
            x=0,
            y=1.06,
            showarrow=False,
            font=dict(size=DEFAULT_FONT_SIZE - 2),
        )

    if hlines:
        _draw_hlines_plotly(fig, hlines)
    if vlines:
        _draw_vlines_plotly(fig, vlines)

    return fig


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def tsplot(df, cols=None, title: str = "", subtitle: str = "",
           labels: bool = False, hlines=None, vlines=None,
           date_format=None, backend=None, **kwargs):
    """Plot one or more time series columns from a DataFrame as line charts.

    Args:
        df: pandas DataFrame with a DatetimeIndex.
        cols: list of column names to plot. Defaults to all columns.
        title: figure title (suptitle for matplotlib, title_text for plotly).
        subtitle: smaller subtitle below the title.
        labels: if True, annotate the end of each line with the column name.
            matplotlib: text annotations; plotly: hover only (no text traces).
        hlines: horizontal reference lines. List[float] or Dict[str, float].
        vlines: vertical reference lines. List[timestamp] or Dict[str, timestamp].
        date_format: custom date format string (overrides auto-detection).
        backend: 'matplotlib' or 'plotly'. Defaults to get_backend().
        **kwargs: forwarded to the underlying plot call (e.g., linewidth, alpha).

    Returns:
        matplotlib.figure.Figure or plotly.graph_objects.Figure

    Raises:
        pxtsValidationError: if df does not have a DatetimeIndex.
        ValueError: if any value in cols is not in df.columns.
    """
    validate_ts(df)
    _validate_plot_params(hlines, vlines, title, subtitle, date_format, caller="tsplot")
    if cols is None:
        cols = list(df.columns)
    _validate_cols(df, cols)

    if backend is None:
        backend = get_backend()

    if backend == "matplotlib":
        return _plot_ts_mpl(df, cols, title, subtitle, labels, hlines, vlines,
                            date_format, **kwargs)
    else:
        return _plot_ts_plotly(df, cols, title, subtitle, labels, hlines, vlines,
                               date_format, **kwargs)


def tsplot_dual(df, left, right, title: str = "", subtitle: str = "",
                labels: bool = False, hlines=None, vlines=None,
                date_format=None, backend=None, **kwargs):
    """Plot time series with two y-axes (left and right).

    Args:
        df: pandas DataFrame with a DatetimeIndex.
        left: list of column names to plot on the left (primary) y-axis.
        right: list of column names to plot on the right (secondary) y-axis.
        title: figure title.
        subtitle: smaller subtitle below the title.
        labels: if True, annotate the end of each line with the column name.
        hlines: horizontal reference lines. List[float] or Dict[str, float].
        vlines: vertical reference lines. List[timestamp] or Dict[str, timestamp].
        date_format: custom date format string.
        backend: 'matplotlib' or 'plotly'. Defaults to get_backend().
        **kwargs: forwarded to the underlying plot call.

    Returns:
        matplotlib.figure.Figure or plotly.graph_objects.Figure

    Raises:
        pxtsValidationError: if df does not have a DatetimeIndex.
        ValueError: if any value in left or right is not in df.columns.
    """
    validate_ts(df)
    _validate_plot_params(hlines, vlines, title, subtitle, date_format, caller="tsplot_dual")
    _validate_cols(df, left, param_name="left")
    _validate_cols(df, right, param_name="right")

    if backend is None:
        backend = get_backend()

    if backend == "matplotlib":
        return _plot_ts_dual_mpl(df, left, right, title, subtitle, labels,
                                 hlines, vlines, date_format, **kwargs)
    else:
        return _plot_ts_dual_plotly(df, left, right, title, subtitle, labels,
                                    hlines, vlines, date_format, **kwargs)
