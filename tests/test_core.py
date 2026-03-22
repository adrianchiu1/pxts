"""Unit tests for pxts.core public functions.

Covers: validate_ts, set_tz, to_dense, infer_freq — all edge cases per spec.
"""
import warnings

import pandas as pd
import pytest

from pxts.core import infer_freq, set_tz, to_dense, validate_ts
from pxts.exceptions import pxtsValidationError


# ---------------------------------------------------------------------------
# validate_ts
# ---------------------------------------------------------------------------


def test_validate_ts_valid_returns_df(ts_df):
    """Valid DatetimeIndex DataFrame is returned unchanged."""
    result = validate_ts(ts_df)
    assert result is ts_df


def test_validate_ts_range_index_raises(bad_df):
    """RangeIndex DataFrame raises pxtsValidationError."""
    with pytest.raises(pxtsValidationError):
        validate_ts(bad_df)


def test_validate_ts_error_is_type_error_subclass(bad_df):
    """pxtsValidationError is catchable as TypeError (isinstance check)."""
    with pytest.raises(TypeError):
        validate_ts(bad_df)


def test_validate_ts_error_message_contains_datetimeindex(bad_df):
    """Error message mentions DatetimeIndex."""
    with pytest.raises(pxtsValidationError, match="DatetimeIndex"):
        validate_ts(bad_df)


# ---------------------------------------------------------------------------
# set_tz
# ---------------------------------------------------------------------------


def _make_naive_df():
    """Return a 3-row DataFrame with tz-naive DatetimeIndex."""
    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    return pd.DataFrame({"v": [1.0, 2.0, 3.0]}, index=idx)


def _make_eastern_df():
    """Return a 3-row DataFrame whose index is US/Eastern-aware."""
    idx = pd.date_range("2024-01-01", periods=3, freq="D", tz="US/Eastern")
    return pd.DataFrame({"v": [1.0, 2.0, 3.0]}, index=idx)


def _make_utc_df():
    """Return a 3-row DataFrame whose index is UTC-aware."""
    idx = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    return pd.DataFrame({"v": [1.0, 2.0, 3.0]}, index=idx)


def test_set_tz_naive_localizes_to_utc():
    """Naive index + tz='UTC' → localized, result index is UTC."""
    naive_df = _make_naive_df()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = set_tz(naive_df, tz="UTC")
    assert str(result.index.tz) == "UTC"


def test_set_tz_naive_no_warning_emitted():
    """Localizing a naive index must not emit any warning."""
    naive_df = _make_naive_df()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        set_tz(naive_df, tz="UTC")  # Would raise WarningMessage if any warning emitted


def test_set_tz_already_utc_returns_same_object():
    """Already-UTC index + tz='UTC' → same object returned, no warning."""
    utc_df = _make_utc_df()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = set_tz(utc_df, tz="UTC")
    assert result is utc_df


def test_set_tz_eastern_to_utc_emits_warning():
    """US/Eastern index converted to UTC emits UserWarning containing 'converted'."""
    eastern_df = _make_eastern_df()
    with pytest.warns(UserWarning, match="converted"):
        result = set_tz(eastern_df, tz="UTC")
    assert str(result.index.tz) == "UTC"


def test_set_tz_naive_to_eastern():
    """Naive index + tz='US/Eastern' → localized to US/Eastern, no warning."""
    naive_df = _make_naive_df()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = set_tz(naive_df, tz="US/Eastern")
    assert "Eastern" in str(result.index.tz)


def test_set_tz_etc_utc_is_noop():
    """UTC-aware index + tz='Etc/UTC' → same object returned, no warning (FIX-02).

    'Etc/UTC' and 'UTC' are semantically equivalent timezones. Calling set_tz
    with a semantically equivalent zone must be a no-op — no conversion, no warning.
    """
    utc_df = _make_utc_df()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = set_tz(utc_df, tz="Etc/UTC")
    assert result is utc_df


def test_set_tz_non_datetimeindex_raises(bad_df):
    """set_tz propagates pxtsValidationError from validate_ts gate."""
    with pytest.raises(pxtsValidationError):
        set_tz(bad_df, tz="UTC")


# ---------------------------------------------------------------------------
# to_dense
# ---------------------------------------------------------------------------


def _make_sparse_daily_df():
    """5-row daily df with two interior gaps (2024-01-02 and 2024-01-04 missing)."""
    dates = pd.DatetimeIndex(
        ["2024-01-01", "2024-01-03", "2024-01-05", "2024-01-07", "2024-01-09"]
    )
    return pd.DataFrame({"v": [1.0, 3.0, 5.0, 7.0, 9.0]}, index=dates)


def test_to_dense_fills_gaps_with_nan():
    """Sparse daily df + freq='D' → densified with NaN in new rows."""
    sparse = _make_sparse_daily_df()
    result = to_dense(sparse, freq="D")
    assert len(result) == 9  # 2024-01-01 through 2024-01-09
    assert result.loc["2024-01-02", "v"] != result.loc["2024-01-02", "v"]  # NaN check


def test_to_dense_ffill_fills_gaps():
    """Sparse daily df + freq='D' + fill='ffill' → gaps filled with prior value."""
    sparse = _make_sparse_daily_df()
    result = to_dense(sparse, freq="D", fill="ffill")
    assert len(result) == 9
    # 2024-01-02 should be filled with the value from 2024-01-01
    assert result.loc["2024-01-02", "v"] == pytest.approx(1.0)
    assert result.loc["2024-01-04", "v"] == pytest.approx(3.0)


def test_to_dense_noop_when_already_at_freq(ts_df):
    """Already-dense df with freq set + matching freqstr → same object returned."""
    # ts_df has freq='D' from date_range; verify the guard fires
    assert ts_df.index.freq is not None
    result = to_dense(ts_df, freq="D")
    assert result is ts_df


def test_to_dense_non_datetimeindex_raises(bad_df):
    """to_dense propagates pxtsValidationError from validate_ts gate."""
    with pytest.raises(pxtsValidationError):
        to_dense(bad_df, freq="D")


def test_to_dense_1D_alias_is_noop(ts_df):
    """freq='1D' on df with freqstr 'D' IS a no-op after alias normalization (FIX-04).

    '1D' and 'D' are semantically equivalent pandas offset aliases. The no-op guard
    must normalize both sides before comparing so '1D' on a 'D'-freq index is a no-op.
    """
    result = to_dense(ts_df, freq="1D")
    assert result is ts_df


def test_to_dense_different_freq_is_not_noop(ts_df):
    """freq='h' on df with freqstr 'D' is NOT a no-op (genuinely different freq)."""
    # ts_df has freq='D'; requesting hourly freq should trigger asfreq
    result = to_dense(ts_df, freq="h")
    assert result is not ts_df


# ---------------------------------------------------------------------------
# infer_freq
# ---------------------------------------------------------------------------


def test_infer_freq_daily_weekdays_returns_B(ts_df):
    """5-row Mon-Fri daily df → returns 'B' (business day), not 'D' (FIX-03).

    ts_df spans 2024-01-01 (Mon) through 2024-01-05 (Fri) — no weekends.
    Smart detection should return 'B' since all timestamps are weekdays.
    """
    result = infer_freq(ts_df)
    assert result == "B"


def test_infer_freq_daily_with_weekends_returns_D():
    """Daily df that includes Sat or Sun → returns 'D' (calendar day) (FIX-03)."""
    # 2024-01-01 (Mon) through 2024-01-07 (Sun) — includes Sat and Sun
    idx = pd.date_range("2024-01-01", periods=7, freq="D")
    df = pd.DataFrame({"v": range(7)}, index=idx)
    result = infer_freq(df)
    assert result == "D"


def test_infer_freq_hourly_returns_h():
    """5-row hourly df → returns 'h'."""
    idx = pd.date_range("2024-01-01", periods=5, freq="h")
    df = pd.DataFrame({"v": range(5)}, index=idx)
    result = infer_freq(df)
    assert result == "h"


def test_infer_freq_single_row_raises_valueerror():
    """Single-row df raises ValueError (cannot compute diffs)."""
    idx = pd.DatetimeIndex(["2024-01-01"])
    df = pd.DataFrame({"v": [1.0]}, index=idx)
    with pytest.raises(ValueError):
        infer_freq(df)


def test_infer_freq_empty_df_raises_valueerror():
    """Empty df raises ValueError."""
    idx = pd.DatetimeIndex([])
    df = pd.DataFrame({"v": []}, index=idx)
    with pytest.raises(ValueError):
        infer_freq(df)


def test_infer_freq_non_datetimeindex_raises(bad_df):
    """infer_freq propagates pxtsValidationError from validate_ts gate."""
    with pytest.raises(pxtsValidationError):
        infer_freq(bad_df)


# ---------------------------------------------------------------------------
# to_dense with freq=None (auto-detection)
# ---------------------------------------------------------------------------


def test_to_dense_auto_freq_daily():
    """to_dense(freq=None) on sparse calendar-day df infers 'D' and fills gaps.

    Three rows with 1-day min gap including a weekend ensure infer_freq returns
    'D'. The larger gap (Sun → Tue) is then filled by asfreq('D').
    """
    # Sat 6, Sun 7, Tue 9 — min diff = 1 day; includes weekend → infer_freq='D'
    dates = pd.DatetimeIndex(["2024-01-06", "2024-01-07", "2024-01-09"])
    df = pd.DataFrame({"v": [1.0, 2.0, 3.0]}, index=dates)
    result = to_dense(df)
    assert len(result) == 4  # Sat 6, Sun 7, Mon 8, Tue 9
    assert result.loc["2024-01-08", "v"] != result.loc["2024-01-08", "v"]  # NaN


def test_to_dense_auto_freq_business_day():
    """to_dense(freq=None) on weekday-only sparse df infers 'B' and fills gaps.

    Three rows with 1-day min gap, all weekdays, so infer_freq returns 'B'.
    The larger gap (Tue → Thu) is then filled by asfreq('B').
    """
    # Mon 1, Tue 2, Thu 4 — min diff = 1 day; no weekends → infer_freq='B'
    dates = pd.DatetimeIndex(["2024-01-01", "2024-01-02", "2024-01-04"])
    df = pd.DataFrame({"v": [1.0, 2.0, 4.0]}, index=dates)
    result = to_dense(df)
    assert len(result) == 4  # Mon, Tue, Wed, Thu
    assert result.loc["2024-01-03", "v"] != result.loc["2024-01-03", "v"]  # NaN


def test_to_dense_auto_freq_hourly():
    """to_dense(freq=None) on sparse hourly df infers 'h' and fills gaps.

    Three rows with 1-hour min gap; the larger gap (01:00 → 03:00) is filled.
    """
    # Hours 00, 01, 03 — min diff = 1h → infer_freq='h'
    idx = pd.DatetimeIndex(["2024-01-01 00:00", "2024-01-01 01:00", "2024-01-01 03:00"])
    df = pd.DataFrame({"v": [0.0, 1.0, 3.0]}, index=idx)
    result = to_dense(df)
    assert len(result) == 4  # 00, 01, 02, 03
    assert result.loc["2024-01-01 02:00", "v"] != result.loc["2024-01-01 02:00", "v"]  # NaN


def test_to_dense_auto_freq_single_row_raises():
    """to_dense(freq=None) on single-row df raises ValueError (cannot infer freq)."""
    idx = pd.DatetimeIndex(["2024-01-01"])
    df = pd.DataFrame({"v": [1.0]}, index=idx)
    with pytest.raises(ValueError):
        to_dense(df)
