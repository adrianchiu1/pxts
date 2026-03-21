"""Unit tests for pxts.plots: tsplot and tsplot_dual, both matplotlib and plotly backends.

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

from pxts.plots import tsplot, tsplot_dual
from pxts.exceptions import pxtsValidationError


# ---------------------------------------------------------------------------
# tsplot — matplotlib backend
# ---------------------------------------------------------------------------

class TestTsplotMatplotlib:
    def test_default_cols_returns_figure(self, ts_df):
        """Default cols (None) → plots all columns, returns matplotlib Figure."""
        fig = tsplot(ts_df, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_explicit_cols_returns_figure(self, ts_df):
        """Explicit cols=["A"] → returns Figure."""
        fig = tsplot(ts_df, cols=["A"], backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_title(self, ts_df):
        """title rendered without error."""
        fig = tsplot(ts_df, title="My Title", backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_hlines_as_list(self, ts_df):
        """hlines as list → horizontal lines drawn without error."""
        fig = tsplot(ts_df, hlines=[1.0, 3.0], backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_hlines_as_dict(self, ts_df):
        """hlines as dict → horizontal lines with labels drawn without error."""
        fig = tsplot(ts_df, hlines={"low": 1.0, "high": 4.0}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_vlines_as_list(self, ts_df):
        """vlines as list → vertical lines drawn without error."""
        vline_date = pd.Timestamp("2024-01-03")
        fig = tsplot(ts_df, vlines=[vline_date], backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_unknown_col_raises_value_error(self, ts_df):
        """Unknown col → raises ValueError containing column name."""
        with pytest.raises(ValueError, match="UNKNOWN"):
            tsplot(ts_df, cols=["UNKNOWN"], backend="matplotlib")


# ---------------------------------------------------------------------------
# tsplot — plotly backend
# ---------------------------------------------------------------------------

class TestTsplotPlotly:
    def test_default_cols_returns_figure(self, ts_df):
        """Default cols → returns plotly Figure with one trace per column."""
        fig = tsplot(ts_df, backend="plotly")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == len(ts_df.columns)

    def test_explicit_cols_returns_figure(self, ts_df):
        """Explicit cols=["A"] → returns plotly Figure with one trace."""
        fig = tsplot(ts_df, cols=["A"], backend="plotly")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1

    def test_title(self, ts_df):
        """title -> Figure has title set."""
        fig = tsplot(ts_df, title="My Title", backend="plotly")
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == "My Title"

    def test_hlines_as_list(self, ts_df):
        """hlines as list → Figure has shape/annotation added."""
        fig = tsplot(ts_df, hlines=[1.0, 3.0], backend="plotly")
        assert isinstance(fig, go.Figure)
        # Two hlines should produce two shapes
        assert len(fig.layout.shapes) == 2

    def test_unknown_col_raises_value_error(self, ts_df):
        """Unknown col → raises ValueError."""
        with pytest.raises(ValueError, match="UNKNOWN"):
            tsplot(ts_df, cols=["UNKNOWN"], backend="plotly")

    def test_showlegend_true_in_layout(self, ts_df):
        """tsplot plotly → showlegend=True is set in the pxts template layout."""
        fig = tsplot(ts_df, backend="plotly")
        template_showlegend = fig.layout.template.layout.showlegend
        assert template_showlegend is True


# ---------------------------------------------------------------------------
# tsplot_dual — matplotlib backend
# ---------------------------------------------------------------------------

class TestTsplotDualMatplotlib:
    def test_left_and_right_returns_figure(self, ts_df):
        """left=["A"], right=["B"] → returns Figure, no error."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"], backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_title(self, ts_df):
        """title rendered without error."""
        fig = tsplot_dual(
            ts_df, left=["A"], right=["B"],
            title="Dual Title",
            backend="matplotlib",
        )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ---------------------------------------------------------------------------
# tsplot_dual — plotly backend
# ---------------------------------------------------------------------------

class TestTsplotDualPlotly:
    def test_left_and_right_returns_figure(self, ts_df):
        """left=["A"], right=["B"] → returns plotly Figure with two traces."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"], backend="plotly")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2

    def test_showlegend_true_in_layout(self, ts_df):
        """tsplot_dual plotly → showlegend=True is set in the pxts template layout."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"], backend="plotly")
        template_showlegend = fig.layout.template.layout.showlegend
        assert template_showlegend is True


# ---------------------------------------------------------------------------
# Validation tests (backend-agnostic — use matplotlib for simplicity)
# ---------------------------------------------------------------------------

class TestValidation:
    def test_non_datetime_index_raises(self, bad_df):
        """Non-DatetimeIndex df → raises pxtsValidationError."""
        with pytest.raises(pxtsValidationError):
            tsplot(bad_df, backend="matplotlib")

    def test_unknown_col_in_cols_raises(self, ts_df):
        """Unknown column in cols → raises ValueError."""
        with pytest.raises(ValueError, match="NOPE"):
            tsplot(ts_df, cols=["NOPE"], backend="matplotlib")

    def test_unknown_col_in_left_raises(self, ts_df):
        """Unknown column in left → raises ValueError."""
        with pytest.raises(ValueError, match="NOPE"):
            tsplot_dual(ts_df, left=["NOPE"], right=["B"], backend="matplotlib")


# ---------------------------------------------------------------------------
# FIX-05: parameter type validation in tsplot and tsplot_dual
# ---------------------------------------------------------------------------

class TestParameterTypeValidation:
    def test_hlines_scalar_float(self, ts_df):
        """tsplot(hlines=42.0) → succeeds (scalar normalized to [42.0])."""
        fig = tsplot(ts_df, hlines=42.0, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_hlines_scalar_int(self, ts_df):
        """tsplot(hlines=0) → succeeds (int zero normalized to [0])."""
        fig = tsplot(ts_df, hlines=0, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_hlines_bool_raises(self, ts_df):
        """tsplot(hlines=True) → ValueError (bool excluded from scalar normalization)."""
        with pytest.raises(ValueError, match="hlines"):
            tsplot(ts_df, hlines=True, backend="matplotlib")

    def test_tsplot_title_wrong_type_raises(self, ts_df):
        """tsplot(title=123) → ValueError mentioning 'title'."""
        with pytest.raises(ValueError, match="title"):
            tsplot(ts_df, title=123, backend="matplotlib")

    def test_tsplot_dual_vlines_wrong_type_raises(self, ts_df):
        """tsplot_dual(vlines='bad') → ValueError mentioning 'vlines'."""
        with pytest.raises(ValueError, match="vlines"):
            tsplot_dual(ts_df, left=["A"], right=["B"], vlines="bad", backend="matplotlib")

    def test_tsplot_valid_params_no_error(self, ts_df):
        """tsplot(hlines=None, title='OK') → no error."""
        fig = tsplot(ts_df, hlines=None, title="OK", backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_tsplot_hlines_list_valid(self, ts_df):
        """tsplot(hlines=[1.0, 2.0]) → no error."""
        fig = tsplot(ts_df, hlines=[1.0, 2.0], backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_tsplot_title_none_valid(self, ts_df):
        """tsplot(title=None) → no error (None is valid)."""
        fig = tsplot(ts_df, title=None, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ---------------------------------------------------------------------------
# QUICK-4: ylim / xlim / ylim_lhs / ylim_rhs axis limit parameters
# ---------------------------------------------------------------------------

class TestAxisLimits:
    # --- tsplot ylim/xlim matplotlib ---
    def test_tsplot_ylim_list_mpl(self, ts_df):
        """tsplot(ylim=[0,10], backend='matplotlib') returns Figure with y-axis restricted."""
        fig = tsplot(ts_df, ylim=[0, 10], backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        ax = fig.axes[0]
        lo, hi = ax.get_ylim()
        assert lo == pytest.approx(0)
        assert hi == pytest.approx(10)
        plt.close(fig)

    def test_tsplot_ylim_tuple_mpl(self, ts_df):
        """tsplot(ylim=(0,10)) tuple also accepted."""
        fig = tsplot(ts_df, ylim=(0, 10), backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_tsplot_xlim_mpl(self, ts_df):
        """tsplot(xlim=[date1, date2], backend='matplotlib') returns Figure."""
        fig = tsplot(
            ts_df,
            xlim=[pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-05")],
            backend="matplotlib",
        )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_tsplot_ylim_none_mpl(self, ts_df):
        """tsplot(ylim=None) returns Figure without error (default behaviour)."""
        fig = tsplot(ts_df, ylim=None, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    # --- tsplot ylim/xlim plotly ---
    def test_tsplot_ylim_plotly(self, ts_df):
        """tsplot(ylim=[0,10], backend='plotly') returns Figure with yaxis.range."""
        fig = tsplot(ts_df, ylim=[0, 10], backend="plotly")
        assert isinstance(fig, go.Figure)
        assert list(fig.layout.yaxis.range) == [0, 10]

    def test_tsplot_xlim_plotly(self, ts_df):
        """tsplot(xlim=[date1, date2], backend='plotly') returns plotly Figure."""
        fig = tsplot(
            ts_df,
            xlim=[pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-05")],
            backend="plotly",
        )
        assert isinstance(fig, go.Figure)

    # --- tsplot_dual ylim_lhs / ylim_rhs / xlim ---
    def test_tsplot_dual_ylim_lhs_mpl(self, ts_df):
        """tsplot_dual(ylim_lhs=[0,5]) returns Figure."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"], ylim_lhs=[0, 5], backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_tsplot_dual_ylim_rhs_mpl(self, ts_df):
        """tsplot_dual(ylim_rhs=[0,5]) returns Figure."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"], ylim_rhs=[0, 5], backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_tsplot_dual_xlim_mpl(self, ts_df):
        """tsplot_dual(xlim=[date1, date2]) returns Figure."""
        fig = tsplot_dual(
            ts_df,
            left=["A"], right=["B"],
            xlim=[pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-05")],
            backend="matplotlib",
        )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_tsplot_dual_ylim_lhs_plotly(self, ts_df):
        """tsplot_dual(ylim_lhs=[0,5], backend='plotly') returns go.Figure."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"], ylim_lhs=[0, 5], backend="plotly")
        assert isinstance(fig, go.Figure)

    # --- validation errors ---
    def test_tsplot_ylim_wrong_type_raises(self, ts_df):
        """tsplot(ylim='bad') raises ValueError mentioning 'ylim'."""
        with pytest.raises(ValueError, match="ylim"):
            tsplot(ts_df, ylim="bad", backend="matplotlib")

    def test_tsplot_ylim_wrong_length_raises(self, ts_df):
        """tsplot(ylim=[1,2,3]) raises ValueError mentioning 'ylim'."""
        with pytest.raises(ValueError, match="ylim"):
            tsplot(ts_df, ylim=[1, 2, 3], backend="matplotlib")

    def test_tsplot_xlim_not_date_raises(self, ts_df):
        """tsplot(xlim=[1, 2]) raises ValueError mentioning 'xlim' (not date-like)."""
        with pytest.raises(ValueError, match="xlim"):
            tsplot(ts_df, xlim=[1, 2], backend="matplotlib")

    def test_tsplot_dual_ylim_lhs_wrong_type_raises(self, ts_df):
        """tsplot_dual(ylim_lhs=42) raises ValueError mentioning 'ylim_lhs'."""
        with pytest.raises(ValueError, match="ylim_lhs"):
            tsplot_dual(ts_df, left=["A"], right=["B"], ylim_lhs=42, backend="matplotlib")


# ---------------------------------------------------------------------------
# Range selector buttons (plotly)
# ---------------------------------------------------------------------------

class TestRangeSelector:
    def test_tsplot_has_six_range_buttons(self, ts_df):
        """tsplot plotly default -> rangeselector with 6 buttons."""
        fig = tsplot(ts_df, backend="plotly")
        rs = fig.layout.xaxis.rangeselector
        assert rs is not None, "rangeselector missing"
        assert len(rs.buttons) == 6, f"expected 6 buttons, got {len(rs.buttons)}"

    def test_tsplot_range_button_labels(self, ts_df):
        """tsplot plotly -> buttons labeled 1M, 3M, 6M, YTD, 1Y, All."""
        fig = tsplot(ts_df, backend="plotly")
        labels = [b.label for b in fig.layout.xaxis.rangeselector.buttons]
        for lbl in ["1M", "3M", "6M", "YTD", "1Y", "All"]:
            assert lbl in labels, f"button '{lbl}' missing from {labels}"

    def test_tsplot_dual_has_range_buttons(self, ts_df):
        """tsplot_dual plotly default -> rangeselector with 6 buttons."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"], backend="plotly")
        rs = fig.layout.xaxis.rangeselector
        assert rs is not None, "dual: rangeselector missing"
        assert len(rs.buttons) == 6


# ---------------------------------------------------------------------------
# Plotly template
# ---------------------------------------------------------------------------

class TestPlotlyTemplate:
    def test_plotly_template_has_tighter_margins(self, ts_df):
        """pxts Plotly template margin is set (not default None values)."""
        import plotly.io as pio
        template = pio.templates["pxts"]
        m = template.layout.margin
        assert m.l is not None or m.r is not None, (
            "Template margin not set — whitespace fix not applied"
        )


# ---------------------------------------------------------------------------
# Dual axis labels (plotly)
# ---------------------------------------------------------------------------

class TestDualAxisLabels:
    def test_left_label_sets_yaxis_title(self, ts_df):
        """left_label='Energy' sets primary y-axis title text."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"],
                          left_label="Energy", backend="plotly")
        yaxis_title = fig.layout.yaxis.title.text
        assert yaxis_title == "Energy"

    def test_left_label_title_colored_left_color(self, ts_df):
        """left_label title font color matches LEFT_COLOR."""
        from pxts.plots import LEFT_COLOR
        fig = tsplot_dual(ts_df, left=["A"], right=["B"],
                          left_label="Energy", backend="plotly")
        title_color = fig.layout.yaxis.title.font.color
        assert title_color == LEFT_COLOR

    def test_right_label_sets_yaxis2_title(self, ts_df):
        """right_label='Steam' sets secondary y-axis title text."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"],
                          right_label="Steam", backend="plotly")
        yaxis2_title = fig.layout.yaxis2.title.text
        assert yaxis2_title == "Steam"

    def test_right_label_title_colored_right_color(self, ts_df):
        """right_label title font color matches RIGHT_COLOR."""
        from pxts.plots import RIGHT_COLOR
        fig = tsplot_dual(ts_df, left=["A"], right=["B"],
                          right_label="Steam", backend="plotly")
        title_color = fig.layout.yaxis2.title.font.color
        assert title_color == RIGHT_COLOR

    def test_no_labels_means_no_axis_title(self, ts_df):
        """tsplot_dual with no left_label/right_label -> no y-axis title set."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"], backend="plotly")
        assert not fig.layout.yaxis.title.text

    def test_left_right_labels_mpl_no_error(self, ts_df):
        """left_label/right_label accepted by matplotlib backend without error."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"],
                          left_label="LHS", right_label="RHS",
                          backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)
