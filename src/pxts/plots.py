"""pxts plots module: time series line charts for matplotlib and plotly backends.

Public API:
    tsplot(df, *, xaxis=None, yaxis=None, yaxis2=None, font=None,
           dimension=None, title=None, annotations=None, source=None,
           labels=False, backend=None, **kwargs)

    tsgrid(panels, *, nrow=1, ncol=1, xaxis=None, yaxis=None, font=None,
           dimension=None, title=None, annotations=None, source=None,
           labels=False, backend=None, **kwargs)

When labels=True, the legend is replaced with FT-style end-of-line labels:
series names are placed to the right of each line's last data point,
colored to match. Ignored in dual-axis mode (falls back to legend with a warning).

Column selection is done via yaxis["cols"] and yaxis2["cols"].
If yaxis2 is provided, the chart becomes dual-axis.
If neither yaxis nor yaxis2 specifies cols, all df columns are plotted.

Layout (top to bottom): accent line, title, subtitle, legend,
chart area, source. FT-inspired styling: no spines, horizontal gridlines only.
"""

import inspect
import warnings
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from pxts._backend import get_backend
from pxts.core import validate_ts
from pxts.theme import (
    pxts_COLORS,
    BACKGROUND_COLOR,
    GRID_COLOR,
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


def _infer_hover_date_format(idx: pd.DatetimeIndex) -> str:
    """Return a d3-time-format string appropriate for the data's periodicity.

    Uses the minimum observed timedelta to decide how much precision to show.
    Falls back to '%Y-%m-%d' if the index has fewer than 2 points.
    """
    if len(idx) < 2:
        return "%Y-%m-%d"
    diffs = idx.to_series().diff().dropna()
    min_diff = diffs.min()
    seconds = min_diff.total_seconds()
    if seconds < 60:                       # sub-minute
        return "%Y-%m-%d %H:%M:%S"
    if seconds < 3600:                     # sub-hour (minute-level)
        return "%Y-%m-%d %H:%M"
    if seconds < 86400:                    # sub-day (hourly)
        return "%Y-%m-%d %H:%M"
    if seconds < 28 * 86400:              # daily / weekly
        return "%Y-%m-%d"
    if seconds < 90 * 86400:             # monthly
        return "%b %Y"
    if seconds < 366 * 86400:            # quarterly
        return "%b %Y"
    return "%Y"                           # annual or coarser


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
            left_cols = [c for c in df.columns if c not in right_cols]
        else:
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
    if xaxis is not None:
        if not isinstance(xaxis, dict):
            raise ValueError(f"xaxis must be dict or None, got {type(xaxis).__name__}")
        _validate_axis_range(xaxis.get("range"), "xaxis['range']", is_date=True)

    if yaxis is not None:
        if not isinstance(yaxis, dict):
            raise ValueError(f"yaxis must be dict or None, got {type(yaxis).__name__}")
        _validate_axis_range(yaxis.get("range"), "yaxis['range']")

    if yaxis2 is not None:
        if not isinstance(yaxis2, dict):
            raise ValueError(f"yaxis2 must be dict or None, got {type(yaxis2).__name__}")
        _validate_axis_range(yaxis2.get("range"), "yaxis2['range']")

    if font is not None:
        if not isinstance(font, dict):
            raise ValueError(f"font must be dict or None, got {type(font).__name__}")

    if dimension is not None:
        if not isinstance(dimension, dict):
            raise ValueError(f"dimension must be dict or None, got {type(dimension).__name__}")

    if title is not None:
        if not isinstance(title, dict):
            raise ValueError(f"title must be dict or None, got {type(title).__name__}")
        main = title.get("main")
        if main is not None and not isinstance(main, str):
            raise ValueError(f"title['main'] must be str or None, got {type(main).__name__}")
        sub = title.get("sub") or title.get("subtitle")
        if sub is not None and not isinstance(sub, str):
            raise ValueError(f"title['sub'] must be str or None, got {type(sub).__name__}")

    if annotations is not None:
        if not isinstance(annotations, dict):
            raise ValueError(f"annotations must be dict or None, got {type(annotations).__name__}")
        _validate_annot_lines(_normalize_annot_lines(annotations.get("hline")), "hline")
        _validate_annot_lines(_normalize_annot_lines(annotations.get("vline")), "vline")

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
# Layout metrics — shared spacing for all plot types
# ---------------------------------------------------------------------------

@dataclass
class LayoutMetrics:
    """Resolved layout dimensions shared across all chart types and backends.

    All pixel values assume 100 DPI for matplotlib (1 px = 0.01 inches).
    Plotly uses pixel values directly.

    The vertical layout (top to bottom) is:
        pad_top_px | accent line | accent_gap_px | title | subtitle |
        legend_gap_px | legend | chart area | source | pad_bottom_px
    """
    # Resolved chart parameters
    chart_w_px: float
    chart_h_px: float
    font_size: int
    font_family: str
    title_main: Optional[str]
    title_sub: Optional[str]
    source_text: Optional[str]

    # Vertical spacing (pixels at 100 DPI)
    pad_top_px: float = 8
    accent_gap_px: float = 6
    title_h_px: float = 0       # 0 when no title
    sub_h_px: float = 0         # 0 when no subtitle
    legend_h_px: float = 28
    legend_gap_px: float = 6
    source_h_px: float = 0      # 0 when no source
    pad_bottom_px: float = 45   # room for x-axis tick labels

    # Horizontal margins (pixels)
    left_margin_px: int = 60
    right_margin_px: int = 20

    @classmethod
    def from_params(cls, dimension, font, title, source, *, is_dual: bool = False,
                    labels_margin_px: int = 0, use_labels: bool = False):
        """Build LayoutMetrics from user-facing parameter dicts."""
        if dimension:
            w = dimension.get("width", DEFAULT_CHART_WIDTH)
            ar = dimension.get("aspect_ratio", DEFAULT_ASPECT_RATIO)
        else:
            w = DEFAULT_CHART_WIDTH
            ar = DEFAULT_ASPECT_RATIO

        if font:
            font_size = font.get("size", DEFAULT_FONT_SIZE)
            font_family = font.get("family", FONT_FAMILY)
        else:
            font_size = DEFAULT_FONT_SIZE
            font_family = FONT_FAMILY

        if title:
            title_sub = title.get("sub") or title.get("subtitle")
            title_main = title.get("main")
        else:
            title_main = None
            title_sub = None

        source_text = ("Source: " + ", ".join(source)) if source else None

        if labels_margin_px > 0:
            right_margin = labels_margin_px
        elif is_dual:
            right_margin = 60
        else:
            right_margin = 20

        return cls(
            chart_w_px=w,
            chart_h_px=w / ar,
            font_size=font_size,
            font_family=font_family,
            title_main=title_main,
            title_sub=title_sub,
            source_text=source_text,
            title_h_px=32 if title_main else 0,
            sub_h_px=24 if title_sub else 0,
            source_h_px=24 if source_text else 0,
            right_margin_px=right_margin,
            legend_h_px=0 if use_labels else 28,
            legend_gap_px=0 if use_labels else 6,
        )

    @property
    def top_space_px(self) -> float:
        return (self.pad_top_px + self.accent_gap_px + self.title_h_px
                + self.sub_h_px + self.legend_h_px + self.legend_gap_px)

    @property
    def bottom_space_px(self) -> float:
        return self.source_h_px + self.pad_bottom_px

    @property
    def total_w_px(self) -> float:
        return self.chart_w_px + self.left_margin_px + self.right_margin_px

    @property
    def total_h_px(self) -> float:
        return self.chart_h_px + self.top_space_px + self.bottom_space_px

    @property
    def left_align_x_plotly(self) -> float:
        """X coordinate in plotly paper space that aligns with y-axis labels."""
        return -(self.left_margin_px * 0.85) / self.chart_w_px


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _infer_df_name(df) -> Optional[str]:
    """Try to find the variable name of df in the caller's caller's frame."""
    try:
        frame = inspect.currentframe()
        # Walk up: _infer_df_name -> tsplot -> user code
        caller = frame.f_back.f_back
        for name, val in caller.f_locals.items():
            if val is df:
                return name
    except Exception:
        pass
    finally:
        del frame
    return None


def _sorted_cols_by_last_value(df, cols) -> list:
    """Return cols sorted by their last value in df (descending)."""
    last_vals = {c: df[c].iloc[-1] for c in cols}
    return sorted(cols, key=lambda c: last_vals[c], reverse=True)


def _get_display_name(col, display_names):
    """Get display name for a column, falling back to the column name itself."""
    return display_names.get(col, col)


def _nudge_label_positions(y_positions, min_gap):
    """Nudge y-positions apart so no two labels overlap.

    Uses iterative repulsion: sort by y, then push apart any pair that is
    closer than min_gap. Repeats until stable (max 50 iterations).

    Args:
        y_positions: list of (index, y_value) tuples.
        min_gap: minimum vertical distance between label centres.

    Returns:
        dict mapping original index -> nudged y value.
    """
    items = sorted(y_positions, key=lambda t: t[1])

    for _ in range(50):
        moved = False
        for i in range(1, len(items)):
            idx_a, ya = items[i - 1]
            idx_b, yb = items[i]
            gap = yb - ya
            if gap < min_gap:
                shift = (min_gap - gap) / 2
                items[i - 1] = (idx_a, ya - shift)
                items[i] = (idx_b, yb + shift)
                moved = True
        if not moved:
            break

    return {idx: y for idx, y in items}


def _estimate_label_width_px(labels, font_size):
    """Estimate the pixel width of the longest label string.

    Uses a rough heuristic of 0.6 * font_size per character, plus a small pad.
    """
    if not labels:
        return 0
    max_chars = max(len(lbl) for lbl in labels)
    return int(max_chars * font_size * 0.6) + 10


# ---------------------------------------------------------------------------
# Chrome drawing — matplotlib
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Chrome drawing — plotly
# ---------------------------------------------------------------------------

def _draw_accent_line_plotly(fig, m: LayoutMetrics) -> None:
    """Draw the FT-style accent line at the top of a plotly figure."""
    accent_y = 1 + (m.top_space_px - 12) / m.chart_h_px
    accent_x0 = m.left_align_x_plotly
    accent_x1 = accent_x0 + ACCENT_LINE_LENGTH / m.chart_w_px
    fig.add_shape(
        type="line",
        x0=accent_x0, x1=accent_x1, y0=accent_y, y1=accent_y,
        xref="paper", yref="paper",
        line=dict(color=FT_FONT_COLOR, width=ACCENT_LINE_WIDTH),
    )


def _draw_title_plotly(fig, m: LayoutMetrics, layout_kwargs: dict) -> None:
    """Add title/subtitle to plotly layout kwargs."""
    if not m.title_main and not m.title_sub:
        return

    parts = []
    if m.title_main:
        parts.append(f"<b>{m.title_main}</b>")
    if m.title_sub:
        sub_size = m.font_size + 2
        parts.append(
            f"<span style='font-size:{sub_size}px; font-weight:normal'>{m.title_sub}</span>"
        )

    # Align title with y-axis labels (left margin area)
    title_x = m.left_margin_px * 0.1 / m.total_w_px
    # 3px pad + accent + gap = ~40px from top
    title_y = 1 - 40 / m.total_h_px

    layout_kwargs["title"] = dict(
        text="<br>".join(parts),
        x=title_x, xanchor="left",
        y=title_y, yanchor="top",
        font=dict(color=FT_FONT_COLOR, size=m.font_size + 6, family=m.font_family),
    )


def _draw_source_plotly(fig, m: LayoutMetrics) -> None:
    """Draw source attribution at the bottom of a plotly figure."""
    if not m.source_text:
        return
    fig.add_annotation(
        text=m.source_text,
        x=m.left_align_x_plotly, y=0,
        xref="paper", yref="paper",
        xanchor="left", yanchor="top",
        yshift=-(m.bottom_space_px - m.pad_bottom_px),
        showarrow=False,
        font=dict(size=m.font_size - 1, color=FT_FONT_COLOR),
    )


# ---------------------------------------------------------------------------
# Annotation helpers — matplotlib
# ---------------------------------------------------------------------------

def _draw_hlines_mpl(ax, hlines) -> None:
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


def _draw_line_labels_mpl(ax, df, cols, display_names, font_size):
    """Draw FT-style end-of-line labels for matplotlib.

    Places each series name to the right of the chart at the y-coordinate of
    its last data point, with collision avoidance via _nudge_label_positions.
    """
    lines = ax.get_lines()
    label_to_line = {line.get_label(): line for line in lines}

    # Collect last y-values and display names, paired with colour
    entries = []  # (col, display_name, last_y, color)
    for col in cols:
        dname = _get_display_name(col, display_names)
        last_y = df[col].dropna().iloc[-1] if not df[col].dropna().empty else None
        if last_y is None:
            continue
        color = label_to_line[dname].get_color() if dname in label_to_line else None
        entries.append((dname, last_y, color))

    if not entries:
        return

    # Nudge positions — min_gap based on font size relative to data range
    y_min, y_max = ax.get_ylim()
    data_range = y_max - y_min
    # Approximate: font_size in points → fraction of data range
    # A line of text ~1.4em high; axes typically ~400px → scale accordingly
    ax_height_px = ax.get_figure().get_size_inches()[1] * ax.get_figure().dpi
    ax_bbox = ax.get_position()
    ax_height_data_px = ax_bbox.height * ax_height_px
    min_gap = data_range * (font_size * 1.4) / ax_height_data_px if ax_height_data_px > 0 else 0

    y_positions = [(i, e[1]) for i, e in enumerate(entries)]
    nudged = _nudge_label_positions(y_positions, min_gap)

    x_pos = df.index[-1]
    for i, (dname, _last_y, color) in enumerate(entries):
        y = nudged[i]
        ax.annotate(
            dname,
            xy=(x_pos, y),
            xycoords="data",
            xytext=(6, 0),
            textcoords="offset points",
            color=color,
            fontsize=font_size - 1,
            fontweight="bold",
            va="center",
            ha="left",
            clip_on=False,
        )


# ---------------------------------------------------------------------------
# Annotation helpers — plotly
# ---------------------------------------------------------------------------

def _draw_hlines_plotly(fig, hlines) -> None:
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


def _draw_line_labels_plotly(fig, df, cols, display_names, font_size, m):
    """Draw FT-style end-of-line labels for plotly.

    Places each series name to the right of the plot area at the y-coordinate
    of its last data point, with collision avoidance via _nudge_label_positions.
    """
    # Collect the colour assigned to each trace by matching name
    trace_colors = {}
    for trace in fig.data:
        trace_colors[trace.name] = trace.line.color if trace.line and trace.line.color else None

    entries = []  # (display_name, last_y, color)
    for col in cols:
        dname = _get_display_name(col, display_names)
        series = df[col].dropna()
        if series.empty:
            continue
        last_y = float(series.iloc[-1])
        color = trace_colors.get(dname)
        entries.append((dname, last_y, color))

    if not entries:
        return

    # Determine y-axis range for nudge gap calculation
    yaxis_range = fig.layout.yaxis.range
    if yaxis_range:
        y_min, y_max = yaxis_range
    else:
        all_y = [e[1] for e in entries]
        y_min, y_max = min(all_y), max(all_y)
        # Add some padding
        span = y_max - y_min if y_max != y_min else 1
        y_min -= span * 0.05
        y_max += span * 0.05

    data_range = y_max - y_min if y_max != y_min else 1
    # min_gap: font_size in px relative to chart height in data units
    min_gap = data_range * (font_size * 1.4) / m.chart_h_px

    y_positions = [(i, e[1]) for i, e in enumerate(entries)]
    nudged = _nudge_label_positions(y_positions, min_gap)

    for i, (dname, _last_y, color) in enumerate(entries):
        y = nudged[i]
        fig.add_annotation(
            text=f"<b>{dname}</b>",
            x=1, xref="paper",
            y=y, yref="y",
            xanchor="left",
            yanchor="middle",
            xshift=6,
            showarrow=False,
            font=dict(size=font_size - 1, color=color),
        )


# ---------------------------------------------------------------------------
# Matplotlib backend
# ---------------------------------------------------------------------------

def _plot_ts_mpl(df, left_cols, right_cols, display_names,
                 xaxis, yaxis, yaxis2, font, dimension, title, annotations,
                 source, labels=False, **kwargs):
    """matplotlib implementation — relies on mpl defaults for natural look."""
    import matplotlib.pyplot as plt

    is_dual = len(right_cols) > 0

    # Resolve title / source text
    title_main = title.get("main") if title else None
    title_sub = title.get("sub") or (title.get("subtitle") if title else None) if title else None
    source_text = ("Source: " + ", ".join(source)) if source else None

    fig, ax1 = plt.subplots()

    # Plot left-axis columns
    for col in left_cols:
        label = _get_display_name(col, display_names)
        plot_kwargs = dict(label=label, **kwargs)
        if is_dual:
            plot_kwargs["color"] = LEFT_COLOR
        ax1.plot(df.index, df[col], **plot_kwargs)

    # Dual-axis: right-side columns
    ax2 = None
    if is_dual:
        ax2 = ax1.twinx()
        ax2.tick_params(axis="y", labelcolor=RIGHT_COLOR)
        for col in right_cols:
            label = _get_display_name(col, display_names)
            ax2.plot(df.index, df[col], label=label, color=RIGHT_COLOR, **kwargs)
        ax1.tick_params(axis="y", labelcolor=LEFT_COLOR)

    # Legend or line labels
    font_size = font.get("size", DEFAULT_FONT_SIZE) if font else DEFAULT_FONT_SIZE
    if labels and not is_dual:
        # Line labels mode: no legend, add right margin for labels
        display_label_names = [_get_display_name(c, display_names) for c in left_cols]
        label_width_px = _estimate_label_width_px(display_label_names, font_size)
        # Convert px to inches (matplotlib uses inches at fig DPI)
        fig_w, fig_h = fig.get_size_inches()
        label_margin_inches = label_width_px / fig.dpi
        fig.set_size_inches(fig_w + label_margin_inches, fig_h)
        # Adjust right margin so labels are not clipped
        fig.subplots_adjust(right=fig_w / (fig_w + label_margin_inches))
        _draw_line_labels_mpl(ax1, df, left_cols, display_names, font_size)
    else:
        legend_handles, legend_labels = _build_sorted_legend(
            ax1, ax2, df, left_cols, right_cols, display_names)
        if legend_handles:
            ax1.legend(legend_handles, legend_labels, loc="best")

    # Title and subtitle — use ax.set_title so tight_layout handles spacing
    if title_main and title_sub:
        ax1.set_title(f"{title_main}\n{title_sub}", fontweight="bold")
    elif title_main:
        ax1.set_title(title_main, fontweight="bold")

    # Source — place at bottom of figure
    if source_text:
        fig.text(0.01, 0.01, source_text, fontsize="small",
                 ha="left", va="bottom", transform=fig.transFigure)

    # Axis configuration
    if yaxis and yaxis.get("range"):
        r = yaxis["range"]
        ax1.set_ylim(r[0], r[1])
    if yaxis and yaxis.get("name"):
        ax1.set_ylabel(yaxis["name"])
    if yaxis2 and yaxis2.get("range") and ax2:
        r = yaxis2["range"]
        ax2.set_ylim(r[0], r[1])
    if yaxis2 and yaxis2.get("name") and ax2:
        ax2.set_ylabel(yaxis2["name"], color=RIGHT_COLOR)
    if xaxis and xaxis.get("range"):
        r = xaxis["range"]
        ax1.set_xlim(pd.Timestamp(r[0]), pd.Timestamp(r[1]))
    if xaxis and xaxis.get("name"):
        ax1.set_xlabel(xaxis["name"])

    # Annotations
    if annotations:
        hlines = _normalize_annot_lines(annotations.get("hline"))
        vlines = _normalize_annot_lines(annotations.get("vline"))
        if hlines:
            _draw_hlines_mpl(ax1, hlines)
        if vlines:
            _draw_vlines_mpl(ax1, vlines)

    fig.tight_layout()

    return fig


# ---------------------------------------------------------------------------
# Plotly backend
# ---------------------------------------------------------------------------

def _plot_ts_plotly(df, left_cols, right_cols, display_names,
                    xaxis, yaxis, yaxis2, font, dimension, title, annotations,
                    source, labels=False, **kwargs):
    """plotly implementation — FT-style layout with accent line, titles, source."""
    import plotly.graph_objects as go

    is_dual = len(right_cols) > 0
    use_labels = labels and not is_dual

    # Compute dynamic right margin for line labels
    labels_margin_px = 0
    if use_labels:
        _font_size = font.get("size", DEFAULT_FONT_SIZE) if font else DEFAULT_FONT_SIZE
        display_label_names = [_get_display_name(c, display_names) for c in left_cols]
        labels_margin_px = _estimate_label_width_px(display_label_names, _font_size)

    m = LayoutMetrics.from_params(dimension, font, title, source, is_dual=is_dual,
                                  labels_margin_px=labels_margin_px,
                                  use_labels=use_labels)

    if is_dual:
        from plotly.subplots import make_subplots
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.update_layout(template="pxts")
    else:
        fig = go.Figure()

    # Unified hover: date header uses the most precise format for the data,
    # each entry shows "series_name: value".
    date_fmt = _infer_hover_date_format(df.index)
    unified_hovertemplate = (
        "%{fullData.name}: %{y:.4g}<extra></extra>"
    )

    sorted_left = _sorted_cols_by_last_value(df, left_cols)
    for col in sorted_left:
        name = _get_display_name(col, display_names)
        trace_kwargs = dict(
            x=df.index, y=df[col], mode="lines",
            name=name, hovertemplate=unified_hovertemplate,
        )
        if is_dual:
            trace_kwargs["line"] = dict(color=LEFT_COLOR)
            fig.add_trace(go.Scatter(**trace_kwargs), secondary_y=False)
        else:
            fig.add_trace(go.Scatter(**trace_kwargs))

    if is_dual:
        sorted_right = _sorted_cols_by_last_value(df, right_cols)
        for col in sorted_right:
            name = _get_display_name(col, display_names)
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df[col], mode="lines",
                    name=name, hovertemplate=unified_hovertemplate,
                    line=dict(color=RIGHT_COLOR),
                ),
                secondary_y=True,
            )

    # Build layout using shared metrics
    top_margin = int(m.top_space_px)
    bottom_margin = int(m.bottom_space_px)
    total_w = int(m.total_w_px)
    total_h = int(m.total_h_px)

    # Tooltip font is 2pt smaller than axis labels (axis labels = m.font_size - 1)
    tooltip_font_size = m.font_size - 3

    layout_kwargs = dict(
        hovermode="x unified",
        xaxis=dict(
            type="date", showgrid=False,
            hoverformat=date_fmt,
            showspikes=True, spikemode="across", spikesnap="cursor",
            spikedash="dot", spikethickness=1, spikecolor="#999999",
        ),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#cccccc",
            font=dict(
                size=tooltip_font_size,
                family=m.font_family,
                color=FT_FONT_COLOR,
            ),
        ),
        width=total_w,
        height=total_h,
        margin=dict(l=m.left_margin_px, r=m.right_margin_px,
                    t=top_margin, b=bottom_margin),
        font=dict(family=m.font_family, size=m.font_size - 1, color=FT_FONT_COLOR),
        yaxis=dict(
            showgrid=True, gridcolor=GRID_COLOR, zeroline=False,
            ticksuffix="  ",
        ),
    )

    if use_labels:
        # Labels mode: hide legend and reclaim its vertical space
        layout_kwargs["showlegend"] = False
    else:
        layout_kwargs["legend"] = dict(
            orientation="h",
            x=0, y=0.95,
            xanchor="left", yanchor="bottom",
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=m.font_size - 1, color=FT_FONT_COLOR),
        )

    if not is_dual:
        layout_kwargs["template"] = "pxts"

    # Chrome elements — shared layout
    _draw_title_plotly(fig, m, layout_kwargs)

    fig.update_layout(**layout_kwargs)

    if font:
        fig.update_layout(font=dict(
            size=font.get("size", m.font_size),
            family=font.get("family", m.font_family),
            color=FT_FONT_COLOR,
        ))

    _draw_accent_line_plotly(fig, m)
    _draw_source_plotly(fig, m)

    if is_dual:
        fig.update_yaxes(tickfont=dict(color=LEFT_COLOR), secondary_y=False)
        fig.update_yaxes(
            tickfont=dict(color=RIGHT_COLOR),
            ticksuffix="  ",
            showgrid=False,
            secondary_y=True,
        )
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

    if yaxis and yaxis.get("range"):
        fig.update_layout(yaxis=dict(range=list(yaxis["range"])))
    if yaxis and yaxis.get("name") and not is_dual:
        fig.update_layout(yaxis=dict(title_text=yaxis["name"]))
    if yaxis2 and yaxis2.get("range"):
        fig.update_layout(yaxis2=dict(range=list(yaxis2["range"])))

    if xaxis and xaxis.get("range"):
        r = xaxis["range"]
        fig.update_xaxes(range=[str(pd.Timestamp(r[0])), str(pd.Timestamp(r[1]))])
    if xaxis and xaxis.get("name"):
        fig.update_xaxes(title_text=xaxis["name"])

    if annotations:
        hlines = _normalize_annot_lines(annotations.get("hline"))
        vlines = _normalize_annot_lines(annotations.get("vline"))
        if hlines:
            _draw_hlines_plotly(fig, hlines)
        if vlines:
            _draw_vlines_plotly(fig, vlines)

    # Line labels (after layout is finalised so y-axis range is set)
    if use_labels:
        _draw_line_labels_plotly(fig, df, left_cols, display_names, m.font_size, m)

    return fig


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def tsplot(df, *,
           xaxis=None, yaxis=None, yaxis2=None,
           font=None, dimension=None, title=None, annotations=None,
           source=None, labels=False, backend=None, **kwargs):
    """Plot one or more time series columns from a DataFrame.

    Column selection is done via yaxis["cols"] and yaxis2["cols"]. If neither
    specifies cols, all df columns are plotted on a single axis. If yaxis2 is
    provided (dict with required "cols" key), the chart becomes dual-axis.

    Layout (top to bottom): accent line, title, subtitle, legend,
    chart area, source.

    Args:
        df: pandas DataFrame with a DatetimeIndex.
        xaxis: dict with optional keys: range, name.
        yaxis: dict with optional keys: cols, range, name.
            cols: list of column names or dict {display_name: col_name}.
        yaxis2: dict with required "cols" key and optional: range, name.
            Triggers dual-axis mode.
        font: dict with optional keys: size, family.
        dimension: dict with optional keys: width (default 550),
            aspect_ratio (default 1.5). Governs the chart area only —
            title, legend, source are outside this dimension.
        title: dict with optional keys: main (str), sub (str).
        annotations: dict with optional keys: hline, vline. Each is list or dict.
        source: list of source strings, e.g. ['LSEG', 'Bloomberg'].
            Rendered as "Source: LSEG, Bloomberg" at the bottom.
        labels: bool. If True, replace the legend with FT-style end-of-line
            labels (series name placed to the right of each line's last data
            point, colored to match). Ignored in dual-axis mode with a warning.
        backend: 'matplotlib' or 'plotly'. Defaults to get_backend().
        **kwargs: forwarded to the underlying plot call (e.g., linewidth, alpha).

    Returns:
        matplotlib.figure.Figure or plotly.graph_objects.Figure

    Raises:
        pxtsValidationError: if df does not have a DatetimeIndex.
        ValueError: if columns are not in df, overlap between axes, yaxis2
            missing "cols" key, or dict parameters have invalid shapes.
    """
    # Default title: infer DataFrame variable name from caller's frame
    if title is None:
        df_name = _infer_df_name(df)
        if df_name:
            title = {"main": df_name}

    # Default source
    if source is None:
        source = ["Own calculations"]

    validate_ts(df)
    _validate_tsplot_params(xaxis, yaxis, yaxis2, font, dimension, title,
                            annotations, source)
    left_cols, right_cols, display_names = _resolve_cols(df, yaxis, yaxis2)

    # Warn if labels requested with dual-axis (not supported)
    is_dual = len(right_cols) > 0
    if labels and is_dual:
        warnings.warn(
            "labels=True is not supported in dual-axis mode. "
            "Falling back to the standard legend.",
            stacklevel=2,
        )
        labels = False

    if backend is None:
        backend = get_backend()

    if backend == "matplotlib":
        return _plot_ts_mpl(df, left_cols, right_cols, display_names,
                            xaxis, yaxis, yaxis2, font, dimension, title,
                            annotations, source, labels=labels, **kwargs)
    else:
        return _plot_ts_plotly(df, left_cols, right_cols, display_names,
                               xaxis, yaxis, yaxis2, font, dimension, title,
                               annotations, source, labels=labels, **kwargs)


# ---------------------------------------------------------------------------
# tsgrid — multi-panel time series grid
# ---------------------------------------------------------------------------

def _resolve_panel_cols(df, cols_spec):
    """Resolve a panel's 'cols' spec into (col_list, display_names).

    Works like _resolve_cols but for a single panel (no dual-axis).
    If cols_spec is None, all columns are plotted.

    Args:
        df: pandas DataFrame.
        cols_spec: None, list of column names, or dict {display_name: col_name}.

    Returns:
        (col_list, display_names) where col_list is a list of df column names
        and display_names maps df col name -> display name.
    """
    if cols_spec is None:
        return list(df.columns), {}

    if isinstance(cols_spec, dict):
        col_list = list(cols_spec.values())
        display_names = {v: k for k, v in cols_spec.items()}
    elif isinstance(cols_spec, list):
        col_list = cols_spec
        display_names = {}
    else:
        raise ValueError(
            f"cols must be list, dict, or None, got {type(cols_spec).__name__}"
        )

    bad = [c for c in col_list if c not in df.columns]
    if bad:
        raise ValueError(
            f"Column(s) {bad!r} not in DataFrame. Available: {list(df.columns)}"
        )

    return col_list, display_names


def _validate_tsgrid_params(panels, nrow, ncol, xaxis, yaxis, font,
                              dimension, title, annotations, source):
    """Validate all parameters for tsgrid."""
    if not isinstance(panels, dict):
        raise ValueError(f"panels must be dict, got {type(panels).__name__}")
    if len(panels) == 0:
        raise ValueError("panels must not be empty")
    if not isinstance(nrow, int) or nrow < 1:
        raise ValueError(f"nrow must be a positive integer, got {nrow!r}")
    if not isinstance(ncol, int) or ncol < 1:
        raise ValueError(f"ncol must be a positive integer, got {ncol!r}")
    if len(panels) > nrow * ncol:
        raise ValueError(
            f"Too many panels ({len(panels)}) for a {nrow}x{ncol} grid "
            f"(max {nrow * ncol})"
        )

    for panel_name, panel_spec in panels.items():
        if not isinstance(panel_spec, dict):
            raise ValueError(
                f"Panel '{panel_name}' must be a dict, got {type(panel_spec).__name__}"
            )
        if "data" not in panel_spec:
            raise ValueError(f"Panel '{panel_name}' must contain a 'data' key")
        validate_ts(panel_spec["data"])

    # Validate frequency consistency across panels
    freqs = []
    for panel_name, panel_spec in panels.items():
        df = panel_spec["data"]
        if len(df.index) >= 2:
            diffs = df.index.to_series().diff().dropna()
            min_diff = diffs.min()
            freqs.append((panel_name, min_diff))
    if len(freqs) >= 2:
        base_name, base_freq = freqs[0]
        for other_name, other_freq in freqs[1:]:
            if base_freq != other_freq:
                raise ValueError(
                    f"All panels must have the same data frequency. "
                    f"Panel '{base_name}' has frequency {base_freq}, "
                    f"but panel '{other_name}' has frequency {other_freq}."
                )

    # Reuse existing validation for shared params (pass yaxis2=None)
    _validate_tsplot_params(xaxis, yaxis, None, font, dimension, title,
                            annotations, source)


def _build_global_color_map(panels):
    """Build a global color map assigning consistent colors to display names.

    Collects all unique display names across panels and assigns colors from
    pxts_COLORS in order. Returns dict mapping display_name -> color.
    """
    seen = []
    for panel_spec in panels.values():
        df = panel_spec["data"]
        cols_spec = panel_spec.get("cols")
        col_list, display_names = _resolve_panel_cols(df, cols_spec)
        for col in col_list:
            dname = _get_display_name(col, display_names)
            if dname not in seen:
                seen.append(dname)

    color_map = {}
    for i, dname in enumerate(seen):
        color_map[dname] = pxts_COLORS[i % len(pxts_COLORS)]
    return color_map


def _compute_unified_x_range(panels):
    """Compute the union of all panel date ranges as (min_date, max_date)."""
    all_min = []
    all_max = []
    for panel_spec in panels.values():
        idx = panel_spec["data"].index
        if len(idx) > 0:
            all_min.append(idx.min())
            all_max.append(idx.max())
    if not all_min:
        return None
    return (min(all_min), max(all_max))


def _grid_tsgrid_mpl(panels, nrow, ncol, xaxis, yaxis, font, dimension,
                      title, annotations, source, labels, color_map,
                      unified_x_range, **kwargs):
    """matplotlib backend for tsgrid."""
    import matplotlib.pyplot as plt

    title_main = title.get("main") if title else None
    title_sub = title.get("sub") or (title.get("subtitle") if title else None) if title else None
    source_text = ("Source: " + ", ".join(source)) if source else None
    font_size = font.get("size", DEFAULT_FONT_SIZE) if font else DEFAULT_FONT_SIZE

    fig, axes = plt.subplots(nrow, ncol, squeeze=False)
    panel_items = list(panels.items())

    for idx, (panel_name, panel_spec) in enumerate(panel_items):
        row, col_idx = divmod(idx, ncol)
        ax = axes[row][col_idx]

        df = panel_spec["data"]
        cols_spec = panel_spec.get("cols")
        col_list, display_names = _resolve_panel_cols(df, cols_spec)

        sorted_cols = _sorted_cols_by_last_value(df, col_list)
        for c in sorted_cols:
            dname = _get_display_name(c, display_names)
            ax.plot(df.index, df[c], label=dname,
                    color=color_map.get(dname), **kwargs)

        # Panel subtitle
        ax.set_title(panel_name, fontweight="bold", fontsize=font_size,
                     loc="left")

        # Unified x-axis range
        if xaxis and xaxis.get("range"):
            r = xaxis["range"]
            ax.set_xlim(pd.Timestamp(r[0]), pd.Timestamp(r[1]))
        elif unified_x_range:
            ax.set_xlim(unified_x_range[0], unified_x_range[1])

        if xaxis and xaxis.get("name"):
            ax.set_xlabel(xaxis["name"])

        # Y-axis: global range if specified, otherwise auto-scale per panel
        if yaxis and yaxis.get("range"):
            r = yaxis["range"]
            ax.set_ylim(r[0], r[1])
        if yaxis and yaxis.get("name"):
            ax.set_ylabel(yaxis["name"])

        # Labels or legend per panel
        if labels:
            _draw_line_labels_mpl(ax, df, col_list, display_names, font_size)
        else:
            handles, lbls = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, lbls, loc="best")

        # Annotations
        if annotations:
            hlines = _normalize_annot_lines(annotations.get("hline"))
            vlines = _normalize_annot_lines(annotations.get("vline"))
            if hlines:
                _draw_hlines_mpl(ax, hlines)
            if vlines:
                _draw_vlines_mpl(ax, vlines)

    # Hide unused axes
    for idx in range(len(panel_items), nrow * ncol):
        row, col_idx = divmod(idx, ncol)
        axes[row][col_idx].set_visible(False)

    # Figure-level chrome
    if title_main and title_sub:
        fig.suptitle(f"{title_main}\n{title_sub}", fontweight="bold",
                     ha="left", x=0.01, fontsize=font_size + 2)
    elif title_main:
        fig.suptitle(title_main, fontweight="bold",
                     ha="left", x=0.01, fontsize=font_size + 2)

    if source_text:
        fig.text(0.99, 0.01, source_text, fontsize="small",
                 ha="right", va="bottom", transform=fig.transFigure)

    fig.tight_layout()
    if title_main:
        fig.subplots_adjust(top=0.88)

    return fig


def _grid_tsgrid_plotly(panels, nrow, ncol, xaxis, yaxis, font, dimension,
                         title, annotations, source, labels, color_map,
                         unified_x_range, **kwargs):
    """plotly backend for tsgrid."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    use_labels = labels

    # Layout metrics for chrome
    m = LayoutMetrics.from_params(dimension, font, title, source,
                                  is_dual=False, use_labels=use_labels)

    # Panel subtitles as subplot_titles
    panel_items = list(panels.items())
    subplot_titles = [name for name, _ in panel_items]
    # Pad with None for empty grid slots
    while len(subplot_titles) < nrow * ncol:
        subplot_titles.append(None)

    fig = make_subplots(
        rows=nrow, cols=ncol,
        subplot_titles=subplot_titles,
        shared_xaxes=False,
        horizontal_spacing=0.12,
        vertical_spacing=0.15,
    )
    fig.update_layout(template="pxts")

    # Date format from first panel's data
    first_df = panel_items[0][1]["data"]
    date_fmt = _infer_hover_date_format(first_df.index)
    unified_hovertemplate = "%{fullData.name}: %{y:.4g}<extra></extra>"

    # Track which display names have been added to legend already
    legend_names_seen = set()

    for idx, (panel_name, panel_spec) in enumerate(panel_items):
        row = idx // ncol + 1
        col = idx % ncol + 1

        df = panel_spec["data"]
        cols_spec = panel_spec.get("cols")
        col_list, display_names = _resolve_panel_cols(df, cols_spec)

        sorted_cols = _sorted_cols_by_last_value(df, col_list)
        for c in sorted_cols:
            dname = _get_display_name(c, display_names)
            color = color_map.get(dname)
            show_legend = dname not in legend_names_seen
            legend_names_seen.add(dname)

            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df[c], mode="lines",
                    name=dname, legendgroup=dname,
                    showlegend=show_legend,
                    hovertemplate=unified_hovertemplate,
                    line=dict(color=color),
                ),
                row=row, col=col,
            )

        # Per-panel annotations
        if annotations:
            hlines = _normalize_annot_lines(annotations.get("hline"))
            vlines = _normalize_annot_lines(annotations.get("vline"))
            if hlines:
                if isinstance(hlines, dict):
                    items = hlines.items()
                else:
                    items = [(None, y) for y in hlines]
                for label, y_val in items:
                    fig.add_hline(y=y_val, line_dash="dash",
                                 line_color="gray", line_width=1,
                                 row=row, col=col)
            if vlines:
                if isinstance(vlines, dict):
                    items = vlines.items()
                else:
                    items = [(None, x) for x in vlines]
                for label, x_val in items:
                    fig.add_vline(x=x_val, line_dash="dot",
                                 line_color="gray", line_width=1,
                                 row=row, col=col)

        # Per-panel line labels
        if use_labels:
            # Determine the xaxis/yaxis refs for this subplot
            axis_suffix = "" if idx == 0 else str(idx + 1)
            yaxis_ref = f"y{axis_suffix}" if axis_suffix else "y"

            entries = []
            for c in col_list:
                dname = _get_display_name(c, display_names)
                series = df[c].dropna()
                if series.empty:
                    continue
                last_y = float(series.iloc[-1])
                color = color_map.get(dname)
                entries.append((dname, last_y, color))

            if entries:
                y_vals = [e[1] for e in entries]
                y_min, y_max = min(y_vals), max(y_vals)
                span = y_max - y_min if y_max != y_min else 1
                y_min -= span * 0.05
                y_max += span * 0.05
                data_range = y_max - y_min if y_max != y_min else 1
                panel_h = m.chart_h_px / nrow
                min_gap = data_range * (m.font_size * 1.4) / panel_h

                y_positions = [(i, e[1]) for i, e in enumerate(entries)]
                nudged = _nudge_label_positions(y_positions, min_gap)

                for i, (dname, _last_y, color) in enumerate(entries):
                    y = nudged[i]
                    fig.add_annotation(
                        text=f"<b>{dname}</b>",
                        x=1, xref=f"x{axis_suffix} domain" if axis_suffix else "x domain",
                        y=y, yref=yaxis_ref,
                        xanchor="left", yanchor="middle",
                        xshift=6, showarrow=False,
                        font=dict(size=m.font_size - 1, color=color),
                    )

    # Configure all x-axes with spikes for synchronized crosshair
    total_panels = len(panel_items)
    for idx in range(total_panels):
        axis_suffix = "" if idx == 0 else str(idx + 1)
        xaxis_key = f"xaxis{axis_suffix}" if axis_suffix else "xaxis"
        yaxis_key = f"yaxis{axis_suffix}" if axis_suffix else "yaxis"

        xaxis_update = dict(
            type="date", showgrid=False,
            hoverformat=date_fmt,
            showspikes=True, spikemode="across", spikesnap="cursor",
            spikedash="dot", spikethickness=1, spikecolor="#999999",
        )
        # Unified x-axis range
        if xaxis and xaxis.get("range"):
            r = xaxis["range"]
            xaxis_update["range"] = [str(pd.Timestamp(r[0])),
                                     str(pd.Timestamp(r[1]))]
        elif unified_x_range:
            xaxis_update["range"] = [str(unified_x_range[0]),
                                     str(unified_x_range[1])]
        if xaxis and xaxis.get("name"):
            xaxis_update["title_text"] = xaxis["name"]

        yaxis_update = dict(
            showgrid=True, gridcolor=GRID_COLOR, zeroline=False,
            ticksuffix="  ",
        )
        if yaxis and yaxis.get("range"):
            yaxis_update["range"] = list(yaxis["range"])
        if yaxis and yaxis.get("name"):
            yaxis_update["title_text"] = yaxis["name"]

        fig.update_layout(**{xaxis_key: xaxis_update, yaxis_key: yaxis_update})

    # Style panel subtitles (bold, left-aligned)
    for ann in fig.layout.annotations:
        if ann.text in [name for name, _ in panel_items]:
            ann.font = dict(size=m.font_size, color=FT_FONT_COLOR,
                            family=m.font_family)
            ann.x = ann.x - 0.04  # nudge left
            ann.xanchor = "left"

    # Overall figure dimensions
    total_w = int(m.total_w_px)
    total_h = int(m.total_h_px)

    tooltip_font_size = m.font_size - 3

    layout_kwargs = dict(
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#cccccc",
            font=dict(size=tooltip_font_size, family=m.font_family,
                      color=FT_FONT_COLOR),
        ),
        width=total_w,
        height=total_h,
        margin=dict(l=m.left_margin_px, r=m.right_margin_px,
                    t=int(m.top_space_px), b=int(m.bottom_space_px)),
        font=dict(family=m.font_family, size=m.font_size - 1,
                  color=FT_FONT_COLOR),
    )

    if use_labels:
        layout_kwargs["showlegend"] = False
    else:
        layout_kwargs["legend"] = dict(
            orientation="h",
            x=0, y=0.95,
            xanchor="left", yanchor="bottom",
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=m.font_size - 1, color=FT_FONT_COLOR),
        )

    _draw_title_plotly(fig, m, layout_kwargs)
    fig.update_layout(**layout_kwargs)

    _draw_accent_line_plotly(fig, m)
    _draw_source_plotly(fig, m)

    return fig


def tsgrid(panels, *, nrow=1, ncol=1, xaxis=None, yaxis=None,
           font=None, dimension=None, title=None, annotations=None,
           source=None, labels=False, backend=None, **kwargs):
    """Plot a grid of time series panels.

    Each panel is an independent time series chart. All panels share the same
    x-axis range (union of all date ranges), color assignment (by display
    name), and global styling. Hovering on one panel shows the crosshair
    on all panels (Plotly only).

    Args:
        panels: dict mapping panel subtitle (str) to panel spec dict.
            Each panel spec has keys:
                data: pandas DataFrame with DatetimeIndex.
                cols (optional): list of column names or dict
                    {display_name: col_name}. Defaults to all columns.
        nrow: number of grid rows (default 1).
        ncol: number of grid columns (default 1).
        xaxis: dict with optional keys: range, name. Applied globally.
        yaxis: dict with optional keys: range, name.
            range: if provided, applied to all panels identically.
            If omitted, each panel auto-scales independently.
        font: dict with optional keys: size, family.
        dimension: dict with optional keys: width, aspect_ratio.
            Governs total figure size.
        title: dict with optional keys: main (str), sub (str).
        annotations: dict with optional keys: hline, vline.
            Applied to all panels.
        source: list of source strings. Rendered once at the bottom.
        labels: bool. If True, use end-of-line labels instead of legend.
        backend: 'matplotlib' or 'plotly'. Defaults to get_backend().
        **kwargs: forwarded to the underlying plot call.

    Returns:
        matplotlib.figure.Figure or plotly.graph_objects.Figure

    Raises:
        pxtsValidationError: if any panel's data lacks a DatetimeIndex.
        ValueError: for invalid parameters, frequency mismatch, etc.
    """
    # Default source
    if source is None:
        source = ["Own calculations"]

    _validate_tsgrid_params(panels, nrow, ncol, xaxis, yaxis, font,
                             dimension, title, annotations, source)

    color_map = _build_global_color_map(panels)
    unified_x_range = _compute_unified_x_range(panels)

    if backend is None:
        backend = get_backend()

    if backend == "matplotlib":
        return _grid_tsgrid_mpl(panels, nrow, ncol, xaxis, yaxis, font,
                                 dimension, title, annotations, source,
                                 labels, color_map, unified_x_range, **kwargs)
    else:
        return _grid_tsgrid_plotly(panels, nrow, ncol, xaxis, yaxis, font,
                                   dimension, title, annotations, source,
                                   labels, color_map, unified_x_range,
                                   **kwargs)
