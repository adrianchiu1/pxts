"""Unit tests for pxts.plots: unified tsplot function.

Rendering is mocked via matplotlib.use("Agg") (non-interactive) and by passing
explicit backend= parameters, bypassing get_backend() entirely.
"""
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — MUST be before any pyplot import

import matplotlib.pyplot as plt
import matplotlib.figure
import plotly.graph_objects as go
import pandas as pd
import pytest

from pxts.plots import tsplot
from pxts.exceptions import pxtsValidationError


# ---------------------------------------------------------------------------
# Single-axis — matplotlib
# ---------------------------------------------------------------------------

class TestTsplotSingleMpl:
    def test_default_all_cols(self, ts_df):
        fig = tsplot(ts_df, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_explicit_cols_via_yaxis(self, ts_df):
        fig = tsplot(ts_df, yaxis={"cols": ["A"]}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_dict_cols_display_names(self, ts_df):
        fig = tsplot(ts_df, yaxis={"cols": {"Alpha": "A"}}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        # Legend is now placed via bbox_to_anchor on ax1
        ax = fig.axes[0]
        legend = ax.get_legend()
        assert legend is not None
        legend_texts = [t.get_text() for t in legend.get_texts()]
        assert "Alpha" in legend_texts
        plt.close(fig)

    def test_unknown_col_raises(self, ts_df):
        with pytest.raises(ValueError, match="UNKNOWN"):
            tsplot(ts_df, yaxis={"cols": ["UNKNOWN"]}, backend="matplotlib")


# ---------------------------------------------------------------------------
# Single-axis — plotly
# ---------------------------------------------------------------------------

class TestTsplotSinglePlotly:
    def test_default_all_cols(self, ts_df):
        fig = tsplot(ts_df, backend="plotly")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == len(ts_df.columns)

    def test_explicit_cols_via_yaxis(self, ts_df):
        fig = tsplot(ts_df, yaxis={"cols": ["A"]}, backend="plotly")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1

    def test_dict_cols_display_names(self, ts_df):
        fig = tsplot(ts_df, yaxis={"cols": {"Alpha": "A"}}, backend="plotly")
        assert fig.data[0].name == "Alpha"

    def test_showlegend_true_in_template(self, ts_df):
        fig = tsplot(ts_df, backend="plotly")
        assert fig.layout.template.layout.showlegend is True


# ---------------------------------------------------------------------------
# Dual-axis — matplotlib (via yaxis2)
# ---------------------------------------------------------------------------

class TestTsplotDualMpl:
    def test_dual_returns_figure(self, ts_df):
        fig = tsplot(ts_df, yaxis={"cols": ["A"]}, yaxis2={"cols": ["B"]}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_auto_excludes_right_from_left(self, ts_df):
        """No yaxis cols + yaxis2 → left gets A, right gets B."""
        fig = tsplot(ts_df, yaxis2={"cols": ["B"]}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_dual_has_two_axes(self, ts_df):
        fig = tsplot(ts_df, yaxis={"cols": ["A"]}, yaxis2={"cols": ["B"]}, backend="matplotlib")
        assert len(fig.axes) == 2
        plt.close(fig)


# ---------------------------------------------------------------------------
# Dual-axis — plotly (via yaxis2)
# ---------------------------------------------------------------------------

class TestTsplotDualPlotly:
    def test_dual_returns_figure(self, ts_df):
        fig = tsplot(ts_df, yaxis={"cols": ["A"]}, yaxis2={"cols": ["B"]}, backend="plotly")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2

    def test_auto_excludes_right_from_left(self, ts_df):
        fig = tsplot(ts_df, yaxis2={"cols": ["B"]}, backend="plotly")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2

    def test_yaxis2_name_sets_title(self, ts_df):
        fig = tsplot(ts_df, yaxis={"cols": ["A"]},
                     yaxis2={"cols": ["B"], "name": "Pressure"},
                     backend="plotly")
        assert fig.layout.yaxis2.title.text == "Pressure"

    def test_yaxis_name_sets_left_title(self, ts_df):
        fig = tsplot(ts_df, yaxis={"cols": ["A"], "name": "Energy"},
                     yaxis2={"cols": ["B"]},
                     backend="plotly")
        assert fig.layout.yaxis.title.text == "Energy"

    def test_showlegend_true_in_template(self, ts_df):
        fig = tsplot(ts_df, yaxis={"cols": ["A"]}, yaxis2={"cols": ["B"]}, backend="plotly")
        assert fig.layout.template.layout.showlegend is True


# ---------------------------------------------------------------------------
# Cols resolution
# ---------------------------------------------------------------------------

class TestColsResolution:
    def test_overlap_raises(self, ts_df):
        with pytest.raises(ValueError, match="appear in both"):
            tsplot(ts_df, yaxis={"cols": ["A", "B"]}, yaxis2={"cols": ["A"]}, backend="matplotlib")

    def test_yaxis2_without_cols_key_raises(self, ts_df):
        with pytest.raises(ValueError, match="cols"):
            tsplot(ts_df, yaxis2={"range": [0, 10]}, backend="matplotlib")

    def test_yaxis2_not_dict_raises(self, ts_df):
        with pytest.raises(ValueError, match="yaxis2 must be dict"):
            tsplot(ts_df, yaxis2=["B"], backend="matplotlib")

    def test_yaxis_cols_wrong_type_raises(self, ts_df):
        with pytest.raises(ValueError, match="cols.*must be list or dict"):
            tsplot(ts_df, yaxis={"cols": "A"}, backend="matplotlib")

    def test_dict_cols_with_dict_yaxis2_cols(self, ts_df):
        fig = tsplot(ts_df,
                     yaxis={"cols": {"Alpha": "A"}},
                     yaxis2={"cols": {"Beta": "B"}},
                     backend="plotly")
        names = [t.name for t in fig.data]
        assert "Alpha" in names
        assert "Beta" in names


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidation:
    def test_non_datetime_index_raises(self, bad_df):
        with pytest.raises(pxtsValidationError):
            tsplot(bad_df, backend="matplotlib")

    def test_unknown_col_raises(self, ts_df):
        with pytest.raises(ValueError, match="NOPE"):
            tsplot(ts_df, yaxis={"cols": ["NOPE"]}, backend="matplotlib")

    def test_xaxis_range_not_date_raises(self, ts_df):
        with pytest.raises(ValueError, match="xaxis"):
            tsplot(ts_df, xaxis={"range": [1, 2]}, backend="matplotlib")

    def test_yaxis_range_wrong_length_raises(self, ts_df):
        with pytest.raises(ValueError, match="yaxis"):
            tsplot(ts_df, yaxis={"range": [1, 2, 3]}, backend="matplotlib")

    def test_yaxis_not_dict_raises(self, ts_df):
        with pytest.raises(ValueError, match="yaxis must be dict"):
            tsplot(ts_df, yaxis="bad", backend="matplotlib")

    def test_title_not_dict_raises(self, ts_df):
        with pytest.raises(ValueError, match="title must be dict"):
            tsplot(ts_df, title="bad", backend="matplotlib")

    def test_annotations_hline_wrong_type_raises(self, ts_df):
        with pytest.raises(ValueError, match="annotations"):
            tsplot(ts_df, annotations={"hline": "bad"}, backend="matplotlib")

    def test_dimension_not_dict_raises(self, ts_df):
        with pytest.raises(ValueError, match="dimension must be dict"):
            tsplot(ts_df, dimension="bad", backend="matplotlib")

    def test_source_not_list_raises(self, ts_df):
        with pytest.raises(ValueError, match="source must be list"):
            tsplot(ts_df, source="LSEG", backend="matplotlib")

    def test_annotations_not_dict_raises(self, ts_df):
        with pytest.raises(ValueError, match="annotations must be dict"):
            tsplot(ts_df, annotations="bad", backend="matplotlib")


# ---------------------------------------------------------------------------
# Annotations (hline / vline)
# ---------------------------------------------------------------------------

class TestAnnotations:
    def test_hline_list_mpl(self, ts_df):
        fig = tsplot(ts_df, annotations={"hline": [1.0, 3.0]}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_hline_dict_mpl(self, ts_df):
        fig = tsplot(ts_df, annotations={"hline": {"low": 1.0, "high": 4.0}}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_vline_list_mpl(self, ts_df):
        fig = tsplot(ts_df, annotations={"vline": [pd.Timestamp("2024-01-03")]}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_hline_list_plotly(self, ts_df):
        fig = tsplot(ts_df, annotations={"hline": [1.0, 3.0]}, backend="plotly")
        # 2 hlines + accent line shape = 3 shapes
        hline_shapes = [s for s in fig.layout.shapes if s.type == "line"
                        and s.yref != "paper"]
        assert len(hline_shapes) == 2

    def test_hline_scalar_normalized(self, ts_df):
        """Scalar hline value is normalized to list."""
        fig = tsplot(ts_df, annotations={"hline": 42.0}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ---------------------------------------------------------------------------
# Dimension
# ---------------------------------------------------------------------------

class TestDimension:
    def test_dimension_mpl_default(self, ts_df):
        """Default: matplotlib uses its own default figsize."""
        fig = tsplot(ts_df, backend="matplotlib")
        w, h = fig.get_size_inches()
        # matplotlib default is (6.4, 4.8) — just verify a figure is created
        assert w > 0 and h > 0
        plt.close(fig)

    def test_dimension_mpl_custom(self, ts_df):
        """Dimension param is ignored for mpl — always uses mpl defaults."""
        fig = tsplot(ts_df, dimension={"width": 800, "aspect_ratio": 2.0}, backend="matplotlib")
        w, h = fig.get_size_inches()
        assert w > 0 and h > 0
        plt.close(fig)

    def test_dimension_plotly(self, ts_df):
        fig = tsplot(ts_df, dimension={"width": 800, "aspect_ratio": 2.0}, backend="plotly")
        chart_h = 800 / 2.0
        # Total width = chart + margins, total height = chart + margins
        assert fig.layout.width > 800
        assert fig.layout.height > chart_h


# ---------------------------------------------------------------------------
# Font
# ---------------------------------------------------------------------------

class TestFont:
    def test_font_plotly(self, ts_df):
        fig = tsplot(ts_df, font={"size": 18}, backend="plotly")
        assert fig.layout.font.size == 18


# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------

class TestTitle:
    def test_title_main_mpl(self, ts_df):
        fig = tsplot(ts_df, title={"main": "My Title"}, backend="matplotlib")
        ax = fig.axes[0]
        assert "My Title" in ax.get_title()
        plt.close(fig)

    def test_title_plotly(self, ts_df):
        # Title is rendered via layout.title (native Plotly pipeline).
        fig = tsplot(ts_df, title={"main": "My Title"}, backend="plotly")
        assert "My Title" in (fig.layout.title.text or "")

    def test_title_and_sub_plotly(self, ts_df):
        # Both lines combined in a single layout.title.text HTML string.
        fig = tsplot(ts_df, title={"main": "Main", "sub": "Sub"}, backend="plotly")
        title_text = fig.layout.title.text or ""
        assert "Main" in title_text
        assert "Sub" in title_text

    def test_sub_mpl(self, ts_df):
        fig = tsplot(ts_df, title={"main": "Main", "sub": "Sub"}, backend="matplotlib")
        ax = fig.axes[0]
        title_text = ax.get_title()
        assert "Main" in title_text
        assert "Sub" in title_text
        plt.close(fig)


# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------

class TestSource:
    def test_source_mpl(self, ts_df):
        fig = tsplot(ts_df, source=["LSEG"], backend="matplotlib")
        texts = [t.get_text() for t in fig.texts]
        assert "Source: LSEG" in texts
        plt.close(fig)

    def test_source_multiple_mpl(self, ts_df):
        fig = tsplot(ts_df, source=["LSEG", "Bloomberg"], backend="matplotlib")
        texts = [t.get_text() for t in fig.texts]
        assert "Source: LSEG, Bloomberg" in texts
        plt.close(fig)

    def test_source_plotly(self, ts_df):
        fig = tsplot(ts_df, source=["LSEG"], backend="plotly")
        annot_texts = [a.text for a in fig.layout.annotations]
        assert "Source: LSEG" in annot_texts


# ---------------------------------------------------------------------------
# Accent line
# ---------------------------------------------------------------------------

class TestAccentLine:
    def test_no_accent_line_mpl(self, ts_df):
        """Matplotlib backend should not have an accent line."""
        from matplotlib.lines import Line2D
        fig = tsplot(ts_df, backend="matplotlib")
        # Only Line2D artists at the figure level (not axes) would be accent lines
        figure_lines = [a for a in fig.get_children()
                        if isinstance(a, Line2D) and a.axes is None]
        assert len(figure_lines) == 0
        plt.close(fig)

    def test_accent_line_plotly(self, ts_df):
        """Plotly figure should have a shape for the accent line at paper ref."""
        fig = tsplot(ts_df, backend="plotly")
        accent_shapes = [s for s in fig.layout.shapes
                         if s.xref == "paper" and s.yref == "paper"]
        assert len(accent_shapes) >= 1



# ---------------------------------------------------------------------------
# Axis ranges
# ---------------------------------------------------------------------------

class TestAxisRanges:
    def test_yaxis_range_mpl(self, ts_df):
        fig = tsplot(ts_df, yaxis={"range": [0, 10]}, backend="matplotlib")
        ax = fig.axes[0]
        lo, hi = ax.get_ylim()
        assert lo == pytest.approx(0)
        assert hi == pytest.approx(10)
        plt.close(fig)

    def test_yaxis_range_plotly(self, ts_df):
        fig = tsplot(ts_df, yaxis={"range": [0, 10]}, backend="plotly")
        assert list(fig.layout.yaxis.range) == [0, 10]

    def test_xaxis_range_mpl(self, ts_df):
        fig = tsplot(ts_df,
                     xaxis={"range": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-05")]},
                     backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_xaxis_range_plotly(self, ts_df):
        fig = tsplot(ts_df,
                     xaxis={"range": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-05")]},
                     backend="plotly")
        assert isinstance(fig, go.Figure)

    def test_yaxis2_range_plotly(self, ts_df):
        fig = tsplot(ts_df, yaxis={"cols": ["A"]},
                     yaxis2={"cols": ["B"], "range": [0, 10]},
                     backend="plotly")
        assert list(fig.layout.yaxis2.range) == [0, 10]

    def test_yaxis2_range_mpl(self, ts_df):
        fig = tsplot(ts_df, yaxis={"cols": ["A"]},
                     yaxis2={"cols": ["B"], "range": [0, 10]},
                     backend="matplotlib")
        ax2 = fig.axes[1]  # secondary axis
        lo, hi = ax2.get_ylim()
        assert lo == pytest.approx(0)
        assert hi == pytest.approx(10)
        plt.close(fig)


# ---------------------------------------------------------------------------
# Plotly template
# ---------------------------------------------------------------------------

class TestPlotlyTemplate:
    def test_template_has_tighter_margins(self):
        import plotly.io as pio
        template = pio.templates["pxts"]
        m = template.layout.margin
        assert m.l is not None or m.r is not None

    def test_template_legend_horizontal(self):
        import plotly.io as pio
        template = pio.templates["pxts"]
        assert template.layout.legend.orientation == "h"

    def test_template_no_vertical_grid(self):
        import plotly.io as pio
        template = pio.templates["pxts"]
        assert template.layout.xaxis.showgrid is False


# ---------------------------------------------------------------------------
# FT styling
# ---------------------------------------------------------------------------

class TestFTStyling:
    def test_spines_visible_mpl(self, ts_df):
        """Matplotlib backend uses default spines (all visible)."""
        fig = tsplot(ts_df, backend="matplotlib")
        ax = fig.axes[0]
        for spine in ax.spines.values():
            assert spine.get_visible()
        plt.close(fig)

    def test_horizontal_gridlines_only_plotly(self, ts_df):
        fig = tsplot(ts_df, backend="plotly")
        assert fig.layout.yaxis.showgrid is True
        assert fig.layout.xaxis.showgrid is False
