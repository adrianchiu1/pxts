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
    def test_default_cols_returns_figure(self, ts_df):
        fig = tsplot(ts_df, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_explicit_cols(self, ts_df):
        fig = tsplot(ts_df, cols=["A"], backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_dict_cols_display_names(self, ts_df):
        fig = tsplot(ts_df, cols={"Alpha": "A"}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        # Legend should use display name
        ax = fig.axes[0]
        legend_texts = [t.get_text() for t in ax.get_legend().get_texts()]
        assert "Alpha" in legend_texts
        plt.close(fig)

    def test_unknown_col_raises(self, ts_df):
        with pytest.raises(ValueError, match="UNKNOWN"):
            tsplot(ts_df, cols=["UNKNOWN"], backend="matplotlib")


# ---------------------------------------------------------------------------
# Single-axis — plotly
# ---------------------------------------------------------------------------

class TestTsplotSinglePlotly:
    def test_default_cols_returns_figure(self, ts_df):
        fig = tsplot(ts_df, backend="plotly")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == len(ts_df.columns)

    def test_explicit_cols(self, ts_df):
        fig = tsplot(ts_df, cols=["A"], backend="plotly")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1

    def test_dict_cols_display_names(self, ts_df):
        fig = tsplot(ts_df, cols={"Alpha": "A"}, backend="plotly")
        assert fig.data[0].name == "Alpha"

    def test_showlegend_true_in_template(self, ts_df):
        fig = tsplot(ts_df, backend="plotly")
        assert fig.layout.template.layout.showlegend is True


# ---------------------------------------------------------------------------
# Dual-axis — matplotlib (via yaxis2)
# ---------------------------------------------------------------------------

class TestTsplotDualMpl:
    def test_dual_returns_figure(self, ts_df):
        fig = tsplot(ts_df, cols=["A"], yaxis2={"cols": ["B"]}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_cols_none_auto_excludes(self, ts_df):
        """cols=None + yaxis2 → left gets A, right gets B."""
        fig = tsplot(ts_df, yaxis2={"cols": ["B"]}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_dual_has_two_axes(self, ts_df):
        fig = tsplot(ts_df, cols=["A"], yaxis2={"cols": ["B"]}, backend="matplotlib")
        assert len(fig.axes) == 2
        plt.close(fig)


# ---------------------------------------------------------------------------
# Dual-axis — plotly (via yaxis2)
# ---------------------------------------------------------------------------

class TestTsplotDualPlotly:
    def test_dual_returns_figure(self, ts_df):
        fig = tsplot(ts_df, cols=["A"], yaxis2={"cols": ["B"]}, backend="plotly")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2

    def test_cols_none_auto_excludes(self, ts_df):
        fig = tsplot(ts_df, yaxis2={"cols": ["B"]}, backend="plotly")
        assert isinstance(fig, go.Figure)
        # Should have 2 traces: A on left, B on right
        assert len(fig.data) == 2

    def test_yaxis2_name_sets_title(self, ts_df):
        fig = tsplot(ts_df, cols=["A"],
                     yaxis2={"cols": ["B"], "name": "Pressure"},
                     backend="plotly")
        assert fig.layout.yaxis2.title.text == "Pressure"

    def test_yaxis_name_sets_left_title(self, ts_df):
        fig = tsplot(ts_df, cols=["A"],
                     yaxis={"name": "Energy"},
                     yaxis2={"cols": ["B"]},
                     backend="plotly")
        assert fig.layout.yaxis.title.text == "Energy"

    def test_showlegend_true_in_template(self, ts_df):
        fig = tsplot(ts_df, cols=["A"], yaxis2={"cols": ["B"]}, backend="plotly")
        assert fig.layout.template.layout.showlegend is True


# ---------------------------------------------------------------------------
# Cols resolution
# ---------------------------------------------------------------------------

class TestColsResolution:
    def test_overlap_raises(self, ts_df):
        with pytest.raises(ValueError, match="appear in both"):
            tsplot(ts_df, cols=["A", "B"], yaxis2={"cols": ["A"]}, backend="matplotlib")

    def test_yaxis2_without_cols_key_raises(self, ts_df):
        with pytest.raises(ValueError, match="cols"):
            tsplot(ts_df, yaxis2={"range": [0, 10]}, backend="matplotlib")

    def test_yaxis2_not_dict_raises(self, ts_df):
        with pytest.raises(ValueError, match="yaxis2 must be dict"):
            tsplot(ts_df, yaxis2=["B"], backend="matplotlib")

    def test_cols_wrong_type_raises(self, ts_df):
        with pytest.raises(ValueError, match="cols must be"):
            tsplot(ts_df, cols="A", backend="matplotlib")

    def test_dict_cols_with_dict_yaxis2_cols(self, ts_df):
        fig = tsplot(ts_df,
                     cols={"Alpha": "A"},
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
            tsplot(ts_df, cols=["NOPE"], backend="matplotlib")

    def test_xaxis_range_not_date_raises(self, ts_df):
        with pytest.raises(ValueError, match="xaxis"):
            tsplot(ts_df, xaxis={"range": [1, 2]}, backend="matplotlib")

    def test_yaxis_range_wrong_length_raises(self, ts_df):
        with pytest.raises(ValueError, match="yaxis"):
            tsplot(ts_df, yaxis={"range": [1, 2, 3]}, backend="matplotlib")

    def test_yaxis_not_dict_raises(self, ts_df):
        with pytest.raises(ValueError, match="yaxis must be dict"):
            tsplot(ts_df, yaxis="bad", backend="matplotlib")

    def test_titles_not_dict_raises(self, ts_df):
        with pytest.raises(ValueError, match="titles must be dict"):
            tsplot(ts_df, titles="bad", backend="matplotlib")

    def test_annot_hline_wrong_type_raises(self, ts_df):
        with pytest.raises(ValueError, match="annot"):
            tsplot(ts_df, annot={"hline": "bad"}, backend="matplotlib")


# ---------------------------------------------------------------------------
# Annotations (hline / vline)
# ---------------------------------------------------------------------------

class TestAnnot:
    def test_hline_list_mpl(self, ts_df):
        fig = tsplot(ts_df, annot={"hline": [1.0, 3.0]}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_hline_dict_mpl(self, ts_df):
        fig = tsplot(ts_df, annot={"hline": {"low": 1.0, "high": 4.0}}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_vline_list_mpl(self, ts_df):
        fig = tsplot(ts_df, annot={"vline": [pd.Timestamp("2024-01-03")]}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_hline_list_plotly(self, ts_df):
        fig = tsplot(ts_df, annot={"hline": [1.0, 3.0]}, backend="plotly")
        assert len(fig.layout.shapes) == 2

    def test_hline_scalar_normalized(self, ts_df):
        """Scalar hline value is normalized to list."""
        fig = tsplot(ts_df, annot={"hline": 42.0}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ---------------------------------------------------------------------------
# Dim
# ---------------------------------------------------------------------------

class TestDim:
    def test_dim_mpl(self, ts_df):
        fig = tsplot(ts_df, dim={"width": 800, "height": 400}, backend="matplotlib")
        w, h = fig.get_size_inches()
        assert w == pytest.approx(8.0)
        assert h == pytest.approx(4.0)
        plt.close(fig)

    def test_dim_plotly(self, ts_df):
        fig = tsplot(ts_df, dim={"width": 800, "height": 400}, backend="plotly")
        assert fig.layout.width == 800
        assert fig.layout.height == 400


# ---------------------------------------------------------------------------
# Font
# ---------------------------------------------------------------------------

class TestFont:
    def test_font_plotly(self, ts_df):
        fig = tsplot(ts_df, font={"size": 18}, backend="plotly")
        assert fig.layout.font.size == 18


# ---------------------------------------------------------------------------
# Titles
# ---------------------------------------------------------------------------

class TestTitles:
    def test_title_mpl(self, ts_df):
        fig = tsplot(ts_df, titles={"title": "My Title"}, backend="matplotlib")
        assert fig._suptitle.get_text() == "My Title"
        plt.close(fig)

    def test_title_plotly(self, ts_df):
        fig = tsplot(ts_df, titles={"title": "My Title"}, backend="plotly")
        assert fig.layout.title.text == "My Title"

    def test_title_and_subtitle_plotly(self, ts_df):
        fig = tsplot(ts_df, titles={"title": "Main", "subtitle": "Sub"}, backend="plotly")
        assert "Main" in fig.layout.title.text
        assert "Sub" in fig.layout.title.text

    def test_subtitle_mpl(self, ts_df):
        fig = tsplot(ts_df, titles={"title": "Main", "subtitle": "Sub"}, backend="matplotlib")
        ax = fig.axes[0]
        assert ax.get_title() == "Sub"
        plt.close(fig)


# ---------------------------------------------------------------------------
# Range selector (plotly)
# ---------------------------------------------------------------------------

class TestRangeSelector:
    def test_six_range_buttons(self, ts_df):
        fig = tsplot(ts_df, backend="plotly")
        rs = fig.layout.xaxis.rangeselector
        assert rs is not None
        assert len(rs.buttons) == 6

    def test_range_button_labels(self, ts_df):
        fig = tsplot(ts_df, backend="plotly")
        labels = [b.label for b in fig.layout.xaxis.rangeselector.buttons]
        for lbl in ["1M", "3M", "6M", "YTD", "1Y", "All"]:
            assert lbl in labels

    def test_dual_has_range_buttons(self, ts_df):
        fig = tsplot(ts_df, cols=["A"], yaxis2={"cols": ["B"]}, backend="plotly")
        rs = fig.layout.xaxis.rangeselector
        assert rs is not None
        assert len(rs.buttons) == 6


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
        fig = tsplot(ts_df, cols=["A"],
                     yaxis2={"cols": ["B"], "range": [0, 10]},
                     backend="plotly")
        assert list(fig.layout.yaxis2.range) == [0, 10]

    def test_yaxis2_range_mpl(self, ts_df):
        fig = tsplot(ts_df, cols=["A"],
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
