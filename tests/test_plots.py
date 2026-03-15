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
