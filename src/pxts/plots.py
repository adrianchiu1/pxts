"""pxts plots module: time series line charts for matplotlib and plotly backends.

Public API:
    tsplot(df, *, xaxis=None, yaxis=None, yaxis2=None, font=None,
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
    MASTER_SPACING_PX,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LEFT_COLOR: str = pxts_COLORS[0]   # '#0072B2' Blue
RIGHT_COLOR: str = pxts_COLORS[1]  # '#D55E00' Vermillion


def _estimate_xaxis_pad_px(idx: pd.DatetimeIndex, font_size: int) -> int:
    """Estimate pixels needed for x-axis tick labels based on data frequency.

    Single-line formats (annual, monthly, daily) need one line-height.
    Formats with both a date and a time component ('%Y-%m-%d %H:%M…') are long
    enough that Plotly may wrap or rotate them, so two line-heights are used.
    """
    fmt = _infer_hover_date_format(idx)
    line_h = int(font_size * 2)          # generous line-height per row of text
    lines = 2 if len(fmt) > 10 else 1   # datetime formats are >10 chars
    return lines * line_h + 10           # +10px breathing room


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
        accent_top_px | accent line | accent_gap_px | title | subtitle |
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
    accent_top_px: float = MASTER_SPACING_PX + 1.5  # figure top → accent line centre
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
                    labels_margin_px: int = 0, use_labels: bool = False, idx=None):
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

        pad_bottom = (
            _estimate_xaxis_pad_px(idx, font_size) if idx is not None and len(idx) > 0
            else 45
        )

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
            source_h_px=(MASTER_SPACING_PX + font_size * 1.5 - 1) if source_text else 0,
            right_margin_px=right_margin,
            legend_h_px=0 if use_labels else 28,
            legend_gap_px=0 if use_labels else 6,
            pad_bottom_px=pad_bottom,
        )

    @property
    def top_space_px(self) -> float:
        return (self.accent_top_px + self.accent_gap_px + self.title_h_px
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
    def title_top_px(self) -> float:
        """Pixels from figure top to the top of the title text block.

        With yanchor='top', Plotly anchors to the true top of the bounding box,
        so no compensation for text height is needed.  The base offset places
        the title MASTER_SPACING_PX below the bottom edge of the accent line.
        """
        return MASTER_SPACING_PX * 2 + ACCENT_LINE_WIDTH

    @property
    def left_align_x_plotly(self) -> float:
        """X in plotly paper space corresponding to MASTER_SPACING_PX from the figure left."""
        return (MASTER_SPACING_PX - self.left_margin_px) / self.chart_w_px


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


# Per-character advance widths for a proportional sans-serif (Helvetica/Arial metrics,
# measured at 16px). Scaled linearly to actual font_size at render time.
# Covers the printable ASCII range; anything outside falls back to the median width.
_CHAR_WIDTHS_16PX: dict[str, float] = {
    " ": 4.4, "!": 4.4, '"': 5.7, "#": 8.9, "$": 8.9, "%": 14.2,
    "&": 10.7, "'": 3.1, "(": 5.3, ")": 5.3, "*": 6.2, "+": 9.3,
    ",": 4.4, "-": 5.3, ".": 4.4, "/": 4.4,
    "0": 8.9, "1": 7.7, "2": 8.9, "3": 8.9, "4": 8.9,
    "5": 8.9, "6": 8.9, "7": 8.9, "8": 8.9, "9": 8.9,
    ":": 4.4, ";": 4.4, "<": 9.3, "=": 9.3, ">": 9.3,
    "?": 8.9, "@": 16.2,
    "A": 10.7, "B": 10.7, "C": 11.6, "D": 11.6, "E": 10.7,
    "F": 9.8,  "G": 12.4, "H": 11.6, "I": 4.4,  "J": 8.0,
    "K": 10.7, "L": 8.9,  "M": 13.3, "N": 11.6, "O": 12.4,
    "P": 10.7, "Q": 12.4, "R": 11.6, "S": 10.7, "T": 9.8,
    "U": 11.6, "V": 10.7, "W": 15.1, "X": 10.7, "Y": 10.7,
    "Z": 9.8,
    "[": 4.4, "\\": 4.4, "]": 4.4, "^": 7.5, "_": 8.9, "`": 5.3,
    "a": 8.9, "b": 8.9, "c": 8.0, "d": 8.9, "e": 8.9,
    "f": 4.2, "g": 8.9, "h": 8.9, "i": 3.6, "j": 3.6,
    "k": 8.0, "l": 3.6, "m": 13.3, "n": 8.9, "o": 8.9,
    "p": 8.9, "q": 8.9, "r": 5.3, "s": 8.0, "t": 4.4,
    "u": 8.9, "v": 8.0, "w": 11.6, "x": 8.0, "y": 8.0, "z": 8.0,
    "{": 5.3, "|": 4.2, "}": 5.3, "~": 9.3,
}
_FALLBACK_CHAR_WIDTH_16PX: float = 8.9  # median advance width for unknown characters


def _estimate_label_width_px(labels, font_size):
    """Estimate the right-margin width (px) needed to display line labels.

    Uses per-character advance widths (Helvetica/Arial proportions at 16px, scaled
    to font_size) so that short labels like 'EU' — where every character is a wide
    capital — are not underestimated by a flat per-character factor.

    The returned value covers: xshift gap (6px) + text width + trailing breathing
    room (10px).
    """
    if not labels:
        return 0
    # Labels are drawn at font_size - 1
    render_size = font_size - 1
    scale = render_size / 16.0
    longest_px = max(
        sum(_CHAR_WIDTHS_16PX.get(ch, _FALLBACK_CHAR_WIDTH_16PX) for ch in lbl)
        for lbl in labels
    )
    text_px = longest_px * scale
    # xshift=8 is hardcoded in the annotation; trailing gap = 12px
    return int(text_px) + 8 + 12


# ---------------------------------------------------------------------------
# Chrome drawing — matplotlib
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Chrome drawing — plotly
# ---------------------------------------------------------------------------

def _draw_accent_line_plotly(fig, m: LayoutMetrics) -> None:
    """Draw the FT-style accent line at the top of a plotly figure."""
    accent_y = 1 + (m.top_space_px - m.accent_top_px) / m.chart_h_px
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

    # MASTER_SPACING_PX from figure left; title uses container coords (0=fig left, 1=fig right)
    title_x = MASTER_SPACING_PX / m.total_w_px
    # title_top_px below the figure top (container coords: 1=fig top, 0=fig bottom)
    title_y = 1 - m.title_top_px / m.total_h_px

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
        yshift=-m.pad_bottom_px,
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
            text=dname,
            x=1, xref="paper",
            y=y, yref="y",
            xanchor="left",
            yanchor="middle",
            xshift=8,
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
                                  use_labels=use_labels, idx=df.index)

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
    for i, col in enumerate(sorted_left):
        name = _get_display_name(col, display_names)
        trace_kwargs = dict(
            x=df.index, y=df[col], mode="lines",
            name=name, hovertemplate=unified_hovertemplate,
        )
        if is_dual:
            trace_kwargs["line"] = dict(color=LEFT_COLOR)
            fig.add_trace(go.Scatter(**trace_kwargs), secondary_y=False)
        else:
            trace_kwargs["line"] = dict(color=pxts_COLORS[i % len(pxts_COLORS)])
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
            automargin=True,
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
