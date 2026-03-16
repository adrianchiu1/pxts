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
# Phase 6: Plotly date axis autoformatting and legend fixes
# ---------------------------------------------------------------------------

class TestTsplotPlotlyPhase6Fixes:
    def test_tickformatstops_set_when_no_date_format(self, ts_df):
        """date_format=None → x-axis uses tickformatstops (zoom-responsive), not a static tickformat."""
        fig = tsplot(ts_df, backend="plotly")
        xaxis = fig.layout.xaxis
        assert xaxis.tickformatstops, "tickformatstops must be set and non-empty"
        # Static tickformat should NOT be set when using tickformatstops
        assert not xaxis.tickformat, (
            f"tickformat should be empty when tickformatstops is used, got: {xaxis.tickformat!r}"
        )

    def test_tickformat_override_uses_static_string(self, ts_df):
        """date_format='%Y' → x-axis uses static tickformat string, not tickformatstops."""
        fig = tsplot(ts_df, date_format="%Y", backend="plotly")
        xaxis = fig.layout.xaxis
        assert xaxis.tickformat == "%Y", f"Expected '%Y', got {xaxis.tickformat!r}"
        assert not xaxis.tickformatstops, (
            "tickformatstops should not be set when date_format override is used"
        )

    def test_showlegend_true_in_layout(self, ts_df):
        """tsplot plotly → showlegend=True is set in the pxts template layout."""
        fig = tsplot(ts_df, backend="plotly")
        # showlegend=True is set in the pxts template layout (not directly on fig.layout)
        template_showlegend = fig.layout.template.layout.showlegend
        assert template_showlegend is True, (
            f"showlegend must be True in template layout, got: {template_showlegend!r}"
        )

    def test_year_annotation_present(self, ts_df):
        """tsplot plotly with auto date_format → year annotation added to figure."""
        fig = tsplot(ts_df, backend="plotly")
        annotation_texts = [a.text for a in fig.layout.annotations]
        # The year of the last index date should appear somewhere in annotations
        import pandas as pd
        expected_year = str(ts_df.index[-1].year)
        assert any(expected_year in t for t in annotation_texts), (
            f"Year annotation '{expected_year}' not found. Annotations: {annotation_texts}"
        )

    def test_year_annotation_absent_with_date_format_override(self, ts_df):
        """tsplot plotly with date_format override → no year annotation (subtitle may exist but not year)."""
        fig = tsplot(ts_df, date_format="%Y-%m-%d", backend="plotly")
        import pandas as pd
        expected_year = str(ts_df.index[-1].year)
        annotation_texts = [a.text for a in fig.layout.annotations]
        assert not any(
            t == expected_year for t in annotation_texts
        ), (
            f"Year annotation should not appear with date_format override. Found: {annotation_texts}"
        )

    def test_tickformatstops_has_four_tiers(self, ts_df):
        """tickformatstops must have exactly 4 tiers (decade, year, month, day)."""
        fig = tsplot(ts_df, backend="plotly")
        stops = fig.layout.xaxis.tickformatstops
        assert len(stops) == 4, f"Expected 4 tickformatstops tiers, got {len(stops)}"


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

    def test_showlegend_true_in_layout(self, ts_df):
        """tsplot_dual plotly → showlegend=True is set in the pxts template layout."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"], backend="plotly")
        # showlegend=True is set in the pxts template layout (not directly on fig.layout)
        template_showlegend = fig.layout.template.layout.showlegend
        assert template_showlegend is True, (
            f"showlegend must be True in template layout, got: {template_showlegend!r}"
        )

    def test_tickformatstops_set_when_no_date_format(self, ts_df):
        """tsplot_dual date_format=None → x-axis uses tickformatstops."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"], backend="plotly")
        assert fig.layout.xaxis.tickformatstops, "dual: tickformatstops must be set"


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


# ---------------------------------------------------------------------------
# Phase 7: Interactive Plotly time series charts
# ---------------------------------------------------------------------------

class TestPhase7RangeNav:
    """PLT7-01 / PLT7-02: Range selector buttons and rangeslider."""

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

    def test_tsplot_rangeslider_visible_by_default(self, ts_df):
        """tsplot plotly default -> rangeslider visible."""
        fig = tsplot(ts_df, backend="plotly")
        assert fig.layout.xaxis.rangeslider.visible is True

    def test_tsplot_rangeslider_opt_out(self, ts_df):
        """tsplot(rangeslider=False) -> rangeslider not visible."""
        fig = tsplot(ts_df, rangeslider=False, backend="plotly")
        assert fig.layout.xaxis.rangeslider.visible is False

    def test_tsplot_dual_has_range_buttons(self, ts_df):
        """tsplot_dual plotly default -> rangeselector with 6 buttons."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"], backend="plotly")
        rs = fig.layout.xaxis.rangeselector
        assert rs is not None, "dual: rangeselector missing"
        assert len(rs.buttons) == 6

    def test_tsplot_dual_rangeslider_opt_out(self, ts_df):
        """tsplot_dual(rangeslider=False) -> rangeslider not visible."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"],
                          rangeslider=False, backend="plotly")
        assert fig.layout.xaxis.rangeslider.visible is False

    def test_rangeslider_mpl_no_error(self, ts_df):
        """rangeslider param accepted by matplotlib backend without error."""
        import matplotlib.figure
        fig = tsplot(ts_df, rangeslider=False, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


class TestPhase7Theme:
    """PLT7-03 / PLT7-04: Visual polish and dark theme."""

    def test_plotly_template_has_tighter_margins(self, ts_df):
        """pxts Plotly template margin is set (not default None values)."""
        import plotly.io as pio
        template = pio.templates["pxts"]
        m = template.layout.margin
        # Any explicit margin means we set it (Plotly defaults are None)
        assert m.l is not None or m.r is not None, (
            "Template margin not set — whitespace fix not applied"
        )

    def test_theme_light_is_default(self, ts_df):
        """tsplot(backend='plotly') defaults to light (white) background."""
        fig = tsplot(ts_df, backend="plotly")
        # With theme='light', paper_bgcolor should NOT be the dark color
        assert fig.layout.paper_bgcolor != "#1a1a2e", "Default should not be dark"

    def test_theme_dark_sets_dark_background(self, ts_df):
        """tsplot(theme='dark') sets dark paper_bgcolor."""
        fig = tsplot(ts_df, theme="dark", backend="plotly")
        assert fig.layout.paper_bgcolor == "#1a1a2e", (
            f"dark theme paper_bgcolor: {fig.layout.paper_bgcolor}"
        )

    def test_theme_dark_dual(self, ts_df):
        """tsplot_dual(theme='dark') sets dark paper_bgcolor."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"],
                          theme="dark", backend="plotly")
        assert fig.layout.paper_bgcolor == "#1a1a2e"

    def test_theme_mpl_no_error(self, ts_df):
        """theme param accepted by matplotlib backend without error."""
        import matplotlib.figure
        fig = tsplot(ts_df, theme="dark", backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


class TestPhase7Annotations:
    """PLT7-05 / PLT7-06: Annotation parameter and add_annotation helper."""

    def test_tsplot_annotation_adds_text(self, ts_df):
        """tsplot(annotations=[{...}]) adds annotation text to Plotly figure."""
        from pxts.plots import tsplot, add_annotation
        ann = [{"x": "2024-01-03", "text": "Event"}]
        fig = tsplot(ts_df, annotations=ann, backend="plotly")
        texts = [a.text for a in fig.layout.annotations]
        assert any("Event" in t for t in texts), f"'Event' not in annotations: {texts}"

    def test_tsplot_annotation_showarrow_false(self, ts_df):
        """Annotations have showarrow=False (text only, no arrow)."""
        from pxts.plots import tsplot
        ann = [{"x": "2024-01-03", "text": "Peak"}]
        fig = tsplot(ts_df, annotations=ann, backend="plotly")
        # Find the non-year annotation
        user_anns = [a for a in fig.layout.annotations if "Peak" in (a.text or "")]
        assert len(user_anns) == 1, f"Expected 1 Peak annotation, got {user_anns}"
        assert user_anns[0].showarrow is False

    def test_tsplot_annotation_y_auto_lookup(self, ts_df):
        """Annotation without y key auto-looks up y from nearest data point."""
        from pxts.plots import tsplot
        # 2024-01-03 is index position 2, A=3.0
        ann = [{"x": "2024-01-03", "text": "AutoY"}]
        fig = tsplot(ts_df, cols=["A"], annotations=ann, backend="plotly")
        user_anns = [a for a in fig.layout.annotations if "AutoY" in (a.text or "")]
        assert len(user_anns) == 1
        # y should be auto-looked up as 3.0 (A value at 2024-01-03)
        assert abs(user_anns[0].y - 3.0) < 0.01, f"Expected y~3.0, got {user_anns[0].y}"

    def test_tsplot_dual_annotation_with_col(self, ts_df):
        """tsplot_dual annotation with col key adds annotation to correct axis."""
        from pxts.plots import tsplot_dual
        ann = [{"x": "2024-01-03", "text": "Dual", "col": "A"}]
        fig = tsplot_dual(ts_df, left=["A"], right=["B"],
                          annotations=ann, backend="plotly")
        texts = [a.text for a in fig.layout.annotations]
        assert any("Dual" in t for t in texts), f"'Dual' not found in {texts}"

    def test_add_annotation_adds_to_figure(self, ts_df):
        """add_annotation(fig, x, text=...) adds annotation in-place to existing figure."""
        from pxts.plots import tsplot, add_annotation
        fig = tsplot(ts_df, backend="plotly")
        count_before = len(fig.layout.annotations)
        add_annotation(fig, "2024-01-03", text="PostCall")
        count_after = len(fig.layout.annotations)
        assert count_after == count_before + 1, (
            f"Expected {count_before+1} annotations, got {count_after}"
        )
        texts = [a.text for a in fig.layout.annotations]
        assert any("PostCall" in t for t in texts)

    def test_add_annotation_with_y(self, ts_df):
        """add_annotation(fig, x, y=2.5, text=...) uses provided y."""
        from pxts.plots import tsplot, add_annotation
        fig = tsplot(ts_df, backend="plotly")
        add_annotation(fig, "2024-01-02", y=2.5, text="Fixed")
        user_anns = [a for a in fig.layout.annotations if "Fixed" in (a.text or "")]
        assert len(user_anns) == 1
        assert abs(user_anns[0].y - 2.5) < 0.01

    def test_add_annotation_exported_from_pxts(self):
        """add_annotation is importable from pxts top-level package."""
        from pxts import add_annotation
        assert callable(add_annotation)

    def test_annotations_wrong_type_raises(self, ts_df):
        """annotations='bad' raises ValueError mentioning 'annotations'."""
        with pytest.raises(ValueError, match="annotations"):
            tsplot(ts_df, annotations="bad", backend="matplotlib")

    def test_annotations_missing_x_raises(self, ts_df):
        """annotations=[{'text': 'x'}] (no x key) raises ValueError."""
        with pytest.raises(ValueError, match="annotations"):
            tsplot(ts_df, annotations=[{"text": "no x key"}], backend="matplotlib")

    def test_annotations_missing_text_raises(self, ts_df):
        """annotations=[{'x': date}] (no text key) raises ValueError."""
        with pytest.raises(ValueError, match="annotations"):
            tsplot(ts_df, annotations=[{"x": "2024-01-01"}], backend="matplotlib")


class TestPhase7DualAxisLabels:
    """PLT7-07: left_label and right_label axis title parameters."""

    def test_left_label_sets_yaxis_title(self, ts_df):
        """left_label='Energy' sets primary y-axis title text."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"],
                          left_label="Energy", backend="plotly")
        yaxis_title = fig.layout.yaxis.title.text
        assert yaxis_title == "Energy", f"Expected 'Energy', got {yaxis_title!r}"

    def test_left_label_title_colored_left_color(self, ts_df):
        """left_label title font color matches LEFT_COLOR."""
        from pxts.plots import LEFT_COLOR
        fig = tsplot_dual(ts_df, left=["A"], right=["B"],
                          left_label="Energy", backend="plotly")
        title_color = fig.layout.yaxis.title.font.color
        assert title_color == LEFT_COLOR, (
            f"Expected {LEFT_COLOR}, got {title_color!r}"
        )

    def test_right_label_sets_yaxis2_title(self, ts_df):
        """right_label='Steam' sets secondary y-axis title text."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"],
                          right_label="Steam", backend="plotly")
        yaxis2_title = fig.layout.yaxis2.title.text
        assert yaxis2_title == "Steam", f"Expected 'Steam', got {yaxis2_title!r}"

    def test_right_label_title_colored_right_color(self, ts_df):
        """right_label title font color matches RIGHT_COLOR."""
        from pxts.plots import RIGHT_COLOR
        fig = tsplot_dual(ts_df, left=["A"], right=["B"],
                          right_label="Steam", backend="plotly")
        title_color = fig.layout.yaxis2.title.font.color
        assert title_color == RIGHT_COLOR, (
            f"Expected {RIGHT_COLOR}, got {title_color!r}"
        )

    def test_no_labels_means_no_axis_title(self, ts_df):
        """tsplot_dual with no left_label/right_label -> no y-axis title set."""
        fig = tsplot_dual(ts_df, left=["A"], right=["B"], backend="plotly")
        # When None, Plotly leaves title.text as None or empty
        assert not fig.layout.yaxis.title.text, (
            f"Unexpected yaxis title: {fig.layout.yaxis.title.text!r}"
        )

    def test_left_right_labels_mpl_no_error(self, ts_df):
        """left_label/right_label accepted by matplotlib backend without error."""
        import matplotlib.figure
        fig = tsplot_dual(ts_df, left=["A"], right=["B"],
                          left_label="LHS", right_label="RHS",
                          backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)
