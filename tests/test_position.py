"""Unit tests for pxts.position: posplot and its data helpers."""
import warnings
from unittest.mock import patch

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — MUST be before any pyplot import

import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

import pxts  # noqa: F401 — registers the .ts accessor
from pxts.exceptions import pxtsValidationError
from pxts.position import (
    _CANDLE_WIDTH,
    _VCANDLE_MAX,
    _candle_width_fracs,
    _position_trades,
    posplot,
)

OHLC = {"open": "open", "high": "high", "low": "low", "close": "close"}


@pytest.fixture(scope="module")
def pos_df():
    """40 business days of OHLCV with a signed position that crosses zero."""
    idx = pd.bdate_range("2024-01-01", periods=40)
    rng = np.random.default_rng(0)
    close = 100 + np.cumsum(rng.normal(0, 1, 40))
    open_ = close + rng.normal(0, 0.5, 40)
    position = np.repeat([0, 50, 100, 50, -25, -75, 0, 25], 5).astype(float)
    return pd.DataFrame({
        "open": open_,
        "high": np.maximum(open_, close) + 0.5,
        "low": np.minimum(open_, close) - 0.5,
        "close": close,
        "volume": rng.integers(1_000, 10_000, 40).astype(float),
        "position": position,
    }, index=idx)


def _series(values):
    return pd.Series(values, index=pd.date_range("2024-01-01", periods=len(values)),
                     dtype=float)


def _trace(fig, name):
    return next(t for t in fig.data if t.name == name)


# ---------------------------------------------------------------------------
# Trades and average entry price
# ---------------------------------------------------------------------------

class TestPositionTrades:
    def test_trades_are_position_changes(self):
        trades, _ = _position_trades(_series([10, 11, 12, 13]), _series([0, 50, 50, 20]))
        assert list(trades["change"]) == [50, -30]
        assert list(trades["position"]) == [50, 20]
        assert list(trades["price"]) == [11, 13]

    def test_adding_averages_entry_by_size(self):
        _, entry = _position_trades(_series([10, 20]), _series([50, 100]))
        assert entry.iloc[0] == 10
        assert entry.iloc[1] == pytest.approx(15)  # 50 @ 10 and 50 @ 20

    def test_reducing_keeps_entry(self):
        _, entry = _position_trades(_series([10, 20]), _series([100, 40]))
        assert list(entry) == [10, 10]

    def test_flat_has_no_entry(self):
        _, entry = _position_trades(_series([10, 20, 30]), _series([50, 0, 0]))
        assert entry.iloc[0] == 10
        assert entry.iloc[1:].isna().all()

    def test_crossing_zero_resets_entry(self):
        _, entry = _position_trades(_series([10, 20, 30]), _series([50, -50, -50]))
        assert list(entry) == [10, 20, 20]

    def test_adding_to_short_averages_entry(self):
        _, entry = _position_trades(_series([10, 20]), _series([-25, -100]))
        assert entry.iloc[1] == pytest.approx((25 * 10 + 75 * 20) / 100)

    def test_no_trades(self):
        trades, entry = _position_trades(_series([10, 11]), _series([0, 0]))
        assert trades.empty
        assert entry.isna().all()


# ---------------------------------------------------------------------------
# Candle widths
# ---------------------------------------------------------------------------

class TestCandleWidths:
    def test_plain_candles_are_constant(self):
        widths = _candle_width_fracs([1, 100, 10_000], "candle")
        assert np.allclose(widths, _CANDLE_WIDTH)

    def test_volume_candles_grow_with_volume(self):
        widths = _candle_width_fracs([100, 200, 400, 800], "vcandle")
        assert np.all(np.diff(widths) > 0)
        assert widths.max() <= _VCANDLE_MAX
        assert widths.min() > 0

    def test_volume_spike_is_capped(self):
        volume = [100] * 99 + [1_000_000]
        widths = _candle_width_fracs(volume, "vcandle")
        assert widths[-1] == pytest.approx(_VCANDLE_MAX)
        # The spike does not squash ordinary days into slivers.
        assert widths[0] == pytest.approx(_VCANDLE_MAX)

    def test_zero_volume_falls_back_to_constant(self):
        widths = _candle_width_fracs([0, 0, 0], "vcandle")
        assert np.allclose(widths, _CANDLE_WIDTH)


# ---------------------------------------------------------------------------
# Plotly
# ---------------------------------------------------------------------------

class TestPosplotPlotly:
    def test_line_default(self, pos_df):
        fig = posplot(pos_df, backend="plotly")
        assert isinstance(fig, go.Figure)
        names = [t.name for t in fig.data]
        for expected in ("Close", "Long", "Short", "Position", "Buy", "Sell", "Average entry"):
            assert expected in names

    def test_trades_off_drops_trade_layers(self, pos_df):
        fig = posplot(pos_df, trades=False, backend="plotly")
        names = [t.name for t in fig.data]
        assert "Buy" not in names and "Average entry" not in names

    def test_buy_and_sell_counts(self, pos_df):
        fig = posplot(pos_df, backend="plotly")
        # position path: 0, 50, 100, 50, -25, -75, 0, 25
        assert len(_trace(fig, "Buy").x) == 4
        assert len(_trace(fig, "Sell").x) == 3

    def test_candle_bodies_have_constant_width(self, pos_df):
        fig = posplot(pos_df, price=OHLC, kind="candle", backend="plotly")
        body = _trace(fig, "Price")
        assert body.type == "bar"
        assert len(set(np.round(body.width, 6))) == 1

    def test_vcandle_widths_follow_volume(self, pos_df):
        fig = posplot(pos_df, price=OHLC, volume="volume", kind="vcandle", backend="plotly")
        widths = np.asarray(_trace(fig, "Price").width)
        assert len(set(np.round(widths, 6))) > 1
        order = np.argsort(pos_df["volume"].to_numpy())
        assert np.all(np.diff(widths[order]) >= -1e-9)

    def test_candle_body_spans_open_to_close(self, pos_df):
        fig = posplot(pos_df, price=OHLC, kind="candle", backend="plotly")
        body = _trace(fig, "Price")
        assert np.allclose(body.base, np.minimum(pos_df["open"], pos_df["close"]))

    def test_position_axis_is_fixed_and_symmetric(self, pos_df):
        fig = posplot(pos_df, backend="plotly")
        lo, hi = fig.layout.yaxis3.range
        assert lo == -hi and hi >= 100

    def test_volume_pane(self, pos_df):
        fig = posplot(pos_df, volume="volume", volume_pane=True, backend="plotly")
        assert _trace(fig, "Volume").yaxis == "y2"
        assert fig.layout.yaxis2.domain is not None

    def test_strip_layout_colours_by_position(self, pos_df):
        fig = posplot(pos_df, layout="strip", backend="plotly")
        strip = _trace(fig, "Position")
        assert strip.type == "bar"
        assert list(strip.marker.color) == list(pos_df["position"])
        assert (strip.marker.cmin, strip.marker.cmax) == (-100, 100)

    def test_xaxis_range_slices_window(self, pos_df):
        fig = posplot(pos_df, xaxis={"range": ["2024-01-15", "2024-02-02"]}, backend="plotly")
        x = pd.DatetimeIndex(_trace(fig, "Close").x)
        assert x.min() >= pd.Timestamp("2024-01-15")
        assert x.max() <= pd.Timestamp("2024-02-02")

    def test_entry_price_uses_history_before_window(self, pos_df):
        full = posplot(pos_df, backend="plotly")
        cut = posplot(pos_df, xaxis={"range": ["2024-01-22", "2024-02-23"]}, backend="plotly")
        full_entry = pd.Series(_trace(full, "Average entry").y, index=pos_df.index)
        cut_trace = _trace(cut, "Average entry")
        cut_entry = pd.Series(cut_trace.y, index=pd.DatetimeIndex(cut_trace.x))
        pd.testing.assert_series_equal(cut_entry, full_entry.loc[cut_entry.index],
                                       check_freq=False)

    def test_weekends_skipped_for_business_days(self, pos_df):
        fig = posplot(pos_df, backend="plotly")
        assert fig.layout.xaxis.rangebreaks

    def test_title_and_source(self, pos_df):
        fig = posplot(pos_df, title={"main": "XYZ", "sub": "Daily"}, source=["Desk"],
                      backend="plotly")
        assert "XYZ" in fig.layout.title.text
        texts = [a.text for a in fig.layout.annotations]
        assert "Daily" in texts
        assert "Source: Desk" in texts

    def test_dim_sets_chart_width(self, pos_df):
        small = posplot(pos_df, dim={"width": 500}, backend="plotly")
        large = posplot(pos_df, dim={"width": 900}, backend="plotly")
        assert large.layout.width - small.layout.width == 400

    def test_nan_position_is_forward_filled(self, pos_df):
        df = pos_df.copy()
        df.loc[df.index[7], "position"] = np.nan
        fig = posplot(df, backend="plotly")
        assert not np.isnan(np.asarray(_trace(fig, "Position").y, dtype=float)).any()


# ---------------------------------------------------------------------------
# Matplotlib
# ---------------------------------------------------------------------------

class TestPosplotMpl:
    @pytest.mark.parametrize("kwargs", [
        {},
        {"price": OHLC, "kind": "candle"},
        {"price": OHLC, "volume": "volume", "kind": "vcandle"},
        {"volume": "volume", "volume_pane": True},
        {"layout": "strip"},
        {"trades": False},
    ])
    def test_renders(self, pos_df, kwargs):
        fig = posplot(pos_df, backend="matplotlib", **kwargs)
        assert isinstance(fig, matplotlib.figure.Figure)
        fig.canvas.draw()
        plt.close(fig)

    def test_pane_count(self, pos_df):
        fig = posplot(pos_df, backend="matplotlib")
        assert len(fig.axes) == 2
        plt.close(fig)
        fig = posplot(pos_df, volume="volume", volume_pane=True, backend="matplotlib")
        assert len(fig.axes) == 3
        plt.close(fig)

    def test_position_axis_limits(self, pos_df):
        fig = posplot(pos_df, backend="matplotlib")
        lo, hi = fig.axes[-1].get_ylim()
        assert lo == -hi and hi >= 100
        plt.close(fig)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidation:
    def test_requires_datetime_index(self, bad_df):
        with pytest.raises(pxtsValidationError):
            posplot(bad_df, backend="plotly")

    def test_unknown_column(self, pos_df):
        with pytest.raises(ValueError, match="NOPE"):
            posplot(pos_df, position="NOPE", backend="plotly")

    def test_unknown_kind(self, pos_df):
        with pytest.raises(ValueError, match="kind"):
            posplot(pos_df, kind="bars", backend="plotly")

    def test_unknown_layout(self, pos_df):
        with pytest.raises(ValueError, match="layout"):
            posplot(pos_df, layout="overlay", backend="plotly")

    def test_candle_needs_ohlc(self, pos_df):
        df = pos_df[["close", "position"]]
        with pytest.raises(ValueError, match="open/high/low/close"):
            posplot(df, kind="candle", backend="plotly")

    def test_candle_needs_all_ohlc_keys(self, pos_df):
        with pytest.raises(ValueError, match="missing keys"):
            posplot(pos_df, price={"open": "open", "close": "close"}, kind="candle",
                    backend="plotly")

    def test_vcandle_needs_volume(self, pos_df):
        with pytest.raises(ValueError, match="volume"):
            posplot(pos_df.drop(columns="volume"), kind="vcandle", backend="plotly")

    def test_volume_pane_needs_volume(self, pos_df):
        with pytest.raises(ValueError, match="volume"):
            posplot(pos_df.drop(columns="volume"), volume_pane=True, backend="plotly")

    def test_no_price_column(self, pos_df):
        df = pos_df[["position"]].assign(px=pos_df["close"])
        with pytest.raises(ValueError, match="price column"):
            posplot(df, backend="plotly")

    def test_position_out_of_range(self, pos_df):
        df = pos_df.assign(position=pos_df["position"] * 2)
        with pytest.raises(ValueError, match="-100"):
            posplot(df, backend="plotly")

    def test_empty_window(self, pos_df):
        with pytest.raises(ValueError, match="no rows"):
            posplot(pos_df, xaxis={"range": ["2030-01-01", "2030-02-01"]}, backend="plotly")

    def test_dense_vcandles_warn(self, pos_df):
        with pytest.warns(UserWarning, match="volume candles"):
            posplot(pos_df, price=OHLC, volume="volume", kind="vcandle",
                    dim={"width": 100}, backend="plotly")

    def test_roomy_vcandles_do_not_warn(self, pos_df):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            posplot(pos_df, price=OHLC, volume="volume", kind="vcandle", backend="plotly")


# ---------------------------------------------------------------------------
# Column auto-detection and external position
# ---------------------------------------------------------------------------

class TestAutodetect:
    def test_ohlc_and_volume_found_without_arguments(self, pos_df):
        fig = posplot(pos_df, kind="vcandle", backend="plotly")
        body = _trace(fig, "Price")
        assert np.allclose(body.base, np.minimum(pos_df["open"], pos_df["close"]))
        assert len(set(np.round(body.width, 6))) > 1

    def test_close_only_frame_draws_line(self, pos_df):
        fig = posplot(pos_df[["close", "position"]], backend="plotly")
        assert np.allclose(_trace(fig, "Close").y, pos_df["close"])

    def test_explicit_columns_still_win(self, pos_df):
        df = pos_df.assign(mid=(pos_df["high"] + pos_df["low"]) / 2)
        fig = posplot(df, price="mid", backend="plotly")
        assert np.allclose(_trace(fig, "Close").y, df["mid"])


class TestPositionSeries:
    def test_series_matches_column(self, pos_df):
        prices = pos_df.drop(columns="position")
        by_col = posplot(pos_df, backend="plotly")
        by_series = posplot(prices, position=pos_df["position"], backend="plotly")
        assert list(_trace(by_series, "Position").y) == list(_trace(by_col, "Position").y)
        assert list(_trace(by_series, "Buy").x) == list(_trace(by_col, "Buy").x)

    def test_one_column_dataframe(self, pos_df):
        prices = pos_df.drop(columns="position")
        fig = posplot(prices, position=pos_df[["position"]], backend="plotly")
        assert list(_trace(fig, "Position").y) == list(pos_df["position"])

    def test_multi_column_dataframe_rejected(self, pos_df):
        with pytest.raises(ValueError, match="2 columns"):
            posplot(pos_df, position=pos_df[["position", "close"]], backend="plotly")

    def test_sparse_positions_are_held_between_dates(self, pos_df):
        prices = pos_df.drop(columns="position")
        idx = prices.index
        changes = pd.Series([50.0, -25.0], index=[idx[5], idx[20]])
        fig = posplot(prices, position=changes, backend="plotly")
        pos = np.asarray(_trace(fig, "Position").y)
        assert (pos[:5] == 0).all()        # flat before the first position
        assert (pos[5:20] == 50).all()     # held until the next change
        assert (pos[20:] == -25).all()

    def test_position_on_non_trading_day_applies_next_session(self, pos_df):
        prices = pos_df.drop(columns="position")
        saturday = pd.Timestamp("2024-01-06")
        fig = posplot(prices, position=pd.Series([75.0], index=[saturday]), backend="plotly")
        pos = pd.Series(_trace(fig, "Position").y, index=prices.index)
        assert pos.loc["2024-01-05"] == 0
        assert pos.loc["2024-01-08"] == 75

    def test_timezone_aware_position_on_naive_prices(self, pos_df):
        prices = pos_df.drop(columns="position")
        aware = pos_df["position"].tz_localize("UTC")
        fig = posplot(prices, position=aware, backend="plotly")
        assert list(_trace(fig, "Position").y) == list(pos_df["position"])

    def test_bad_position_type(self, pos_df):
        with pytest.raises(ValueError, match="position must be"):
            posplot(pos_df, position=[1, 2, 3], backend="plotly")


# ---------------------------------------------------------------------------
# Bloomberg ticker input
# ---------------------------------------------------------------------------

class TestTickerInput:
    @pytest.fixture
    def bbg(self, pos_df):
        """Patch read_bdh_ohlcv to return the fixture's OHLCV columns."""
        ohlcv = pos_df[["open", "high", "low", "close", "volume"]]
        with patch("pxts.io.read_bdh_ohlcv", return_value=ohlcv.copy()) as mock:
            yield mock

    def test_ticker_and_position_is_enough(self, pos_df, bbg):
        fig = posplot("XYZ US Equity", position=pos_df["position"], kind="vcandle",
                      backend="plotly")
        assert isinstance(fig, go.Figure)
        assert len(set(np.round(_trace(fig, "Price").width, 6))) > 1
        assert list(_trace(fig, "Position").y) == list(pos_df["position"])

    def test_download_starts_at_first_position(self, pos_df, bbg):
        pos = pos_df["position"].iloc[10:]
        posplot("XYZ US Equity", position=pos, backend="plotly")
        args, kwargs = bbg.call_args
        assert args == ("XYZ US Equity",)
        assert kwargs["start"] == pos.index[0]

    def test_default_title_and_source(self, pos_df, bbg):
        fig = posplot("XYZ US Equity", position=pos_df["position"], backend="plotly")
        assert "XYZ US Equity" in fig.layout.title.text
        assert "Source: Bloomberg" in [a.text for a in fig.layout.annotations]

    def test_explicit_title_and_source_kept(self, pos_df, bbg):
        fig = posplot("XYZ US Equity", position=pos_df["position"],
                      title={"main": "My title"}, source=["Desk"], backend="plotly")
        assert "My title" in fig.layout.title.text
        assert "Source: Desk" in [a.text for a in fig.layout.annotations]

    def test_matplotlib_backend(self, pos_df, bbg):
        fig = posplot("XYZ US Equity", position=pos_df["position"], kind="candle",
                      backend="matplotlib")
        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)

    def test_column_name_position_rejected(self, bbg):
        with pytest.raises(ValueError, match="Series"):
            posplot("XYZ US Equity", position="position", backend="plotly")
        bbg.assert_not_called()

    def test_no_volume_falls_back_to_candles(self, pos_df):
        ohlcv = pos_df[["open", "high", "low", "close"]].assign(volume=np.nan)
        with patch("pxts.io.read_bdh_ohlcv", return_value=ohlcv):
            with pytest.warns(UserWarning, match="no volume data"):
                fig = posplot("SPX Index", position=pos_df["position"], kind="vcandle",
                              backend="plotly")
        assert len(set(np.round(_trace(fig, "Price").width, 6))) == 1

    def test_no_volume_drops_volume_pane(self, pos_df):
        ohlcv = pos_df[["open", "high", "low", "close"]].assign(volume=np.nan)
        with patch("pxts.io.read_bdh_ohlcv", return_value=ohlcv):
            with pytest.warns(UserWarning, match="volume pane omitted"):
                fig = posplot("SPX Index", position=pos_df["position"], volume_pane=True,
                              backend="plotly")
        assert "Volume" not in [t.name for t in fig.data]

    def test_no_ohlc_falls_back_to_line(self, pos_df):
        ohlcv = pos_df[["close", "volume"]].assign(open=np.nan, high=np.nan, low=np.nan)
        with patch("pxts.io.read_bdh_ohlcv", return_value=ohlcv):
            with pytest.warns(UserWarning, match="drawing a line"):
                fig = posplot("USGG10YR Index", position=pos_df["position"], kind="candle",
                              backend="plotly")
        assert "Close" in [t.name for t in fig.data]


# ---------------------------------------------------------------------------
# Accessor
# ---------------------------------------------------------------------------

class TestAccessor:
    def test_accessor_delegates(self, pos_df):
        fig = pos_df.ts.posplot(price=OHLC, kind="candle", backend="plotly")
        assert isinstance(fig, go.Figure)
        assert _trace(fig, "Price").type == "bar"
