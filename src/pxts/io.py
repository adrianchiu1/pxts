"""pxts I/O layer — read_ts, write_ts, and read_bdh for CSV round-trips and Bloomberg data.

Public API:
    read_ts(path, *, tz=None, date_format=None) -> pd.DataFrame
    write_ts(df, path, *, date_format=None) -> None
    read_bdh(tickers, start, field='PX_LAST', end=None) -> pd.DataFrame

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
                   ambiguous (both <= 12) -> default to British ("%d/%m/%Y", True)
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
            # Ambiguous — both parts <= 12 — default to British DD/MM/YYYY
            warnings.warn(
                f"pxts: ambiguous date '{sample}' — assumed DD/MM/YYYY (British). "
                f"Pass date_format='%m/%d/%Y' to override.",
                UserWarning,
                stacklevel=3,  # _detect_date_format -> read_ts -> user call site
            )
            return ("%d/%m/%Y", True)

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


def read_bdh(
    tickers,
    start,
    field: str = "PX_LAST",
    end=None,
) -> pd.DataFrame:
    """Fetch Bloomberg BDH historical time series data.

    Opens a Bloomberg connection, fetches the requested tickers over the
    given date range, and returns a validated wide-format DataFrame with
    a DatetimeIndex and one column per ticker.

    Requires pdblp (optional dependency). Install with:
        pip install pxts[bloomberg]

    Parameters
    ----------
    tickers : list of str
        Bloomberg ticker strings, e.g. ['AAPL US Equity', 'MSFT US Equity'].
    start : str, datetime, or pd.Timestamp
        Start date (inclusive). Converted to 'YYYYMMDD' string internally.
    field : str
        Bloomberg field name. Defaults to 'PX_LAST'.
    end : str, datetime, pd.Timestamp, or None
        End date (inclusive). Defaults to today when None.

    Returns
    -------
    pd.DataFrame
        Wide-format DataFrame with DatetimeIndex (rows = dates,
        columns = Bloomberg ticker strings).

    Raises
    ------
    ImportError
        If pdblp is not installed.
    pxtsValidationError
        If the returned DataFrame does not have a DatetimeIndex.
    """
    try:
        import pdblp
    except ImportError:
        raise ImportError(
            "pdblp required for read_bdh(). Install with: pip install pxts[bloomberg]"
        )

    start_date = pd.to_datetime(start).strftime("%Y%m%d")
    if end is None:
        end_date = pd.Timestamp.today().strftime("%Y%m%d")
    else:
        end_date = pd.to_datetime(end).strftime("%Y%m%d")

    con = pdblp.BCon(port=8194, timeout=20)
    con.start()
    try:
        raw = con.bdh(tickers, field, start_date, end_date)
    finally:
        con.stop()

    # raw has a MultiIndex column (ticker, field) — select just the field level
    df = raw.xs(field, axis=1, level=1)

    validate_ts(df)
    return df
