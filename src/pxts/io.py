"""pxts I/O layer — read_ts and write_ts for CSV round-trips.

Public API:
    read_ts(path, *, tz=None, date_format=None) -> pd.DataFrame
    write_ts(df, path, *, date_format=None) -> None

Internal:
    _detect_date_format(sample) -> tuple[str, bool]
"""
from __future__ import annotations

import re
import warnings
from pathlib import Path
from typing import Union

import pandas as pd

from pxts.core import validate_ts

# ---------------------------------------------------------------------------
# Compiled regex patterns for date format detection
# ---------------------------------------------------------------------------

# Matches ISO 8601: YYYY-MM-DD or YYYY/MM/DD
_ISO_RE = re.compile(r"^\d{4}[-/]\d{2}[-/]\d{2}")

# Matches slash-delimited dates: D/M/YYYY or DD/MM/YYYY or M/D/YYYY etc.
_SLASH_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})")


def _detect_date_format(sample: str) -> tuple[str, bool]:
    """Detect date format from a sample date string.

    Returns a tuple of (format_string, dayfirst) where:
    - format_string is one of "ISO8601", "%d/%m/%Y", "%m/%d/%Y", or "mixed"
    - dayfirst is True for DD/MM/YYYY format, False otherwise

    Rules:
    - ISO match (YYYY-MM-DD or YYYY/MM/DD): return ("ISO8601", False)
    - Slash match: if first part > 12 -> DD/MM/YYYY ("%d/%m/%Y", True)
                   if second part > 12 -> MM/DD/YYYY ("%m/%d/%Y", False)
                   ambiguous (both <= 12) -> default to US ("%m/%d/%Y", False)
    - Fallback: ("mixed", False)
    """
    sample = sample.strip()

    if _ISO_RE.match(sample):
        return ("ISO8601", False)

    slash_match = _SLASH_RE.match(sample)
    if slash_match:
        first = int(slash_match.group(1))
        second = int(slash_match.group(2))
        if first > 12:
            # Day must be first — UK format DD/MM/YYYY
            return ("%d/%m/%Y", True)
        elif second > 12:
            # Month first — US format MM/DD/YYYY
            return ("%m/%d/%Y", False)
        else:
            # Ambiguous — both parts <= 12 — default to US MM/DD/YYYY
            warnings.warn(
                f"pxts: ambiguous date '{sample}' — assumed MM/DD/YYYY (US). "
                f"Pass date_format='%d/%m/%Y' to override.",
                UserWarning,
                stacklevel=3,  # _detect_date_format -> read_ts -> user call site
            )
            return ("%m/%d/%Y", False)

    return ("mixed", False)


def read_ts(
    path: Union[str, Path],
    *,
    tz: str | None = None,
    date_format: str | None = None,
) -> pd.DataFrame:
    """Read a CSV file into a DataFrame with a DatetimeIndex.

    The first column is treated as the datetime index. The first row is
    column headers. Date format is auto-detected from the first data row —
    supports ISO 8601 (YYYY-MM-DD), US (MM/DD/YYYY), and UK (DD/MM/YYYY).

    Parameters
    ----------
    path : str or Path
        Path to the CSV file.
    tz : str or None
        If provided, localize (or convert) the index to this timezone.
        Example: tz='US/Eastern'
    date_format : str or None
        Explicit date format string (e.g. '%Y-%m-%d'). If None, auto-detects.

    Returns
    -------
    pd.DataFrame
        DataFrame with a DatetimeIndex as the index.
    """
    path = Path(path)

    if date_format is not None:
        # Caller provided explicit format — skip detection
        detected_format = date_format
        dayfirst = False
    else:
        # Two-pass: peek first row to detect format
        peek = pd.read_csv(path, nrows=1, header=0)
        sample_str = str(peek.iloc[0, 0])
        detected_format, dayfirst = _detect_date_format(sample_str)

    # Full read with index in first column
    df = pd.read_csv(path, index_col=0, header=0)

    # Save index name before conversion (will be lost during to_datetime)
    index_name = df.index.name

    # Convert string index to DatetimeIndex
    if detected_format == "ISO8601":
        df.index = pd.to_datetime(df.index, format="ISO8601")
    elif detected_format == "mixed":
        df.index = pd.to_datetime(df.index, format="mixed", dayfirst=dayfirst)
    else:
        df.index = pd.to_datetime(df.index, format=detected_format, dayfirst=dayfirst)

    # Restore index name
    df.index.name = index_name

    # Apply timezone if requested
    if tz is not None:
        if df.index.tz is None:
            df.index = df.index.tz_localize(tz)
        else:
            df.index = df.index.tz_convert(tz)

    return df


def write_ts(
    df: pd.DataFrame,
    path: Union[str, Path],
    *,
    date_format: str | None = None,
) -> None:
    """Write a DatetimeIndex DataFrame to a CSV file.

    The datetime index is written as the first column. The first row is
    column headers. Uses ISO 8601 with UTC offset by default for safe
    round-trips.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a DatetimeIndex. Raises pxtsValidationError otherwise.
    path : str or Path
        Destination CSV path.
    date_format : str or None
        Explicit date format string. Defaults to '%Y-%m-%dT%H:%M:%S%z'
        (ISO 8601 with offset — safe for round-trips).

    Raises
    ------
    pxtsValidationError
        If df does not have a DatetimeIndex.
    """
    validate_ts(df)

    if date_format is None:
        date_format = "%Y-%m-%dT%H:%M:%S%z"

    df.to_csv(path, index=True, date_format=date_format)
