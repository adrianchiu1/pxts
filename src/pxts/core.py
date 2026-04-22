"""pxts core standalone functions for datetime-indexed DataFrames."""
from __future__ import annotations

import calendar as _calendar
import warnings

import pandas as pd
from pandas.tseries.frequencies import to_offset

from pxts.exceptions import pxtsValidationError

_MONTH_ABBR = {
    1: "JAN", 2: "FEB", 3: "MAR", 4: "APR",
    5: "MAY", 6: "JUN", 7: "JUL", 8: "AUG",
    9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC",
}

# IMM months: March, June, September, December
_IMM_MONTHS = frozenset({3, 6, 9, 12})

# Quarter-start month sets mapped to their pandas alias
_QS_SETS = (
    (frozenset({1, 4, 7, 10}), "QS"),
    (frozenset({2, 5, 8, 11}), "QS-FEB"),
    (frozenset({3, 6, 9, 12}), "QS-MAR"),
)

# Quarter-end month sets mapped to their pandas alias
_QE_SETS = (
    (frozenset({3, 6, 9, 12}), "QE"),
    (frozenset({1, 4, 7, 10}), "QE-OCT"),
    (frozenset({2, 5, 8, 11}), "QE-NOV"),
)


def _is_month_end(ts: pd.Timestamp) -> bool:
    return ts.day == _calendar.monthrange(ts.year, ts.month)[1]


def _detect_monthly(index: pd.DatetimeIndex) -> str | None:
    if all(ts.day == 1 for ts in index):
        return "MS"
    if all(_is_month_end(ts) for ts in index):
        return "ME"
    return None


def _detect_quarterly(index: pd.DatetimeIndex) -> str | None:
    months = [ts.month for ts in index]

    # IMM: 3rd Wednesday of Mar/Jun/Sep/Dec — check before QS-MAR which shares months
    if (
        all(m in _IMM_MONTHS for m in months)
        and all(15 <= ts.day <= 21 for ts in index)
        and all(ts.weekday() == 2 for ts in index)
    ):
        return "IMM"

    unique_months = frozenset(months)

    if all(ts.day == 1 for ts in index):
        for month_set, alias in _QS_SETS:
            if unique_months <= month_set:
                return alias

    if all(_is_month_end(ts) for ts in index):
        for month_set, alias in _QE_SETS:
            if unique_months <= month_set:
                return alias

    return None


def _detect_yearly(index: pd.DatetimeIndex) -> str | None:
    months = [ts.month for ts in index]
    if len(set(months)) != 1:
        return None
    month = months[0]

    if all(ts.day == 1 for ts in index):
        return "YS" if month == 1 else f"YS-{_MONTH_ABBR[month]}"

    if all(_is_month_end(ts) for ts in index):
        return "YE" if month == 12 else f"YE-{_MONTH_ABBR[month]}"

    return None


def _generate_imm_dates(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """Return all IMM dates in [start, end] plus the next one after end."""
    dates: list[pd.Timestamp] = []
    year = start.year
    found_beyond = False
    while not found_beyond:
        for month in [3, 6, 9, 12]:
            first = pd.Timestamp(year, month, 1)
            days_to_wed = (2 - first.weekday()) % 7
            third_wed = first + pd.Timedelta(days=days_to_wed) + pd.Timedelta(weeks=2)
            if third_wed >= start:
                dates.append(third_wed)
                if third_wed > end:
                    found_beyond = True
                    break
        year += 1
    return pd.DatetimeIndex(dates)


def _tz_equal(tz_a, tz_b) -> bool:
    """Return True if tz_a and tz_b represent the same timezone.

    Compares UTC offsets at a winter and summer reference point to handle
    aliases like 'UTC' vs 'Etc/UTC', while correctly distinguishing
    fixed-offset zones from DST-observing zones.
    """
    try:
        ref_points = ("2000-01-01", "2000-07-01")
        for ref in ref_points:
            if pd.Timestamp(ref, tz=tz_a).utcoffset() != pd.Timestamp(ref, tz=tz_b).utcoffset():
                return False
        return True
    except Exception:
        return False


def validate_ts(df: pd.DataFrame) -> pd.DataFrame:
    """Validate that df has a DatetimeIndex, that it is not a MultiIndex, and that the datetime index is unique.
    Returns df unchanged if valid.
    Raises pxtsValidationError (a TypeError subclass) if not.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise pxtsValidationError(
            f"pxts requires a DatetimeIndex. "
            f"Instead index type is {type(df.index).__name__}. "
            f"Use pd.DataFrame(..., index=pd.to_datetime(dates)) to fix."
        )
    if isinstance(df.index, pd.MultiIndex):
        raise AttributeError("Index must not be pd.MultiIndex")
    
    # Verify that index is unique
    if not df.index.is_unique:
        raise AttributeError("Index must be unique")
    
    return df


def set_tz(df: pd.DataFrame, tz: str = "UTC") -> pd.DataFrame:
    """Normalize the DatetimeIndex timezone.

    - Tz-naive index: localized to `tz` silently.
    - Already at target tz: returned unchanged (same object).
    - Tz-aware but different tz: converted to `tz` with a UserWarning.

    Returns a new DataFrame (immutable). Does not modify in place.
    """
    validate_ts(df)
    index = df.index

    if index.tz is None:
        # Naive — localize silently
        new_index = index.tz_localize(tz)
    elif _tz_equal(index.tz, tz):
        # Already at target tz (semantically) — no-op
        return df
    else:
        # Tz-aware but different — convert with warning
        warnings.warn(
            f"pxts: DatetimeIndex timezone '{index.tz}' converted to {tz}. "
            f"Use set_tz(df, tz='{index.tz}') to restore.",
            UserWarning,
            stacklevel=2,
        )
        new_index = index.tz_convert(tz)

    return df.set_index(new_index)


def to_dense(
    df: pd.DataFrame, freq: str | None = None, fill: str | None = None
) -> pd.DataFrame:
    """Regularize a sparse DatetimeIndex to equal intervals.

    Uses pandas offset aliases: 'D' (calendar day), 'B' (business day),
    'h' (hour), 'ME' (month end), etc.

    New rows receive NaN by default. Pass fill='ffill' or fill='bfill'
    to forward- or back-fill values.

    If the index is already at `freq`, returns df unchanged (no-op).

    If freq is None, the frequency is inferred automatically via infer_freq().
    Note: auto-detection cannot distinguish 'B' from 'D' if all timestamps
    are weekdays — it will return 'B' in that case. Pass freq explicitly to
    override.
    """
    validate_ts(df)
    if freq is None:
        freq = infer_freq(df)
    if freq == "IMM":
        new_index = _generate_imm_dates(df.index.min(), df.index.max())
        return df.reindex(new_index, method=fill)
    # Guard: no-op if already at requested frequency (normalize alias before comparing)
    if df.index.freq is not None:
        try:
            norm_freq = to_offset(freq).freqstr
            if df.index.freqstr == norm_freq:
                return df
        except Exception:
            pass  # Unrecognized alias — let asfreq raise its own error
    return df.asfreq(freq=freq, method=fill)


def infer_freq(df: pd.DataFrame) -> str:
    """Infer the minimum observed interval in the DatetimeIndex.

    Returns a pandas offset alias string ('D', 'h', 'ME', 'QS', 'IMM', etc.)
    directly usable in to_dense() and pandas resampling.

    Uses the minimum diff approach: min(index.diff().dropna()). This returns
    the most granular interval present, which prevents data loss when densifying.

    Calendar-based frequencies (monthly, quarterly, yearly, IMM) are detected
    from date alignment and emit a UserWarning so callers know the freq was
    inferred. Pass freq= explicitly to to_dense() to suppress the warning.

    Limitation: Cannot distinguish 'B' (business day) from 'D' (calendar day)
    because a 1-day timedelta maps to Day, not BusinessDay. Pass freq='B' to
    to_dense() explicitly.

    Raises ValueError if fewer than 2 data points (cannot compute diffs).
    """
    validate_ts(df)
    diffs = df.index.to_series().diff().dropna()
    if diffs.empty:
        raise ValueError(
            "pxts: Cannot infer frequency from fewer than 2 data points."
        )
    min_diff = diffs.min()

    # B-vs-D: a 1-day minimum diff could be business or calendar day
    if min_diff == pd.Timedelta(days=1):
        has_weekend = any(ts.weekday() >= 5 for ts in df.index)
        return "D" if has_weekend else "B"

    # Calendar-based detection: range check then date-alignment check.
    # Quarterly range [84, 98] is wider than standard [90, 92] to cover all
    # possible IMM gaps (3rd Wednesday shifts cause 84–98 day spreads).
    days = min_diff.days
    cal_freq: str | None = None
    ambiguous_msg: str | None = None

    if 28 <= days <= 31:
        cal_freq = _detect_monthly(df.index)
        if cal_freq is None:
            ambiguous_msg = (
                f"Data looks monthly (min gap {days} days) but dates don't align "
                f"to month-start or month-end."
            )
    elif 84 <= days <= 98:
        cal_freq = _detect_quarterly(df.index)
        if cal_freq is None:
            ambiguous_msg = (
                f"Data looks quarterly (min gap {days} days) but dates don't align "
                f"to a recognised quarterly pattern (QS, QE, or IMM)."
            )
    elif 365 <= days <= 366:
        cal_freq = _detect_yearly(df.index)
        if cal_freq is None:
            ambiguous_msg = (
                f"Data looks yearly (min gap {days} days) but dates don't align "
                f"to year-start or year-end."
            )

    if cal_freq is not None:
        if cal_freq == "IMM":
            warnings.warn(
                "pxts: Inferred IMM quarterly frequency "
                "(3rd Wednesday of Mar/Jun/Sep/Dec). "
                "Pass freq='IMM' explicitly to suppress this warning.",
                UserWarning,
                stacklevel=2,
            )
        else:
            warnings.warn(
                f"pxts: Inferred calendar frequency '{cal_freq}' from data. "
                f"Pass freq='{cal_freq}' explicitly to suppress this warning.",
                UserWarning,
                stacklevel=2,
            )
        return cal_freq

    if ambiguous_msg is not None:
        fallback = to_offset(min_diff).freqstr
        warnings.warn(
            f"pxts: {ambiguous_msg} "
            f"Falling back to '{fallback}'. Pass freq= explicitly to override.",
            UserWarning,
            stacklevel=2,
        )

    offset = to_offset(min_diff)
    if offset is None:
        raise ValueError(
            f"pxts: Cannot map timedelta {min_diff} to a pandas offset alias."
        )
    return offset.freqstr
