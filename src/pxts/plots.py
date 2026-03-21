"""pxts plots module: time series line charts for matplotlib and plotly backends.

Public API:
    tsplot(df, *, xaxis=None, yaxis=None, yaxis2=None, font=None,
           dimension=None, title=None, annotations=None, source=None,
           backend=None, **kwargs)

Column selection is done via yaxis["cols"] and yaxis2["cols"].
If yaxis2 is provided, the chart becomes dual-axis.
If neither yaxis nor yaxis2 specifies cols, all df columns are plotted.

Layout (top to bottom): accent line, title, subtitle, legend, [range selector],
chart area, source. FT-inspired styling: no spines, horizontal gridlines only.
"""

import pandas as pd

from pxts._backend import get_backend
from pxts.core import validate_ts
from pxts.theme import (
    pxts_COLORS,
    BACKGROUND_COLOR,
    GRID_COLOR,
    GRID_ALPHA,
    DEFAULT_FONT_SIZE,
    FONT_FAMILY,
    FT_FONT_COLOR,
    ACCENT_LINE_WIDTH,
    ACCENT_LINE_LENGTH,
    DEFAULT_CHART_WIDTH,
    DEFAULT_ASPECT_RATIO,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LEFT_COLOR: str = pxts_COLORS[0]   # '#0072B2' Blue
RIGHT_COLOR: str = pxts_COLORS[1]  # '#D55E00' Vermillion

_RANGE_SELECTOR_BUTTONS = [
    dict(count=1, label="1M", step="month", stepmode="backward"),
    dict(count=6, label="6M", step="month", stepmode="backward"),
    dict(count=1, label="YTD", step="year", stepmode="todate"),
    dict(count=1, label="1Y", step="year", stepmode="backward"),
    dict(count=5, label="5Y", step="year", stepmode="backward"),
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
    """Validate hline/vline inside annotations dict."""
    if value is None:
        return
    if not isinstance(value, (list, dict)):
        raise ValueError(
            f"annotations['{name}'] must be list or dict, got {type(value).__name__}"
        )


def _validate_tsplot_params(xaxis, yaxis, yaxis2, font, dimension,
                             title, annotations, source) -> None:
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

    # dimension
    if dimension is not None:
        if not isinstance(dimension, dict):
            raise ValueError(f"dimension must be dict or None, got {type(dimension).__name__}")

    # title
    if title is not None:
        if not isinstance(title, dict):
            raise ValueError(f"title must be dict or None, got {type(title).__name__}")
        main = title.get("main")
        if main is not None and not isinstance(main, str):
            raise ValueError(f"title['main'] must be str or None, got {type(main).__name__}")
        sub = title.get("sub") or title.get("subtitle")
        if sub is not None and not isinstance(sub, str):
            raise ValueError(f"title['sub'] must be str or None, got {type(sub).__name__}")

    # annotations
    if annotations is not None:
        if not isinstance(annotations, dict):
            raise ValueError(f"annotations must be dict or None, got {type(annotations).__name__}")
        # Normalize scalars before validation
        _validate_annot_lines(_normalize_annot_lines(annotations.get("hline")), "hline")
        _validate_annot_lines(_normalize_annot_lines(annotations.get("vline")), "vline")

    # source
    if source is not None:
        if not isinstance(source, list):
            raise ValueError(f"source must be list or None, got {type(source).__name__}")


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


def _resolve_dimension(dimension):
    """Extract chart width (px) and aspect ratio from dimension dict."""
    if dimension:
        w = dimension.get("width", DEFAULT_CHART_WIDTH)
        ar = dimension.get("aspect_ratio", DEFAULT_ASPECT_RATIO)
    else:
        w = DEFAULT_CHART_WIDTH
        ar = DEFAULT_ASPECT_RATIO
    return w, ar


def _resolve_font(font):
    """Extract font size and family from font dict."""
    if font:
        return font.get("size", DEFAULT_FONT_SIZE), font.get("family", FONT_FAMILY)
    return DEFAULT_FONT_SIZE, FONT_FAMILY


def _resolve_title(title):
    """Extract main and sub from title dict. Accepts 'sub' or 'subtitle' key."""
    if title:
        sub = title.get("sub") or title.get("subtitle")
        return title.get("main"), sub
    return None, None


def _resolve_source(source):
    """Build source text from list."""
    if source:
        return "Source: " + ", ".join(source)
    return None


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
        x_val = pd.Timestamp(x_val)
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


def _build_sorted_legend(ax1, ax2, df, left_cols, right_cols, display_names):
    """Build sorted legend handles and labels for single or dual axis."""
    is_dual = ax2 is not None
    if is_dual:
        all_lines = list(ax1.get_lines()) + list(ax2.get_lines())
        all_cols = left_cols + right_cols
    else:
        all_lines = list(ax1.get_lines())
        all_cols = left_cols

    combined_handles = {line.get_label(): line for line in all_lines}
    sorted_cols = _sorted_cols_by_last_value(df, all_cols)
    sorted_display = [_get_display_name(c, display_names) for c in sorted_cols]
    handles = [combined_handles[d] for d in sorted_display if d in combined_handles]
    labels = [d for d in sorted_display if d in combined_handles]
    return handles, labels


def _plot_ts_mpl(df, left_cols, right_cols, display_names,
                 xaxis, yaxis, yaxis2, font, dimension, title, annotations,
                 source, **kwargs):
    """matplotlib implementation — FT-style layout with accent line, titles, source."""
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D as MplLine2D

    # --- Resolve parameters ---
    chart_w_px, aspect_ratio = _resolve_dimension(dimension)
    chart_h_px = chart_w_px / aspect_ratio
    font_size, font_family = _resolve_font(font)
    title_main, title_sub = _resolve_title(title)
    source_text = _resolve_source(source)

    # --- Layout calculation (inches at 100 DPI) ---
    DPI = 100
    chart_w_in = chart_w_px / DPI
    chart_h_in = chart_h_px / DPI

    # Vertical spacing (inches) for elements above/below chart
    pad_top = 0.08
    accent_gap = 0.06
    title_h = 0.32 if title_main else 0
    sub_h = 0.24 if title_sub else 0
    legend_h = 0.28
    legend_gap = 0.06
    source_h = 0.24 if source_text else 0
    pad_bottom = 0.45  # room for x-axis tick labels

    top_space = pad_top + accent_gap + title_h + sub_h + legend_h + legend_gap
    bottom_space = source_h + pad_bottom

    fig_w_in = chart_w_in
    fig_h_in = chart_h_in + top_space + bottom_space

    fig = plt.figure(figsize=(fig_w_in, fig_h_in), dpi=DPI)

    # --- Position chart axes [left, bottom, width, height] in figure fraction ---
    is_dual = len(right_cols) > 0
    ax_left = 0.06
    ax_right_margin = 0.04 if not is_dual else 0.08
    ax_bottom = bottom_space / fig_h_in
    ax_height = chart_h_in / fig_h_in
    ax_width = 1 - ax_left - ax_right_margin

    ax1 = fig.add_axes([ax_left, ax_bottom, ax_width, ax_height])

    # --- Apply FT styling to axes ---
    for spine in ax1.spines.values():
        spine.set_visible(False)
    ax1.grid(True, axis="y", color=GRID_COLOR, alpha=GRID_ALPHA, linewidth=0.6)
    ax1.grid(False, axis="x")
    ax1.tick_params(axis="x", colors=FT_FONT_COLOR, labelsize=font_size - 2)
    ax1.tick_params(axis="y", colors=FT_FONT_COLOR, labelsize=font_size - 2, pad=8)
    ax1.set_axisbelow(True)

    # --- Plot left series ---
    for col in left_cols:
        label = _get_display_name(col, display_names)
        plot_kwargs = dict(label=label, **kwargs)
        if is_dual:
            plot_kwargs["color"] = LEFT_COLOR
        ax1.plot(df.index, df[col], **plot_kwargs)

    # --- Plot right series on secondary axis ---
    ax2 = None
    if is_dual:
        ax2 = ax1.twinx()
        ax2.grid(False)
        for spine in ax2.spines.values():
            spine.set_visible(False)
        ax2.tick_params(axis="y", labelcolor=RIGHT_COLOR, labelsize=font_size - 2)
        for col in right_cols:
            label = _get_display_name(col, display_names)
            ax2.plot(df.index, df[col], label=label, color=RIGHT_COLOR, **kwargs)
        ax1.tick_params(axis="y", labelcolor=LEFT_COLOR)

    # --- Legend (horizontal, left-aligned, above chart) ---
    handles, labels = _build_sorted_legend(ax1, ax2, df, left_cols, right_cols,
                                           display_names)
    if handles:
        ax1.legend(handles, labels,
                   loc="lower left", bbox_to_anchor=(0, 1.01),
                   ncol=len(labels), frameon=False,
                   fontsize=font_size - 1, handlelength=2.5)

    # --- Accent line (short bar, top-left, aligned with y-axis/title) ---
    x_left = ax_left
    accent_x_right = x_left + ACCENT_LINE_LENGTH / (fig_w_in * DPI)
    accent_y = 1 - pad_top / fig_h_in
    fig.add_artist(MplLine2D(
        [x_left, accent_x_right], [accent_y, accent_y],
        transform=fig.transFigure, color=FT_FONT_COLOR,
        linewidth=ACCENT_LINE_WIDTH, clip_on=False, solid_capstyle="butt",
    ))

    # --- Title (bold, left-aligned, font_size + 6 = 20px) ---
    text_y = accent_y - accent_gap / fig_h_in
    if title_main:
        fig.text(x_left, text_y, title_main,
                 fontsize=font_size + 6, fontweight="bold",
                 color=FT_FONT_COLOR, va="top", ha="left",
                 fontfamily=font_family)
        text_y -= title_h / fig_h_in

    # --- Subtitle (lighter, left-aligned, font_size + 2 = 16px) ---
    if title_sub:
        fig.text(x_left, text_y, title_sub,
                 fontsize=font_size + 2, color=FT_FONT_COLOR,
                 va="top", ha="left", fontfamily=font_family)

    # --- Source (bottom-left, aligned with title) ---
    if source_text:
        source_y = pad_bottom / fig_h_in
        fig.text(x_left, source_y, source_text,
                 fontsize=font_size - 1, color=FT_FONT_COLOR,
                 va="top", ha="left", fontfamily=font_family)

    # --- Annotations (hline / vline) ---
    if annotations:
        hlines = _normalize_annot_lines(annotations.get("hline"))
        vlines = _normalize_annot_lines(annotations.get("vline"))
        if hlines:
            _draw_hlines_mpl(ax1, hlines)
        if vlines:
            _draw_vlines_mpl(ax1, vlines)

    # --- Axis ranges and labels ---
    if yaxis and yaxis.get("range"):
        r = yaxis["range"]
        ax1.set_ylim(r[0], r[1])
    if yaxis and yaxis.get("name"):
        ax1.set_ylabel(yaxis["name"], color=FT_FONT_COLOR)
    if yaxis2 and yaxis2.get("range") and ax2:
        r = yaxis2["range"]
        ax2.set_ylim(r[0], r[1])
    if yaxis2 and yaxis2.get("name") and ax2:
        ax2.set_ylabel(yaxis2["name"], color=RIGHT_COLOR)
    if xaxis and xaxis.get("range"):
        r = xaxis["range"]
        ax1.set_xlim(pd.Timestamp(r[0]), pd.Timestamp(r[1]))
    if xaxis and xaxis.get("name"):
        ax1.set_xlabel(xaxis["name"], color=FT_FONT_COLOR)

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
                    xaxis, yaxis, yaxis2, font, dimension, title, annotations,
                    source, **kwargs):
    """plotly implementation — FT-style layout with accent line, titles, source."""
    import plotly.graph_objects as go

    # --- Resolve parameters ---
    chart_w_px, aspect_ratio = _resolve_dimension(dimension)
    chart_h_px = chart_w_px / aspect_ratio
    font_size, font_family = _resolve_font(font)
    title_main, title_sub = _resolve_title(title)
    source_text = _resolve_source(source)

    is_dual = len(right_cols) > 0

    # --- Create figure ---
    if is_dual:
        from plotly.subplots import make_subplots
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.update_layout(template="pxts")
    else:
        fig = go.Figure()

    # --- Add left traces ---
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

    # --- Add right traces ---
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

    # --- Layout margins (pixel-precise, top to bottom) ---
    # 3px top pad | accent line | 5px gap | title | subtitle | 5px gap | legend | range sel
    top_margin = 3                          # top edge to accent line
    top_margin += 5                         # accent line to title
    if title_main:
        top_margin += 24                    # title text height
    if title_sub:
        top_margin += 20                    # subtitle text height
    top_margin += 5                         # subtitle/title to legend
    top_margin += 22                        # legend row
    top_margin += 24                        # range selector row + gap to chart

    bottom_margin = 40
    if source_text:
        bottom_margin += 30

    left_margin = 60
    right_margin = 20 if not is_dual else 60

    total_w = chart_w_px + left_margin + right_margin
    total_h = int(chart_h_px) + top_margin + bottom_margin

    # --- X-axis config with range selector ---
    # Range selector sits just above chart (y=1.0), legend sits above that (y=1.07)
    xaxis_cfg = dict(
        type="date",
        showgrid=False,
        rangeselector=dict(
            buttons=_RANGE_SELECTOR_BUTTONS,
            bgcolor="rgba(255,255,255,0.8)",
            activecolor=LEFT_COLOR,
            x=0, y=1.0, xanchor="left", yanchor="bottom",
            font=dict(size=font_size - 1),
        ),
        rangeslider=dict(visible=False),
    )

    # --- Build layout ---
    layout_kwargs = dict(
        xaxis=xaxis_cfg,
        width=total_w,
        height=total_h,
        margin=dict(l=left_margin, r=right_margin, t=top_margin, b=bottom_margin),
        font=dict(family=font_family, size=font_size - 1, color=FT_FONT_COLOR),
        legend=dict(
            orientation="h",
            x=0, y=1.08,
            xanchor="left", yanchor="bottom",
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=font_size - 1, color=FT_FONT_COLOR),
        ),
        yaxis=dict(
            showgrid=True, gridcolor=GRID_COLOR, zeroline=False,
            ticksuffix="  ",  # small gap between y-axis labels and gridlines
        ),
    )

    if not is_dual:
        layout_kwargs["template"] = "pxts"

    # --- Title (font_size + 6 = 20px) / Subtitle (font_size + 2 = 16px) ---
    if title_main or title_sub:
        parts = []
        if title_main:
            parts.append(f"<b>{title_main}</b>")
        if title_sub:
            sub_size = font_size + 2
            parts.append(
                f"<span style='font-size:{sub_size}px; font-weight:normal'>{title_sub}</span>"
            )
        # Align title with y-axis labels (left margin area)
        title_x = left_margin * 0.1 / total_w
        # Position title 8px from top of figure (3px pad + accent + 5px gap)
        title_y = 1 - 8 / total_h
        layout_kwargs["title"] = dict(
            text="<br>".join(parts),
            x=title_x, xanchor="left",
            y=title_y, yanchor="top",
            font=dict(color=FT_FONT_COLOR, size=font_size + 6, family=font_family),
        )

    fig.update_layout(**layout_kwargs)

    # --- Font override ---
    if font:
        fig.update_layout(font=dict(
            size=font.get("size", font_size),
            family=font.get("family", font_family),
            color=FT_FONT_COLOR,
        ))

    # --- Accent line (short bar, top-left, aligned with title/y-axis labels) ---
    accent_y = 1 + (top_margin - 3) / chart_h_px
    # paper x=0 is plot area left edge; shift left into margin to align with y-labels
    accent_x0 = -(left_margin * 0.85) / chart_w_px
    accent_x1 = accent_x0 + ACCENT_LINE_LENGTH / chart_w_px
    fig.add_shape(
        type="line",
        x0=accent_x0, x1=accent_x1, y0=accent_y, y1=accent_y,
        xref="paper", yref="paper",
        line=dict(color=FT_FONT_COLOR, width=ACCENT_LINE_WIDTH),
    )

    # --- Source annotation at bottom, aligned with title/y-axis labels ---
    if source_text:
        fig.add_annotation(
            text=source_text,
            x=accent_x0, y=0,
            xref="paper", yref="paper",
            xanchor="left", yanchor="top",
            yshift=-(bottom_margin - 15),
            showarrow=False,
            font=dict(size=font_size - 1, color=FT_FONT_COLOR),
        )

    # --- Dual axis styling ---
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

    # --- Y-axis range ---
    if yaxis and yaxis.get("range"):
        fig.update_layout(yaxis=dict(range=list(yaxis["range"])))
    if yaxis and yaxis.get("name") and not is_dual:
        fig.update_layout(yaxis=dict(title_text=yaxis["name"]))
    if yaxis2 and yaxis2.get("range"):
        fig.update_layout(yaxis2=dict(range=list(yaxis2["range"])))

    # --- X-axis range ---
    if xaxis and xaxis.get("range"):
        r = xaxis["range"]
        fig.update_xaxes(range=[str(pd.Timestamp(r[0])), str(pd.Timestamp(r[1]))])
    if xaxis and xaxis.get("name"):
        fig.update_xaxes(title_text=xaxis["name"])

    # --- Annotations (hline / vline) ---
    if annotations:
        hlines = _normalize_annot_lines(annotations.get("hline"))
        vlines = _normalize_annot_lines(annotations.get("vline"))
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
           font=None, dimension=None, title=None, annotations=None,
           source=None, backend=None, **kwargs):
    """Plot one or more time series columns from a DataFrame.

    Column selection is done via yaxis["cols"] and yaxis2["cols"]. If neither
    specifies cols, all df columns are plotted on a single axis. If yaxis2 is
    provided (dict with required "cols" key), the chart becomes dual-axis.

    Layout (top to bottom): accent line, title, subtitle, legend,
    [range selector buttons — plotly only], chart area, source.

    Args:
        df: pandas DataFrame with a DatetimeIndex.
        xaxis: dict with optional keys: range, name.
        yaxis: dict with optional keys: cols, range, name.
            cols: list of column names or dict {display_name: col_name}.
        yaxis2: dict with required "cols" key and optional: range, name.
            Triggers dual-axis mode.
        font: dict with optional keys: size, family.
        dimension: dict with optional keys: width (default 1000),
            aspect_ratio (default 1.618). Governs the chart area only —
            title, legend, source are outside this dimension.
        title: dict with optional keys: main (str), sub (str).
        annotations: dict with optional keys: hline, vline. Each is list or dict.
        source: list of source strings, e.g. ['LSEG', 'Bloomberg'].
            Rendered as "Source: LSEG, Bloomberg" at the bottom.
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
    _validate_tsplot_params(xaxis, yaxis, yaxis2, font, dimension, title,
                            annotations, source)
    left_cols, right_cols, display_names = _resolve_cols(df, yaxis, yaxis2)

    if backend is None:
        backend = get_backend()

    if backend == "matplotlib":
        return _plot_ts_mpl(df, left_cols, right_cols, display_names,
                            xaxis, yaxis, yaxis2, font, dimension, title,
                            annotations, source, **kwargs)
    else:
        return _plot_ts_plotly(df, left_cols, right_cols, display_names,
                               xaxis, yaxis, yaxis2, font, dimension, title,
                               annotations, source, **kwargs)
