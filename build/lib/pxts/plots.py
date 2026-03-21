"""pxts plots module: time series line charts for matplotlib and plotly backends.

Public API:
    tsplot(df, ...) -> matplotlib.figure.Figure | plotly.graph_objects.Figure
    tsplot_dual(df, left, right, ...) -> matplotlib.figure.Figure | plotly.graph_objects.Figure

Both functions dispatch to backend-specific helpers based on the `backend` parameter
or the active backend returned by get_backend().
"""

import warnings

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

# Once-per-session flag for missing adjustText warning (DEP-02)
_ADJUSTTEXT_WARNED: bool = False


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
    hlines, vlines, title, subtitle, date_format, caller: str,
    ylim=None, xlim=None, ylim_lhs=None, ylim_rhs=None,
    annotations=None,
) -> None:
    """Validate parameter types for tsplot and tsplot_dual.

    hlines/vlines accept list, dict, or None (dict is used for labeled reference lines).
    Scalar int/float values are normalized upstream by _normalize_lines before reaching
    this function, so they will already be wrapped in a list when validated here.
    title, subtitle, date_format accept str or None.
    ylim, ylim_lhs, ylim_rhs: list or tuple of 2 numeric values, or None.
    xlim: list or tuple of 2 date-like values, or None.
    annotations: list of dicts with "x" and "text" keys, or None.

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
    if annotations is not None:
        if not isinstance(annotations, list):
            raise ValueError(
                f"{caller}: annotations must be list or None, got {type(annotations).__name__}"
            )
        for i, ann in enumerate(annotations):
            if not isinstance(ann, dict):
                raise ValueError(
                    f"{caller}: annotations[{i}] must be a dict, got {type(ann).__name__}"
                )
            if "x" not in ann:
                raise ValueError(
                    f"{caller}: annotations[{i}] missing required key 'x'"
                )
            if "text" not in ann:
                raise ValueError(
                    f"{caller}: annotations[{i}] missing required key 'text'"
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
# Plotly date axis — zoom-responsive tick format stops
# ---------------------------------------------------------------------------

# Plotly dtickrange values are in milliseconds.
# Each entry: [lower_bound_ms, upper_bound_ms] for when that format applies.
# None means "no bound" (open-ended).
# Tiers ordered most-zoomed-out to most-zoomed-in (Plotly requires this order).
_PLOTLY_TICKFORMATSTOPS = [
    # Decade+ view: show year only
    dict(dtickrange=[None, 1000 * 60 * 60 * 24 * 365 * 2], value="%Y"),
    # Year view: show month + year
    dict(dtickrange=[1000 * 60 * 60 * 24 * 28, 1000 * 60 * 60 * 24 * 365 * 2], value="%b %Y"),
    # Month view: show month + day
    dict(dtickrange=[1000 * 60 * 60 * 24, 1000 * 60 * 60 * 24 * 28], value="%b %d"),
    # Day/sub-day view: show day only
    dict(dtickrange=[None, 1000 * 60 * 60 * 24], value="%d"),
]


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

    Sorts texts by y-value and nudges overlapping annotations apart. Used as a
    fallback when adjustText is not installed.

    Important limitations:
    - ``min_spacing_pt`` is compared directly against y-axis **data values**, NOT
      against display/screen points. The parameter name "pt" is a misnomer inherited
      from the original design — no conversion to pixels or points is performed.
    - The spacing is an **approximation**: whether ``min_spacing_pt`` data units
      translates to visually non-overlapping labels depends on the y-axis scale and
      the figure size. Visual overlap may still occur for compressed axes or large
      datasets with closely-valued end points.
    - For accurate display-coordinate deconfliction, install adjustText
      (``pip install adjustText``), which is the preferred code path.
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
                 date_format, ylim=None, xlim=None, **kwargs):
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

    if ylim is not None:
        ax.set_ylim(ylim[0], ylim[1])
    if xlim is not None:
        ax.set_xlim(pd.Timestamp(xlim[0]), pd.Timestamp(xlim[1]))

    return fig


def _add_plotly_year_annotation(fig, df) -> None:
    """Add a small year label at the bottom-right of a Plotly figure.

    Equivalent to matplotlib ConciseDateFormatter's offset label: shows the
    current year so the viewer always has year context when viewing sub-year data.
    Uses the last index value's year. Placed at xref='paper', yref='paper',
    bottom-right corner, small font, no arrow.
    """
    if len(df) == 0:
        return
    year = df.index[-1].year
    fig.add_annotation(
        text=str(year),
        xref="paper",
        yref="paper",
        x=1.0,
        y=-0.08,
        showarrow=False,
        font=dict(size=DEFAULT_FONT_SIZE - 2),
        xanchor="right",
        yanchor="top",
    )


def _extend_yaxis_for_legend(fig, df, cols, ylim) -> None:
    """Extend y-axis upper bound to create headroom for the top-right legend.

    If any series' last value falls in the top 25% of the y-range AND ylim was
    not explicitly set by the user, extend the upper bound by 15% to push data
    away from the legend area.

    Only operates on the primary y-axis (yaxis). Does not touch secondary_y.
    Only applies when ylim is None (never overrides user-set limits).
    """
    if ylim is not None:
        return
    if not cols:
        return

    # Compute data y-range from all plotted columns
    all_vals = []
    for col in cols:
        series = df[col].dropna()
        if len(series) > 0:
            all_vals.extend([series.min(), series.max()])
    if not all_vals:
        return

    y_min = min(all_vals)
    y_max = max(all_vals)
    y_range = y_max - y_min
    if y_range == 0:
        return

    # Check if any series' last value is in the top 25% of y-range
    top_25_threshold = y_max - 0.25 * y_range
    last_vals = [df[col].dropna().iloc[-1] for col in cols if len(df[col].dropna()) > 0]
    if any(v >= top_25_threshold for v in last_vals):
        # Extend upper bound by 15% to give legend room
        new_y_max = y_max + 0.15 * y_range
        fig.update_layout(yaxis=dict(range=[y_min, new_y_max]))


def _plot_ts_plotly(df, cols, title, subtitle, labels, hlines, vlines,
                    date_format, ylim=None, xlim=None,
                    annotations=None, rangeslider=True, theme="light", **kwargs):
    """plotly implementation of plot_ts."""
    import plotly.graph_objects as go

    sorted_cols = _sorted_cols_by_last_value(df, cols)

    if date_format:
        xaxis_cfg = dict(type="date", tickformat=date_format)
    else:
        xaxis_cfg = dict(type="date", tickformatstops=_PLOTLY_TICKFORMATSTOPS)

    # Range selector buttons and rangeslider
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
    xaxis_cfg["rangeslider"] = dict(visible=rangeslider)

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

    # Apply dark theme after layout update
    if theme == "dark":
        from pxts.theme import (DARK_BACKGROUND_COLOR, DARK_PLOT_COLOR,
                                 DARK_GRID_COLOR, DARK_FONT_COLOR)
        fig.update_layout(paper_bgcolor=DARK_BACKGROUND_COLOR,
                          plot_bgcolor=DARK_PLOT_COLOR,
                          font=dict(color=DARK_FONT_COLOR))
        fig.update_xaxes(gridcolor=DARK_GRID_COLOR)
        fig.update_yaxes(gridcolor=DARK_GRID_COLOR)

    # Year annotation (ConciseDateFormatter offset equivalent): only when auto-formatting
    if not date_format:
        _add_plotly_year_annotation(fig, df)

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

    if annotations:
        _apply_plotly_annotations(fig, annotations, df, cols)

    if ylim is not None:
        fig.update_layout(yaxis=dict(range=list(ylim)))
    _extend_yaxis_for_legend(fig, df, cols, ylim)
    if xlim is not None:
        fig.update_xaxes(range=[str(pd.Timestamp(xlim[0])), str(pd.Timestamp(xlim[1]))])

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


def _apply_plotly_annotations(fig, annotations, df, cols, secondary_y_cols=None) -> None:
    """Add data-point annotations to a Plotly figure.

    Each annotation dict must have "x" and "text" keys. "y" is optional — if absent,
    y is auto-looked up from the nearest row to x in df[col]. "col" is optional for
    single-axis charts but required for dual-axis charts (secondary_y_cols provided).

    Args:
        fig: Plotly figure to annotate.
        annotations: list of dicts with keys "x", "text", optionally "y" and "col".
        df: DataFrame used for y auto-lookup (must have DatetimeIndex).
        cols: list of column names available for y lookup.
        secondary_y_cols: if not None, list of column names on secondary y-axis;
            used to set yref="y2" for those annotations.
    """
    if not annotations:
        return
    for ann in annotations:
        x_val = ann["x"]
        text = ann["text"]
        x_ts = pd.Timestamp(x_val)

        # Determine which column to use for y-lookup
        col = ann.get("col", None)
        if col is None:
            col = cols[0]  # default to first column for single-axis charts

        # y auto-lookup: find nearest row index to x_ts
        if "y" in ann:
            y_val = ann["y"]
        else:
            # Find index of nearest timestamp
            if col in df.columns:
                idx = (df.index - x_ts).to_pytimedelta()
                idx = [abs(d) for d in idx]
                nearest_pos = idx.index(min(idx))
                y_val = df[col].iloc[nearest_pos]
            else:
                y_val = 0

        # Determine yref based on whether col is on secondary axis
        if secondary_y_cols and col in secondary_y_cols:
            yref = "y2"
        else:
            yref = "y"

        fig.add_annotation(
            x=str(x_ts),
            xref="x",
            y=y_val,
            yref=yref,
            text=str(text),
            showarrow=False,
            font=dict(size=DEFAULT_FONT_SIZE - 1),
            yanchor="bottom",
            bgcolor="rgba(255,255,255,0.7)",
        )


def add_annotation(fig, x, y=None, text: str = '', col: str = None) -> None:
    """Add a single annotation to an existing Plotly figure.

    Standalone helper for post-call annotation. Useful when you want to annotate
    a figure returned by tsplot() or tsplot_dual() without rebuilding it.

    Args:
        fig: plotly.graph_objects.Figure to annotate.
        x: x-position as a date-like value (str, pd.Timestamp, datetime).
        y: y-position. If None, the annotation is placed at y=0.5 with yref="paper"
           (you should provide y for accurate positioning).
        text: annotation label text. Defaults to '' if not provided.
        col: column name hint — not used for positioning here (caller is responsible
           for passing the correct y value), but included for API symmetry with
           the annotations= dict format.

    Returns:
        None. Modifies fig in place.
    """
    x_str = str(pd.Timestamp(x))
    if y is None:
        yref = "paper"
        y_val = 0.5
    else:
        yref = "y"
        y_val = y

    fig.add_annotation(
        x=x_str,
        xref="x",
        y=y_val,
        yref=yref,
        text=str(text),
        showarrow=False,
        font=dict(size=DEFAULT_FONT_SIZE - 1),
        yanchor="bottom",
        bgcolor="rgba(255,255,255,0.7)",
    )


# ---------------------------------------------------------------------------
# matplotlib dual-axis helpers
# ---------------------------------------------------------------------------

def _plot_ts_dual_mpl(df, left, right, title, subtitle, labels, hlines, vlines,
                      date_format, ylim_lhs=None, ylim_rhs=None, xlim=None, **kwargs):
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

    if ylim_lhs is not None:
        ax1.set_ylim(ylim_lhs[0], ylim_lhs[1])
    if ylim_rhs is not None:
        ax2.set_ylim(ylim_rhs[0], ylim_rhs[1])
    if xlim is not None:
        ax1.set_xlim(pd.Timestamp(xlim[0]), pd.Timestamp(xlim[1]))

    return fig


# ---------------------------------------------------------------------------
# plotly dual-axis helpers
# ---------------------------------------------------------------------------

def _plot_ts_dual_plotly(df, left, right, title, subtitle, labels, hlines, vlines,
                         date_format, ylim_lhs=None, ylim_rhs=None, xlim=None,
                         annotations=None, rangeslider=True, theme="light",
                         left_label=None, right_label=None, **kwargs):
    """plotly implementation of plot_ts_dual."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Apply template IMMEDIATELY after make_subplots (Pitfall 4)
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

    # Set x-axis type=date (Pitfall 5: must be done via update_xaxes after traces)
    if date_format:
        fig.update_xaxes(type="date", tickformat=date_format)
    else:
        fig.update_xaxes(type="date", tickformatstops=_PLOTLY_TICKFORMATSTOPS)

    # Range selector buttons and rangeslider
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
    fig.update_xaxes(rangeselector=rangeselector_cfg,
                     rangeslider=dict(visible=rangeslider))

    if not date_format:
        _add_plotly_year_annotation(fig, df)

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

    # Apply dark theme
    if theme == "dark":
        from pxts.theme import (DARK_BACKGROUND_COLOR, DARK_PLOT_COLOR,
                                 DARK_GRID_COLOR, DARK_FONT_COLOR)
        fig.update_layout(paper_bgcolor=DARK_BACKGROUND_COLOR,
                          plot_bgcolor=DARK_PLOT_COLOR,
                          font=dict(color=DARK_FONT_COLOR))
        fig.update_xaxes(gridcolor=DARK_GRID_COLOR)
        fig.update_yaxes(gridcolor=DARK_GRID_COLOR)

    if hlines:
        _draw_hlines_plotly(fig, hlines)
    if vlines:
        _draw_vlines_plotly(fig, vlines)

    if annotations:
        _apply_plotly_annotations(fig, annotations, df, left + right,
                                   secondary_y_cols=right)

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

def tsplot(df, cols=None, title: str = "", subtitle: str = "",
           labels: bool = False, hlines=None, vlines=None,
           date_format=None, ylim=None, xlim=None,
           annotations=None, rangeslider: bool = True, theme: str = "light",
           backend=None, **kwargs):
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
        ylim: y-axis limits as [lo, hi] or (lo, hi), or None for default.
        xlim: x-axis limits as [date1, date2] (date-like), or None for default.
        annotations: list of dicts with keys "x" (date) and "text" (str).
            y auto-looked up from nearest data point. Plotly backend only; ignored on matplotlib.
        rangeslider: show rangeslider below chart. Default True. Plotly backend only.
        theme: "light" (default, white background) or "dark" (dark navy). Plotly backend only.
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
    _validate_plot_params(hlines, vlines, title, subtitle, date_format, caller="tsplot",
                          ylim=ylim, xlim=xlim, annotations=annotations)
    if cols is None:
        cols = list(df.columns)
    _validate_cols(df, cols)

    if backend is None:
        backend = get_backend()

    if backend == "matplotlib":
        return _plot_ts_mpl(df, cols, title, subtitle, labels, hlines, vlines,
                            date_format, ylim=ylim, xlim=xlim, **kwargs)
    else:
        return _plot_ts_plotly(df, cols, title, subtitle, labels, hlines, vlines,
                               date_format, ylim=ylim, xlim=xlim,
                               annotations=annotations, rangeslider=rangeslider,
                               theme=theme, **kwargs)


def tsplot_dual(df, left, right, title: str = "", subtitle: str = "",
                labels: bool = False, hlines=None, vlines=None,
                date_format=None, ylim_lhs=None, ylim_rhs=None, xlim=None,
                annotations=None, rangeslider: bool = True, theme: str = "light",
                left_label: str = None, right_label: str = None,
                backend=None, **kwargs):
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
        ylim_lhs: y-axis limits for the left (primary) axis as [lo, hi], or None.
        ylim_rhs: y-axis limits for the right (secondary) axis as [lo, hi], or None.
        xlim: x-axis limits as [date1, date2] (date-like), or None.
        annotations: list of annotation dicts. "col" key required to specify which
            y-axis drives y-lookup. Plotly backend only.
        rangeslider: show rangeslider. Default True. Plotly backend only.
        theme: "light" (default) or "dark". Plotly backend only.
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
    _validate_plot_params(hlines, vlines, title, subtitle, date_format, caller="tsplot_dual",
                          ylim=None, xlim=xlim, ylim_lhs=ylim_lhs, ylim_rhs=ylim_rhs,
                          annotations=annotations)
    _validate_cols(df, left, param_name="left")
    _validate_cols(df, right, param_name="right")

    if backend is None:
        backend = get_backend()

    if backend == "matplotlib":
        return _plot_ts_dual_mpl(df, left, right, title, subtitle, labels,
                                 hlines, vlines, date_format,
                                 ylim_lhs=ylim_lhs, ylim_rhs=ylim_rhs, xlim=xlim,
                                 **kwargs)
    else:
        return _plot_ts_dual_plotly(df, left, right, title, subtitle, labels,
                                    hlines, vlines, date_format,
                                    ylim_lhs=ylim_lhs, ylim_rhs=ylim_rhs, xlim=xlim,
                                    annotations=annotations, rangeslider=rangeslider,
                                    theme=theme, left_label=left_label,
                                    right_label=right_label, **kwargs)
