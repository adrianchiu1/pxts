"""pxts plots module: time series line charts for matplotlib and plotly backends.

Public API:
    tsplot(df, *, xaxis=None, yaxis=None, yaxis2=None, font=None,
           dim=None, titles=None, annot=None, backend=None, **kwargs)

Column selection is done via yaxis["cols"] and yaxis2["cols"].
If yaxis2 is provided, the chart becomes dual-axis.
If neither yaxis nor yaxis2 specifies cols, all df columns are plotted.
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

_RANGE_SELECTOR_BUTTONS = [
    dict(count=1, label="1M", step="month", stepmode="backward"),
    dict(count=3, label="3M", step="month", stepmode="backward"),
    dict(count=6, label="6M", step="month", stepmode="backward"),
    dict(count=1, label="YTD", step="year", stepmode="todate"),
    dict(count=1, label="1Y", step="year", stepmode="backward"),
    dict(step="all", label="All"),
]


# ---------------------------------------------------------------------------
# Column resolution
# ---------------------------------------------------------------------------

def _parse_axis_cols(axis_dict, axis_name):
    """Extract cols and display_names from an axis dict's 'cols' key.

    Returns:
        (col_list, display_names) where col_list is a list of df column names
        and display_names maps df col name -> display name.
    """
    if axis_dict is None or "cols" not in axis_dict:
        return None, {}

    raw = axis_dict["cols"]
    if isinstance(raw, dict):
        col_list = list(raw.values())
        display_names = {v: k for k, v in raw.items()}
        return col_list, display_names
    elif isinstance(raw, list):
        return raw, {}
    else:
        raise ValueError(
            f"{axis_name}['cols'] must be list or dict, got {type(raw).__name__}"
        )


def _resolve_cols(df, yaxis, yaxis2):
    """Resolve yaxis["cols"] and yaxis2["cols"] into left_cols, right_cols, display_names.

    Returns:
        (left_cols, right_cols, display_names)
        - left_cols: list of df column names for the primary y-axis.
        - right_cols: list of df column names for the secondary y-axis (empty if no yaxis2).
        - display_names: dict mapping df column name -> display name.
    """
    display_names = {}

    # Resolve right_cols from yaxis2 (type already validated by _validate_tsplot_params)
    if yaxis2 is not None:
        if "cols" not in yaxis2:
            raise ValueError("yaxis2 must contain a 'cols' key")
        right_cols, right_names = _parse_axis_cols(yaxis2, "yaxis2")
        display_names.update(right_names)
    else:
        right_cols = []

    # Resolve left_cols from yaxis
    left_cols, left_names = _parse_axis_cols(yaxis, "yaxis")
    display_names.update(left_names)

    if left_cols is None:
        if yaxis2 is not None:
            # Auto-exclude right_cols from left
            left_cols = [c for c in df.columns if c not in right_cols]
        else:
            # No cols specified anywhere — plot all
            left_cols = list(df.columns)

    # Check for overlap (skip when single-axis)
    if right_cols:
        overlap = set(left_cols) & set(right_cols)
    else:
        overlap = set()
    if overlap:
        raise ValueError(
            f"Columns {sorted(overlap)!r} appear in both yaxis['cols'] and yaxis2['cols']. "
            f"Each column must be on exactly one axis."
        )

    # Validate all cols exist in df
    all_cols = left_cols + right_cols
    bad = [c for c in all_cols if c not in df.columns]
    if bad:
        raise ValueError(
            f"Column(s) {bad!r} not in DataFrame. Available: {list(df.columns)}"
        )

    return left_cols, right_cols, display_names


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_axis_range(value, name: str, is_date: bool = False) -> None:
    """Validate a 'range' value from an axis dict."""
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
        for element in value:
            if isinstance(element, bool) or isinstance(element, (int, float)):
                raise ValueError(
                    f"{name} values must be date-like, got {type(element).__name__}"
                )
            try:
                pd.Timestamp(element)
            except Exception:
                raise ValueError(
                    f"{name} values must be date-like, got {type(element).__name__}"
                )


def _validate_annot_lines(value, name: str) -> None:
    """Validate hline/vline inside annot dict."""
    if value is None:
        return
    if not isinstance(value, (list, dict)):
        raise ValueError(
            f"annot['{name}'] must be list or dict, got {type(value).__name__}"
        )


def _validate_tsplot_params(xaxis, yaxis, yaxis2, font, dim, titles, annot) -> None:
    """Validate all dict-based parameters for tsplot."""
    # xaxis
    if xaxis is not None:
        if not isinstance(xaxis, dict):
            raise ValueError(f"xaxis must be dict or None, got {type(xaxis).__name__}")
        _validate_axis_range(xaxis.get("range"), "xaxis['range']", is_date=True)

    # yaxis
    if yaxis is not None:
        if not isinstance(yaxis, dict):
            raise ValueError(f"yaxis must be dict or None, got {type(yaxis).__name__}")
        _validate_axis_range(yaxis.get("range"), "yaxis['range']")

    # yaxis2 (cols presence validated by _resolve_cols)
    if yaxis2 is not None:
        if not isinstance(yaxis2, dict):
            raise ValueError(f"yaxis2 must be dict or None, got {type(yaxis2).__name__}")
        _validate_axis_range(yaxis2.get("range"), "yaxis2['range']")

    # font
    if font is not None:
        if not isinstance(font, dict):
            raise ValueError(f"font must be dict or None, got {type(font).__name__}")

    # dim
    if dim is not None:
        if not isinstance(dim, dict):
            raise ValueError(f"dim must be dict or None, got {type(dim).__name__}")

    # titles
    if titles is not None:
        if not isinstance(titles, dict):
            raise ValueError(f"titles must be dict or None, got {type(titles).__name__}")
        title = titles.get("title")
        if title is not None and not isinstance(title, str):
            raise ValueError(f"titles['title'] must be str or None, got {type(title).__name__}")
        subtitle = titles.get("subtitle")
        if subtitle is not None and not isinstance(subtitle, str):
            raise ValueError(f"titles['subtitle'] must be str or None, got {type(subtitle).__name__}")

    # annot
    if annot is not None:
        if not isinstance(annot, dict):
            raise ValueError(f"annot must be dict or None, got {type(annot).__name__}")
        # Normalize scalars before validation
        _validate_annot_lines(_normalize_annot_lines(annot.get("hline")), "hline")
        _validate_annot_lines(_normalize_annot_lines(annot.get("vline")), "vline")


def _normalize_annot_lines(value):
    """Normalize scalar hline/vline to list."""
    if value is None:
        return None
    if not isinstance(value, bool) and isinstance(value, (int, float)):
        return [value]
    return value


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _sorted_cols_by_last_value(df, cols) -> list:
    """Return cols sorted by their last value in df (descending)."""
    last_vals = {c: df[c].iloc[-1] for c in cols}
    return sorted(cols, key=lambda c: last_vals[c], reverse=True)


def _get_display_name(col, display_names):
    """Get display name for a column, falling back to the column name itself."""
    return display_names.get(col, col)


# ---------------------------------------------------------------------------
# Matplotlib helpers
# ---------------------------------------------------------------------------

def _draw_hlines_mpl(ax, hlines) -> None:
    """Draw horizontal lines on ax from hlines (list or dict)."""
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


def _apply_sorted_legend_mpl(ax, df, cols, display_names) -> None:
    """Sort legend handles/labels by last value descending, then set legend."""
    sorted_cols = _sorted_cols_by_last_value(df, cols)
    valid_labels = {_get_display_name(c, display_names) for c in cols}
    handles_dict = {}
    for line in ax.get_lines():
        lbl = line.get_label()
        if lbl in valid_labels:
            handles_dict[lbl] = line
    sorted_display = [_get_display_name(c, display_names) for c in sorted_cols]
    handles = [handles_dict[d] for d in sorted_display if d in handles_dict]
    labels = [d for d in sorted_display if d in handles_dict]
    if handles:
        ax.legend(handles, labels)


def _plot_ts_mpl(df, left_cols, right_cols, display_names,
                 xaxis, yaxis, yaxis2, font, dim, titles, annot, **kwargs):
    """matplotlib implementation — single or dual axis."""
    import matplotlib.pyplot as plt

    fig, ax1 = plt.subplots()

    # Apply dim
    if dim:
        w = dim.get("width", 1000)
        h = dim.get("height", 600)
        fig.set_size_inches(w / 100, h / 100)

    # Apply font
    if font:
        font_size = font.get("size", DEFAULT_FONT_SIZE)
        font_family = font.get("family", FONT_FAMILY)
        plt.rcParams.update({"font.size": font_size})

    is_dual = len(right_cols) > 0

    # Plot left series
    for col in left_cols:
        label = _get_display_name(col, display_names)
        plot_kwargs = dict(label=label, **kwargs)
        if is_dual:
            plot_kwargs["color"] = LEFT_COLOR
        ax1.plot(df.index, df[col], **plot_kwargs)

    # Plot right series on secondary axis
    ax2 = None
    if is_dual:
        ax2 = ax1.twinx()
        ax2.grid(False)
        for col in right_cols:
            label = _get_display_name(col, display_names)
            ax2.plot(df.index, df[col], label=label, color=RIGHT_COLOR, **kwargs)

        # Color axes
        ax1.spines["left"].set_edgecolor(LEFT_COLOR)
        ax1.tick_params(axis="y", labelcolor=LEFT_COLOR)
        ax2.spines["right"].set_edgecolor(RIGHT_COLOR)
        ax2.tick_params(axis="y", labelcolor=RIGHT_COLOR)

    # Legend — combined for dual axis
    if is_dual:
        all_lines = list(ax1.get_lines()) + list(ax2.get_lines())
        all_cols = left_cols + right_cols
        combined_handles = {l.get_label(): l for l in all_lines}
        last_vals = {_get_display_name(c, display_names): df[c].iloc[-1] for c in all_cols}
        sorted_labels = sorted(last_vals.keys(), key=lambda k: last_vals[k], reverse=True)
        handles = [combined_handles[lbl] for lbl in sorted_labels if lbl in combined_handles]
        ax1.legend(handles, sorted_labels)
    else:
        _apply_sorted_legend_mpl(ax1, df, left_cols, display_names)

    # Titles
    if titles:
        title = titles.get("title")
        subtitle = titles.get("subtitle")
        if title:
            fig.suptitle(title, fontsize=DEFAULT_FONT_SIZE + 1)
        if subtitle:
            ax1.set_title(subtitle, fontsize=DEFAULT_FONT_SIZE - 1)

    # Annotations
    if annot:
        hlines = _normalize_annot_lines(annot.get("hline"))
        vlines = _normalize_annot_lines(annot.get("vline"))
        if hlines:
            _draw_hlines_mpl(ax1, hlines)
        if vlines:
            _draw_vlines_mpl(ax1, vlines)

    fig.tight_layout()

    # Axis ranges (after tight_layout)
    if yaxis and yaxis.get("range"):
        r = yaxis["range"]
        ax1.set_ylim(r[0], r[1])
    if yaxis and yaxis.get("name"):
        ax1.set_ylabel(yaxis["name"])
    if yaxis2 and yaxis2.get("range") and ax2:
        r = yaxis2["range"]
        ax2.set_ylim(r[0], r[1])
    if yaxis2 and yaxis2.get("name") and ax2:
        ax2.set_ylabel(yaxis2["name"])
    if xaxis and xaxis.get("range"):
        r = xaxis["range"]
        ax1.set_xlim(pd.Timestamp(r[0]), pd.Timestamp(r[1]))
    if xaxis and xaxis.get("name"):
        ax1.set_xlabel(xaxis["name"])

    return fig


# ---------------------------------------------------------------------------
# Plotly helpers
# ---------------------------------------------------------------------------

def _draw_hlines_plotly(fig, hlines) -> None:
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
                x=1, xref="paper",
                y=y_val, yref="y",
                showarrow=False,
                font=dict(size=DEFAULT_FONT_SIZE - 2),
                xanchor="right",
            )


def _draw_vlines_plotly(fig, vlines) -> None:
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
                x=x_val, xref="x",
                y=1, yref="paper",
                showarrow=False,
                font=dict(size=DEFAULT_FONT_SIZE - 2),
                yanchor="top",
            )


def _plot_ts_plotly(df, left_cols, right_cols, display_names,
                    xaxis, yaxis, yaxis2, font, dim, titles, annot, **kwargs):
    """plotly implementation — single or dual axis."""
    import plotly.graph_objects as go

    is_dual = len(right_cols) > 0

    if is_dual:
        from plotly.subplots import make_subplots
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.update_layout(template="pxts")
    else:
        fig = go.Figure()

    # Add left traces
    sorted_left = _sorted_cols_by_last_value(df, left_cols)
    for col in sorted_left:
        name = _get_display_name(col, display_names)
        hovertemplate = f"<b>{name}</b><br>Date: %{{x}}<br>Value: %{{y:.4g}}<extra></extra>"
        trace_kwargs = dict(
            x=df.index, y=df[col], mode="lines",
            name=name, hovertemplate=hovertemplate,
        )
        if is_dual:
            trace_kwargs["line"] = dict(color=LEFT_COLOR)
            fig.add_trace(go.Scatter(**trace_kwargs), secondary_y=False)
        else:
            fig.add_trace(go.Scatter(**trace_kwargs))

    # Add right traces
    if is_dual:
        sorted_right = _sorted_cols_by_last_value(df, right_cols)
        for col in sorted_right:
            name = _get_display_name(col, display_names)
            hovertemplate = f"<b>{name}</b><br>Date: %{{x}}<br>Value: %{{y:.4g}}<extra></extra>"
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df[col], mode="lines",
                    name=name, hovertemplate=hovertemplate,
                    line=dict(color=RIGHT_COLOR),
                ),
                secondary_y=True,
            )

    # X-axis config
    xaxis_cfg = dict(type="date")
    xaxis_cfg["rangeselector"] = dict(
        buttons=_RANGE_SELECTOR_BUTTONS,
        bgcolor="rgba(255,255,255,0.8)",
        activecolor=LEFT_COLOR,
        x=0, y=1.02, xanchor="left", yanchor="bottom",
    )
    xaxis_cfg["rangeslider"] = dict(visible=False)

    # Layout
    layout_kwargs = dict(xaxis=xaxis_cfg)
    if not is_dual:
        layout_kwargs["template"] = "pxts"

    # Titles
    if titles:
        title = titles.get("title")
        subtitle = titles.get("subtitle")
        if title and subtitle:
            layout_kwargs["title_text"] = f"{title}<br><sub>{subtitle}</sub>"
        elif title:
            layout_kwargs["title_text"] = title
    fig.update_layout(**layout_kwargs)

    # Dim
    if dim:
        fig.update_layout(
            height=dim.get("height"),
            width=dim.get("width"),
        )

    # Font
    if font:
        fig.update_layout(font=font)

    # Dual axis styling
    if is_dual:
        fig.update_yaxes(tickfont=dict(color=LEFT_COLOR), secondary_y=False)
        fig.update_yaxes(tickfont=dict(color=RIGHT_COLOR), secondary_y=True)
        if yaxis2 and yaxis2.get("name"):
            fig.update_yaxes(
                title_text=yaxis2["name"],
                title_font=dict(color=RIGHT_COLOR),
                secondary_y=True,
            )
        if yaxis and yaxis.get("name"):
            fig.update_yaxes(
                title_text=yaxis["name"],
                title_font=dict(color=LEFT_COLOR),
                secondary_y=False,
            )

    # Y-axis range
    if yaxis and yaxis.get("range"):
        fig.update_layout(yaxis=dict(range=list(yaxis["range"])))
    if yaxis and yaxis.get("name") and not is_dual:
        fig.update_layout(yaxis=dict(title_text=yaxis["name"]))
    if yaxis2 and yaxis2.get("range"):
        fig.update_layout(yaxis2=dict(range=list(yaxis2["range"])))

    # X-axis range
    if xaxis and xaxis.get("range"):
        r = xaxis["range"]
        fig.update_xaxes(range=[str(pd.Timestamp(r[0])), str(pd.Timestamp(r[1]))])
    if xaxis and xaxis.get("name"):
        fig.update_xaxes(title_text=xaxis["name"])

    # Annotations
    if annot:
        hlines = _normalize_annot_lines(annot.get("hline"))
        vlines = _normalize_annot_lines(annot.get("vline"))
        if hlines:
            _draw_hlines_plotly(fig, hlines)
        if vlines:
            _draw_vlines_plotly(fig, vlines)

    return fig


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def tsplot(df, *,
           xaxis=None, yaxis=None, yaxis2=None,
           font=None, dim=None, titles=None, annot=None,
           backend=None, **kwargs):
    """Plot one or more time series columns from a DataFrame.

    Column selection is done via yaxis["cols"] and yaxis2["cols"]. If neither
    specifies cols, all df columns are plotted on a single axis. If yaxis2 is
    provided (dict with required "cols" key), the chart becomes dual-axis.

    Args:
        df: pandas DataFrame with a DatetimeIndex.
        xaxis: dict with optional keys: range, name.
        yaxis: dict with optional keys: cols, range, name.
            cols: list of column names or dict {display_name: col_name}.
            If omitted and yaxis2 is present, left axis gets all columns
            except those in yaxis2["cols"]. If omitted and no yaxis2, all
            columns are plotted.
        yaxis2: dict with required "cols" key and optional: range, name.
            Triggers dual-axis mode.
        font: dict with optional keys: size, family.
        dim: dict with optional keys: height, width (pixels).
        titles: dict with optional keys: title, subtitle.
        annot: dict with optional keys: hline, vline. Each is list or dict.
        backend: 'matplotlib' or 'plotly'. Defaults to get_backend().
        **kwargs: forwarded to the underlying plot call (e.g., linewidth, alpha).

    Returns:
        matplotlib.figure.Figure or plotly.graph_objects.Figure

    Raises:
        pxtsValidationError: if df does not have a DatetimeIndex.
        ValueError: if columns are not in df, overlap between axes, yaxis2
            missing "cols" key, or dict parameters have invalid shapes.
    """
    validate_ts(df)
    _validate_tsplot_params(xaxis, yaxis, yaxis2, font, dim, titles, annot)
    left_cols, right_cols, display_names = _resolve_cols(df, yaxis, yaxis2)

    if backend is None:
        backend = get_backend()

    if backend == "matplotlib":
        return _plot_ts_mpl(df, left_cols, right_cols, display_names,
                            xaxis, yaxis, yaxis2, font, dim, titles, annot,
                            **kwargs)
    else:
        return _plot_ts_plotly(df, left_cols, right_cols, display_names,
                               xaxis, yaxis, yaxis2, font, dim, titles, annot,
                               **kwargs)
