"""pxts core standalone functions for datetime-indexed DataFrames."""
from __future__ import annotations

import warnings

import pandas as pd
from pandas.tseries.frequencies import to_offset

from pxts.exceptions import pxtsValidationError


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
    df: pd.DataFrame, freq: str, fill: str | None = None
) -> pd.DataFrame:
    """Regularize a sparse DatetimeIndex to equal intervals.

    Uses pandas offset aliases: 'D' (calendar day), 'B' (business day),
    'h' (hour), 'ME' (month end), etc.

    New rows receive NaN by default. Pass fill='ffill' or fill='bfill'
    to forward- or back-fill values.

    If the index is already at `freq`, returns df unchanged (no-op).

    Note: Cannot distinguish 'B' from 'D' from index diffs alone.
    If the existing index is already daily (freq='D'), this is a no-op
    even if freq='B' was intended. Pass freq explicitly.
    """
    validate_ts(df)
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

    Returns a pandas offset alias string ('D', 'h', 'ME', etc.) directly
    usable in to_dense() and pandas resampling.

    Uses the minimum diff approach: min(index.diff().dropna()). This returns
    the most granular interval present, which prevents data loss when densifying.

    Limitation: Cannot distinguish 'B' (business day) from 'D' (calendar day)
    because a 1-day timedelta maps to Day, not BusinessDay. Document this in
    user-facing docs; users should pass freq='B' to to_dense() explicitly.

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
    offset = to_offset(min_diff)
    if offset is None:
        raise ValueError(
            f"pxts: Cannot map timedelta {min_diff} to a pandas offset alias."
        )
    return offset.freqstr
