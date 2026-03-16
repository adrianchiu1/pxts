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

    def test_title_and_subtitle(self, ts_df):
        """title and subtitle rendered without error."""
        fig = tsplot(ts_df, title="My Title", subtitle="My Subtitle", backend="matplotlib")
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
        import pandas as pd
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

    def test_title_and_subtitle(self, ts_df):
        """title and subtitle → Figure has title set."""
        fig = tsplot(ts_df, title="My Title", subtitle="My Subtitle", backend="plotly")
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


# ---------------------------------------------------------------------------
# tsplot_dual — matplotlib backend
# ---------------------------------------------------------------------------

class TestTsplotDualMatplotlib:
    def test_left_and_right_returns_figure(self, ts_df):
        """left=["A"], right=["B"] → returns Figure, no error."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"], backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_title_and_subtitle(self, ts_df):
        """title and subtitle rendered without error."""
        fig = tsplot_dual(
            ts_df, left=["A"], right=["B"],
            title="Dual Title", subtitle="Dual Sub",
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
# DEP-02: once-per-session adjustText missing warning
# ---------------------------------------------------------------------------

class TestAdjustTextWarning:
    def test_adjusttext_warning_emitted_once(self, ts_df):
        """First call with labels=True when adjustText absent → UserWarning with 'adjustText'.
        Second call → no warning (module-level flag prevents repeat).
        """
        import pxts.plots as plots_module
        import unittest.mock as mock

        # Reset the module-level flag so we start fresh
        plots_module._ADJUSTTEXT_WARNED = False

        # Patch adjustText import inside _add_mpl_end_labels to simulate absence
        with mock.patch.dict("sys.modules", {"adjustText": None}):
            # First call — should emit exactly one UserWarning mentioning adjustText
            with pytest.warns(UserWarning, match="adjustText") as warning_list:
                fig1 = tsplot(ts_df, labels=True, backend="matplotlib")
            plt.close(fig1)
            assert len(warning_list) == 1

            # Second call — flag is now True, no warning should be emitted
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("error")  # Any warning would become an error
                fig2 = tsplot(ts_df, labels=True, backend="matplotlib")
            plt.close(fig2)

        # Restore flag to False for other tests
        plots_module._ADJUSTTEXT_WARNED = False


# ---------------------------------------------------------------------------
# FIX-05: parameter type validation in tsplot and tsplot_dual
# ---------------------------------------------------------------------------

class TestParameterTypeValidation:
    def test_hlines_scalar_float(self, ts_df):
        """tsplot(hlines=42.0) → succeeds and returns a figure (scalar normalized to [42.0])."""
        fig = tsplot(ts_df, hlines=42.0, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_hlines_scalar_int(self, ts_df):
        """tsplot(hlines=0) → succeeds and returns a figure (int zero normalized to [0])."""
        fig = tsplot(ts_df, hlines=0, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_hlines_bool_raises(self, ts_df):
        """tsplot(hlines=True) → ValueError mentioning 'hlines' (bool excluded from scalar normalization)."""
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

    def test_tsplot_subtitle_wrong_type_raises(self, ts_df):
        """tsplot(subtitle=['a']) → ValueError mentioning 'subtitle'."""
        with pytest.raises(ValueError, match="subtitle"):
            tsplot(ts_df, subtitle=["a"], backend="matplotlib")

    def test_tsplot_date_format_wrong_type_raises(self, ts_df):
        """tsplot(date_format=42) → ValueError mentioning 'date_format'."""
        with pytest.raises(ValueError, match="date_format"):
            tsplot(ts_df, date_format=42, backend="matplotlib")


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
# PLOTLY-01 / PLOTLY-02: _PLOTLY_TICKFORMATSTOPS — zoom-responsive date axis
# ---------------------------------------------------------------------------

class TestPlotlyTickformatstops:
    """Tests for _PLOTLY_TICKFORMATSTOPS constant and its integration into tsplot/tsplot_dual."""

    def test_constant_has_four_tiers(self):
        """_PLOTLY_TICKFORMATSTOPS must have exactly 4 zoom tiers."""
        from pxts.plots import _PLOTLY_TICKFORMATSTOPS
        assert len(_PLOTLY_TICKFORMATSTOPS) == 4

    def test_constant_tiers_have_required_keys(self):
        """Each tier must have dtickrange and value keys."""
        from pxts.plots import _PLOTLY_TICKFORMATSTOPS
        for tier in _PLOTLY_TICKFORMATSTOPS:
            assert "dtickrange" in tier
            assert "value" in tier

    def test_tsplot_plotly_uses_tickformatstops_when_no_date_format(self, ts_df):
        """tsplot plotly backend uses tickformatstops (not tickformat) by default."""
        fig = tsplot(ts_df, backend="plotly")
        assert fig.layout.xaxis.tickformatstops, "tickformatstops should be present"
        assert not fig.layout.xaxis.tickformat, "tickformat should be absent"

    def test_tsplot_plotly_uses_tickformat_when_date_format_given(self, ts_df):
        """tsplot plotly backend uses static tickformat when date_format is provided."""
        fig = tsplot(ts_df, date_format="%Y", backend="plotly")
        assert fig.layout.xaxis.tickformat == "%Y"
        assert not fig.layout.xaxis.tickformatstops, "tickformatstops should be absent"

    def test_tsplot_dual_plotly_uses_tickformatstops(self, ts_df):
        """tsplot_dual plotly backend uses tickformatstops by default."""
        cols = list(ts_df.columns)
        fig = tsplot_dual(ts_df, left=[cols[0]], right=[cols[1]], backend="plotly")
        assert fig.layout.xaxis.tickformatstops, "dual: tickformatstops should be present"
