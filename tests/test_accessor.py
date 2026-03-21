"""Tests for pxts.accessor — TsAccessor delegation and error protocol.

Tests confirm that each .ts method delegates to the correct standalone function
and that the pandas accessor protocol (AttributeError on bad index) is respected.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import pytest
import pxts.accessor  # Side effect: registers .ts accessor globally


class TestAccessorAvailability:
    """The .ts accessor is available on DataFrames with a DatetimeIndex."""

    def test_accessor_available(self, ts_df):
        from pxts.accessor import TsAccessor
        assert isinstance(ts_df.ts, TsAccessor)

    def test_accessor_attr_present(self, ts_df):
        assert hasattr(ts_df, "ts")


class TestDelegation:
    """Each TsAccessor method returns the same result as the standalone function."""

    def test_set_tz_delegates(self, ts_df):
        result = ts_df.ts.set_tz("UTC")
        assert isinstance(result, pd.DataFrame)
        assert result.index.tz is not None

    def test_to_dense_delegates(self, ts_df):
        result = ts_df.ts.to_dense("D")
        assert isinstance(result, pd.DataFrame)
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_infer_freq_delegates(self, ts_df):
        result = ts_df.ts.infer_freq()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_write_ts_delegates(self, ts_df, tmp_path):
        path = tmp_path / "out.csv"
        ts_df.ts.write_ts(path)
        assert path.exists()

    def test_plot_delegates(self, ts_df):
        import matplotlib.figure
        fig = ts_df.ts.plot(backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close("all")

    def test_plot_dual_via_yaxis2(self, ts_df):
        """plot(yaxis2=...) triggers dual-axis mode."""
        import matplotlib.figure
        fig = ts_df.ts.plot(yaxis={"cols": ["A"]}, yaxis2={"cols": ["B"]}, backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        assert len(fig.axes) == 2
        plt.close("all")

    def test_plot_dual_no_longer_exists(self, ts_df):
        """plot_dual() method has been removed."""
        assert not hasattr(ts_df.ts, "plot_dual")

    def test_plot_with_new_params(self, ts_df):
        """New parameters (dimension, title, annotations, source) are accepted."""
        import matplotlib.figure
        fig = ts_df.ts.plot(
            title={"main": "Test", "sub": "Subtitle"},
            dimension={"width": 800},
            annotations={"hline": [2.0]},
            source=["Test Source"],
            backend="matplotlib",
        )
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close("all")


class TestErrorProtocol:
    """Pandas accessor contract: AttributeError on non-DatetimeIndex DataFrame."""

    def test_bad_df_raises_attribute_error(self, bad_df):
        with pytest.raises(AttributeError, match="DatetimeIndex"):
            _ = bad_df.ts

    def test_bad_df_raises_attribute_error_not_validation(self, bad_df):
        """Must raise AttributeError, not pxtsValidationError, per pandas contract."""
        from pxts.exceptions import pxtsValidationError
        with pytest.raises(AttributeError):
            _ = bad_df.ts
        try:
            _ = bad_df.ts
        except AttributeError as exc:
            assert not isinstance(exc, pxtsValidationError)
