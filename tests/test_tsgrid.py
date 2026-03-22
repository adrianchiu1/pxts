"""Unit tests for pxts.plots.tsgrid: multi-panel time series grid.

Rendering is mocked via matplotlib.use("Agg") (non-interactive) and by passing
explicit backend= parameters, bypassing get_backend() entirely.
"""
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.figure
import plotly.graph_objects as go
import pandas as pd
import pytest

from pxts.plots import tsgrid
from pxts.exceptions import pxtsValidationError


# ---------------------------------------------------------------------------
# Helper to build panels dict
# ---------------------------------------------------------------------------

def _panels(ts_df, ts_df2):
    return {
        "Panel A": {"data": ts_df, "cols": {"Alpha": "A", "Beta": "B"}},
        "Panel B": {"data": ts_df2, "cols": {"Gamma": "C", "Delta": "D"}},
    }


# ---------------------------------------------------------------------------
# Basic rendering — matplotlib
# ---------------------------------------------------------------------------

class TestTsgridMpl:
    def test_basic_2x1(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=2, ncol=1, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_basic_1x2(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=1, ncol=2, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_fewer_panels_than_slots(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=2, ncol=2, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_single_panel(self, ts_df):
        panels = {"Only": {"data": ts_df}}
        fig = tsgrid(panels, nrow=1, ncol=1, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_no_cols_uses_all(self, ts_df, ts_df2):
        panels = {
            "P1": {"data": ts_df},
            "P2": {"data": ts_df2},
        }
        fig = tsgrid(panels, nrow=1, ncol=2, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_title_and_source(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=1, ncol=2,
                     title={"main": "Grid Title", "sub": "Subtitle"},
                     source=["LSEG"],
                     backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        texts = [t.get_text() for t in fig.texts]
        assert any("Source: LSEG" in t for t in texts)
        plt.close(fig)

    def test_labels_mode(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=1, ncol=2, labels=True,
                     backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)


# ---------------------------------------------------------------------------
# Basic rendering — plotly
# ---------------------------------------------------------------------------

class TestTsgridPlotly:
    def test_basic_2x1(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=2, ncol=1, backend="plotly")
        assert isinstance(fig, go.Figure)
        # 4 traces total (2 per panel)
        assert len(fig.data) == 4

    def test_basic_1x2(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=1, ncol=2, backend="plotly")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 4

    def test_single_panel(self, ts_df):
        panels = {"Only": {"data": ts_df}}
        fig = tsgrid(panels, nrow=1, ncol=1, backend="plotly")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # A and B

    def test_hovermode_x_unified(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=1, ncol=2, backend="plotly")
        assert fig.layout.hovermode == "x unified"

    def test_spike_lines_enabled(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=1, ncol=2, backend="plotly")
        assert fig.layout.xaxis.showspikes is True
        assert fig.layout.xaxis2.showspikes is True

    def test_accent_line_present(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=1, ncol=2, backend="plotly")
        accent_shapes = [s for s in fig.layout.shapes
                         if s.xref == "paper" and s.yref == "paper"]
        assert len(accent_shapes) >= 1

    def test_source_annotation(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=1, ncol=2,
                     source=["LSEG", "Bloomberg"], backend="plotly")
        annot_texts = [a.text for a in fig.layout.annotations]
        assert "Source: LSEG, Bloomberg" in annot_texts

    def test_title_plotly(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=1, ncol=2,
                     title={"main": "My Grid", "sub": "a subtitle"},
                     backend="plotly")
        assert "My Grid" in fig.layout.title.text

    def test_labels_mode(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=1, ncol=2, labels=True,
                     backend="plotly")
        assert fig.layout.showlegend is False

    def test_legend_deduplication(self, ts_df):
        """Same display name in multiple panels should only appear once in legend."""
        panels = {
            "P1": {"data": ts_df, "cols": {"Shared": "A"}},
            "P2": {"data": ts_df, "cols": {"Shared": "B"}},
        }
        fig = tsgrid(panels, nrow=1, ncol=2, backend="plotly")
        legend_traces = [t for t in fig.data if t.showlegend is not False]
        legend_names = [t.name for t in legend_traces]
        assert legend_names.count("Shared") == 1


# ---------------------------------------------------------------------------
# Color consistency
# ---------------------------------------------------------------------------

class TestColorConsistency:
    def test_same_display_name_same_color(self, ts_df):
        """Same display name across panels gets the same color."""
        panels = {
            "P1": {"data": ts_df, "cols": {"UK": "A"}},
            "P2": {"data": ts_df, "cols": {"UK": "B"}},
        }
        fig = tsgrid(panels, nrow=1, ncol=2, backend="plotly")
        colors = [t.line.color for t in fig.data if t.name == "UK"]
        assert len(colors) == 2
        assert colors[0] == colors[1]


# ---------------------------------------------------------------------------
# Unified x-axis range
# ---------------------------------------------------------------------------

class TestUnifiedXRange:
    def test_different_date_ranges_unified(self):
        """Panels with different date ranges get a unified x-axis."""
        dates1 = pd.date_range("2024-01-01", periods=5, freq="D")
        dates2 = pd.date_range("2024-01-03", periods=5, freq="D")
        df1 = pd.DataFrame({"X": [1, 2, 3, 4, 5]}, index=dates1)
        df2 = pd.DataFrame({"Y": [5, 4, 3, 2, 1]}, index=dates2)
        panels = {"P1": {"data": df1}, "P2": {"data": df2}}
        fig = tsgrid(panels, nrow=1, ncol=2, backend="plotly")
        # Both x-axes should have the same range
        r1 = fig.layout.xaxis.range
        r2 = fig.layout.xaxis2.range
        assert r1 == r2

    def test_explicit_xaxis_range_overrides(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=1, ncol=2,
                     xaxis={"range": ["2024-01-02", "2024-01-04"]},
                     backend="plotly")
        assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestTsgridValidation:
    def test_panels_not_dict_raises(self, ts_df):
        with pytest.raises(ValueError, match="panels must be dict"):
            tsgrid([ts_df], backend="matplotlib")

    def test_empty_panels_raises(self):
        with pytest.raises(ValueError, match="panels must not be empty"):
            tsgrid({}, backend="matplotlib")

    def test_too_many_panels_raises(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        with pytest.raises(ValueError, match="Too many panels"):
            tsgrid(panels, nrow=1, ncol=1, backend="matplotlib")

    def test_missing_data_key_raises(self, ts_df):
        with pytest.raises(ValueError, match="data"):
            tsgrid({"P1": {"cols": ["A"]}}, backend="matplotlib")

    def test_non_datetime_index_raises(self, bad_df):
        with pytest.raises(pxtsValidationError):
            tsgrid({"P1": {"data": bad_df}}, backend="matplotlib")

    def test_frequency_mismatch_raises(self):
        dates_d = pd.date_range("2024-01-01", periods=5, freq="D")
        dates_h = pd.date_range("2024-01-01", periods=5, freq="h")
        df_d = pd.DataFrame({"X": range(5)}, index=dates_d)
        df_h = pd.DataFrame({"Y": range(5)}, index=dates_h)
        with pytest.raises(ValueError, match="same data frequency"):
            tsgrid({"P1": {"data": df_d}, "P2": {"data": df_h}},
                   nrow=1, ncol=2, backend="matplotlib")

    def test_invalid_nrow_raises(self, ts_df):
        with pytest.raises(ValueError, match="nrow"):
            tsgrid({"P1": {"data": ts_df}}, nrow=0, backend="matplotlib")

    def test_invalid_ncol_raises(self, ts_df):
        with pytest.raises(ValueError, match="ncol"):
            tsgrid({"P1": {"data": ts_df}}, ncol=-1, backend="matplotlib")

    def test_bad_cols_spec_raises(self, ts_df):
        with pytest.raises(ValueError, match="cols must be"):
            tsgrid({"P1": {"data": ts_df, "cols": "A"}}, backend="matplotlib")

    def test_unknown_col_raises(self, ts_df):
        with pytest.raises(ValueError, match="NOPE"):
            tsgrid({"P1": {"data": ts_df, "cols": ["NOPE"]}},
                   backend="matplotlib")


# ---------------------------------------------------------------------------
# Y-axis per-panel auto-scaling
# ---------------------------------------------------------------------------

class TestYAxisScaling:
    def test_no_yaxis_range_auto_scales(self, ts_df, ts_df2):
        """Without yaxis range, each panel auto-scales independently."""
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=1, ncol=2, backend="plotly")
        # Just verify it doesn't crash; y-axis ranges will differ
        assert isinstance(fig, go.Figure)

    def test_explicit_yaxis_range_applies_to_all(self, ts_df, ts_df2):
        panels = _panels(ts_df, ts_df2)
        fig = tsgrid(panels, nrow=1, ncol=2,
                     yaxis={"range": [0, 20]}, backend="plotly")
        assert list(fig.layout.yaxis.range) == [0, 20]
        assert list(fig.layout.yaxis2.range) == [0, 20]
