"""Unit tests for pxts.core public functions.

Covers: validate_ts, set_tz, to_dense, infer_freq — all edge cases per spec.
"""
import warnings

import pandas as pd
import pytest

from pxts.core import (
    _detect_monthly,
    _detect_quarterly,
    _detect_yearly,
    _generate_imm_dates,
    infer_freq,
    set_tz,
    to_dense,
    validate_ts,
)
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


# ---------------------------------------------------------------------------
# Calendar frequency detection helpers
# ---------------------------------------------------------------------------


def _make_df(dates):
    idx = pd.DatetimeIndex(dates)
    return pd.DataFrame({"v": range(len(dates))}, index=idx)


# --- monthly ---

def test_detect_monthly_month_start():
    idx = pd.DatetimeIndex(["2000-01-01", "2000-02-01", "2000-03-01"])
    assert _detect_monthly(idx) == "MS"


def test_detect_monthly_month_end():
    # Includes Feb 29 (leap year) to verify end-of-month varies per month
    idx = pd.DatetimeIndex(["2000-01-31", "2000-02-29", "2000-03-31"])
    assert _detect_monthly(idx) == "ME"


def test_detect_monthly_month_end_non_leap():
    idx = pd.DatetimeIndex(["2001-01-31", "2001-02-28", "2001-03-31"])
    assert _detect_monthly(idx) == "ME"


def test_detect_monthly_mid_month_returns_none():
    idx = pd.DatetimeIndex(["2000-01-15", "2000-02-15"])
    assert _detect_monthly(idx) is None


# --- quarterly ---

def test_detect_quarterly_qs_standard():
    idx = pd.DatetimeIndex(["2000-01-01", "2000-04-01", "2000-07-01", "2000-10-01"])
    assert _detect_quarterly(idx) == "QS"


def test_detect_quarterly_qs_feb():
    idx = pd.DatetimeIndex(["2000-02-01", "2000-05-01", "2000-08-01", "2000-11-01"])
    assert _detect_quarterly(idx) == "QS-FEB"


def test_detect_quarterly_qs_mar():
    idx = pd.DatetimeIndex(["2000-03-01", "2000-06-01", "2000-09-01", "2000-12-01"])
    assert _detect_quarterly(idx) == "QS-MAR"


def test_detect_quarterly_qe_standard():
    idx = pd.DatetimeIndex(["2000-03-31", "2000-06-30", "2000-09-30", "2000-12-31"])
    assert _detect_quarterly(idx) == "QE"


def test_detect_quarterly_qe_oct():
    idx = pd.DatetimeIndex(["2000-01-31", "2000-04-30", "2000-07-31", "2000-10-31"])
    assert _detect_quarterly(idx) == "QE-OCT"


def test_detect_quarterly_qe_nov():
    # Feb 29 (leap) end-of-month included
    idx = pd.DatetimeIndex(["2000-02-29", "2000-05-31", "2000-08-31", "2000-11-30"])
    assert _detect_quarterly(idx) == "QE-NOV"


def test_detect_quarterly_imm_2000():
    # 3rd Wednesday of Mar/Jun/Sep/Dec 2000: Mar-15, Jun-21, Sep-20, Dec-20
    idx = pd.DatetimeIndex(["2000-03-15", "2000-06-21", "2000-09-20", "2000-12-20"])
    assert _detect_quarterly(idx) == "IMM"


def test_detect_quarterly_imm_partial_two_dates():
    # Two consecutive IMM dates still detected
    idx = pd.DatetimeIndex(["2000-03-15", "2000-06-21"])
    assert _detect_quarterly(idx) == "IMM"


def test_detect_quarterly_non_wednesday_returns_none():
    # Same months as IMM but not Wednesdays → not IMM, not QS, not QE
    idx = pd.DatetimeIndex(["2000-03-16", "2000-06-22"])  # Thursdays
    assert _detect_quarterly(idx) is None


# --- yearly ---

def test_detect_yearly_ys():
    idx = pd.DatetimeIndex(["2000-01-01", "2001-01-01", "2002-01-01"])
    assert _detect_yearly(idx) == "YS"


def test_detect_yearly_ye():
    idx = pd.DatetimeIndex(["2000-12-31", "2001-12-31", "2002-12-31"])
    assert _detect_yearly(idx) == "YE"


def test_detect_yearly_ys_non_standard():
    idx = pd.DatetimeIndex(["2000-04-01", "2001-04-01", "2002-04-01"])
    assert _detect_yearly(idx) == "YS-APR"


def test_detect_yearly_ye_non_standard():
    idx = pd.DatetimeIndex(["2000-03-31", "2001-03-31", "2002-03-31"])
    assert _detect_yearly(idx) == "YE-MAR"


def test_detect_yearly_ye_feb_leap_variation():
    # Feb end-of-month: 2000-02-29 (leap), 2001-02-28, 2002-02-28
    idx = pd.DatetimeIndex(["2000-02-29", "2001-02-28", "2002-02-28"])
    assert _detect_yearly(idx) == "YE-FEB"


def test_detect_yearly_mid_month_returns_none():
    idx = pd.DatetimeIndex(["2000-03-15", "2001-03-15"])
    assert _detect_yearly(idx) is None


def test_detect_yearly_mixed_months_returns_none():
    idx = pd.DatetimeIndex(["2000-01-01", "2001-04-01"])
    assert _detect_yearly(idx) is None


# ---------------------------------------------------------------------------
# infer_freq — calendar detection + warnings
# ---------------------------------------------------------------------------


def test_infer_freq_monthly_start_warns_and_returns_ms():
    # 2000-01-01 → 2000-02-01: 31 days (in [28,31])
    df = _make_df(["2000-01-01", "2000-02-01", "2000-03-01"])
    with pytest.warns(UserWarning, match="'MS'"):
        result = infer_freq(df)
    assert result == "MS"


def test_infer_freq_monthly_end_warns_and_returns_me():
    df = _make_df(["2000-01-31", "2000-02-29", "2000-03-31"])
    with pytest.warns(UserWarning, match="'ME'"):
        result = infer_freq(df)
    assert result == "ME"


def test_infer_freq_quarterly_start_warns_and_returns_qs():
    # Jan-01 → Apr-01: 91 days (2000 leap)
    df = _make_df(["2000-01-01", "2000-04-01", "2000-07-01", "2000-10-01"])
    with pytest.warns(UserWarning, match="'QS'"):
        result = infer_freq(df)
    assert result == "QS"


def test_infer_freq_quarterly_end_warns_and_returns_qe():
    df = _make_df(["2000-03-31", "2000-06-30", "2000-09-30", "2000-12-31"])
    with pytest.warns(UserWarning, match="'QE'"):
        result = infer_freq(df)
    assert result == "QE"


def test_infer_freq_imm_warns_and_returns_imm():
    df = _make_df(["2000-03-15", "2000-06-21", "2000-09-20", "2000-12-20"])
    with pytest.warns(UserWarning, match="IMM"):
        result = infer_freq(df)
    assert result == "IMM"


def test_infer_freq_yearly_start_warns_and_returns_ys():
    # 2000-01-01 → 2001-01-01: 366 days (leap year)
    df = _make_df(["2000-01-01", "2001-01-01", "2002-01-01"])
    with pytest.warns(UserWarning, match="'YS'"):
        result = infer_freq(df)
    assert result == "YS"


def test_infer_freq_yearly_end_warns_and_returns_ye():
    df = _make_df(["2000-12-31", "2001-12-31", "2002-12-31"])
    with pytest.warns(UserWarning, match="'YE'"):
        result = infer_freq(df)
    assert result == "YE"


_CALENDAR_ALIASES = {"MS", "ME", "QS", "QE", "YS", "YE", "IMM"}


def test_infer_freq_ambiguous_monthly_warns_and_falls_back():
    # Mid-month dates: gap 31 days but not MS or ME
    df = _make_df(["2000-01-15", "2000-02-15"])
    with pytest.warns(UserWarning, match="looks monthly"):
        result = infer_freq(df)
    assert result not in _CALENDAR_ALIASES  # falls back to a fixed-duration alias


def test_infer_freq_ambiguous_quarterly_warns_and_falls_back():
    # 2000-03-16 and 2000-06-22 are Thursdays: in IMM months but wrong weekday
    df = _make_df(["2000-03-16", "2000-06-22"])
    with pytest.warns(UserWarning, match="looks quarterly"):
        result = infer_freq(df)
    assert result not in _CALENDAR_ALIASES


def test_infer_freq_ambiguous_yearly_warns_and_falls_back():
    # 2000 is leap: Mar-15 to Mar-15 next year = 366 days
    df = _make_df(["2000-03-15", "2001-03-15"])
    with pytest.warns(UserWarning, match="looks yearly"):
        result = infer_freq(df)
    assert result not in _CALENDAR_ALIASES


def test_infer_freq_daily_emits_no_calendar_warning():
    # Existing daily detection must not accidentally warn about calendar freq
    idx = pd.date_range("2024-01-01", periods=5, freq="D")
    df = pd.DataFrame({"v": range(5)}, index=idx)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        infer_freq(df)  # must not raise


# ---------------------------------------------------------------------------
# _generate_imm_dates
# ---------------------------------------------------------------------------


def test_generate_imm_dates_full_year_2000():
    # All four 2000 IMM dates plus the first 2001 date (one beyond Dec-20)
    result = _generate_imm_dates(pd.Timestamp("2000-03-15"), pd.Timestamp("2000-12-20"))
    expected = pd.DatetimeIndex([
        "2000-03-15", "2000-06-21", "2000-09-20", "2000-12-20", "2001-03-21",
    ])
    assert list(result) == list(expected)


def test_generate_imm_dates_mid_year_start():
    # Starting mid-year: Sep and Dec 2000, then Mar 2001 (one beyond Dec-20)
    result = _generate_imm_dates(pd.Timestamp("2000-09-20"), pd.Timestamp("2000-12-20"))
    expected = pd.DatetimeIndex(["2000-09-20", "2000-12-20", "2001-03-21"])
    assert list(result) == list(expected)


def test_generate_imm_dates_extends_one_beyond_end():
    # end is exactly the last IMM date; next one must be appended
    result = _generate_imm_dates(pd.Timestamp("2000-12-20"), pd.Timestamp("2000-12-20"))
    assert len(result) == 2
    assert result[0] == pd.Timestamp("2000-12-20")
    assert result[1] == pd.Timestamp("2001-03-21")


# ---------------------------------------------------------------------------
# to_dense with calendar frequencies
# ---------------------------------------------------------------------------


def test_to_dense_monthly_start_fills_gap():
    # Missing Feb and Mar; auto-detected as MS
    df = _make_df(["2000-01-01", "2000-02-01", "2000-04-01"])
    with pytest.warns(UserWarning):
        result = to_dense(df)
    assert pd.Timestamp("2000-03-01") in result.index
    assert pd.isna(result.loc["2000-03-01", "v"])


def test_to_dense_monthly_end_explicit_no_warning():
    # Explicit freq suppresses the warning
    df = _make_df(["2000-01-31", "2000-02-29", "2000-04-30"])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = to_dense(df, freq="ME")
    assert pd.Timestamp("2000-03-31") in result.index


def test_to_dense_quarterly_start_fills_gap():
    # Missing Q3; auto-detected as QS
    df = _make_df(["2000-01-01", "2000-04-01", "2000-10-01"])
    with pytest.warns(UserWarning, match="'QS'"):
        result = to_dense(df)
    assert pd.Timestamp("2000-07-01") in result.index
    assert pd.isna(result.loc["2000-07-01", "v"])


def test_to_dense_quarterly_end_fills_gap():
    df = _make_df(["2000-03-31", "2000-06-30", "2000-12-31"])
    with pytest.warns(UserWarning, match="'QE'"):
        result = to_dense(df)
    assert pd.Timestamp("2000-09-30") in result.index


def test_to_dense_yearly_start_fills_gap():
    # Missing 2001; auto-detected as YS
    df = _make_df(["2000-01-01", "2001-01-01", "2003-01-01"])
    with pytest.warns(UserWarning, match="'YS'"):
        result = to_dense(df)
    assert pd.Timestamp("2002-01-01") in result.index
    assert pd.isna(result.loc["2002-01-01", "v"])


def test_to_dense_imm_fills_gap_and_extends():
    # Input: Mar-15, Jun-21, Dec-20 — gap at Sep-20, extends to Mar-21 next year
    df = _make_df(["2000-03-15", "2000-06-21", "2000-12-20"])
    with pytest.warns(UserWarning, match="IMM"):
        result = to_dense(df)
    expected_index = pd.DatetimeIndex([
        "2000-03-15", "2000-06-21", "2000-09-20", "2000-12-20", "2001-03-21",
    ])
    assert list(result.index) == list(expected_index)
    assert pd.isna(result.loc["2000-09-20", "v"])   # gap filled with NaN
    assert pd.isna(result.loc["2001-03-21", "v"])   # extended row is NaN


def test_to_dense_imm_ffill():
    df = _make_df(["2000-03-15", "2000-06-21", "2000-12-20"])
    with pytest.warns(UserWarning):
        result = to_dense(df, fill="ffill")
    # Sep-20 gap should be forward-filled from Jun-21 value (index 1 → value 1)
    assert result.loc["2000-09-20", "v"] == 1


def test_to_dense_imm_explicit_no_warning():
    # Passing freq='IMM' explicitly suppresses the warning
    df = _make_df(["2000-03-15", "2000-06-21", "2000-12-20"])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = to_dense(df, freq="IMM")
    assert len(result) == 5
