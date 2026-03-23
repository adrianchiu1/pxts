"""pxts I/O layer — read_ts, write_ts, read_bdh, and read_mb for CSV round-trips and data feeds.

Public API:
    read_ts(path, *, tz=None, date_format=None) -> pd.DataFrame
    write_ts(df, path, *, date_format=None) -> None
    read_bdh(tickers, start, field='PX_LAST', end=None) -> pd.DataFrame
    read_mb(series_names, *, unified=False, frequency=None, currency=None,
            calendar_merge_mode=None, start=None, end=None) -> pd.DataFrame

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
            "pdblp required for read_bdh(). Install with: pip install pdblp and https://www.bloomberg.com/professional/support/api-library/"
        )

    if isinstance(tickers, str):
        tickers = [tickers]

    start_date = pd.to_datetime(start).strftime("%Y%m%d")
    if end is None:
        end_date = pd.Timestamp.today().strftime("%Y%m%d")
    else:
        end_date = pd.to_datetime(end).strftime("%Y%m%d")

    # Establish a connection
    con = pdblp.BCon(port=8194, timeout=5000)
    con.start()

    # Get historical data for securities and fields
    try:
        raw = con.bdh(tickers, field, start_date, end_date)
    finally:
        con.stop()

    data = raw.loc[:,tickers]
    data.columns = tickers
    data.index = pd.to_datetime(data.index)

    return validate_ts(data)


def read_mb(
    series_names,
    *,
    unified: bool = False,
    frequency=None,
    currency: str | None = None,
    calendar_merge_mode=None,
    start=None,
    end=None,
) -> pd.DataFrame:
    """Fetch Macrobond time series data.

    Downloads one or more series from the Macrobond Data API and returns a
    wide-format DataFrame with a DatetimeIndex and one column per series.

    By default uses ``get_series`` for a simple fetch. When ``unified=True``,
    uses ``get_unified_series`` to align series to a common frequency and
    calendar — the alignment parameters (frequency, currency,
    calendar_merge_mode, start, end) are only used in unified mode.

    Requires macrobond-data-api (optional dependency). Install with:
        pip install pxts[macrobond]

    Parameters
    ----------
    series_names : str or list of str
        Macrobond series identifiers, e.g. ``['usgdp', 'gbgdp']``.
    unified : bool
        If True, use ``get_unified_series`` to align all series to a common
        frequency and calendar. If False (default), fetch raw series with
        ``get_series`` and outer-join on dates.
    frequency : SeriesFrequency or None
        Target frequency for unified mode (e.g. ``SeriesFrequency.ANNUAL``).
        Ignored when ``unified=False``.
    currency : str or None
        Target currency for unified mode (e.g. ``'USD'``).
        Ignored when ``unified=False``.
    calendar_merge_mode : CalendarMergeMode or None
        Calendar merge strategy for unified mode.
        Ignored when ``unified=False``.
    start : str, datetime, or StartOrEndPoint, or None
        Start date constraint. In unified mode, passed as ``start_point``
        (wrapped in ``StartOrEndPoint`` if a string/datetime is given).
        In non-unified mode, used to filter the returned DataFrame.
    end : str, datetime, or StartOrEndPoint, or None
        End date constraint. In unified mode, passed as ``end_point``.
        In non-unified mode, used to filter the returned DataFrame.

    Returns
    -------
    pd.DataFrame
        Wide-format DataFrame with DatetimeIndex (rows = dates,
        columns = series names).

    Raises
    ------
    ImportError
        If macrobond-data-api is not installed.
    pxtsValidationError
        If the returned DataFrame does not have a DatetimeIndex.
    """
    try:
        import macrobond_data_api as mda
    except ImportError:
        raise ImportError(
            "macrobond-data-api required for read_mb(). "
            "Install with: pip install macrobond-data-api"
        )

    if isinstance(series_names, str):
        series_names = [series_names]

    if unified:
        data = _read_mb_unified(
            mda, series_names,
            frequency=frequency,
            currency=currency,
            calendar_merge_mode=calendar_merge_mode,
            start=start,
            end=end,
        )
    else:
        data = _read_mb_simple(mda, series_names, start=start, end=end)

    return validate_ts(data)


def _read_mb_simple(mda, series_names, *, start=None, end=None) -> pd.DataFrame:
    """Fetch raw series via get_series and outer-join into a wide DataFrame."""
    entities = mda.get_series(series_names)

    frames = {}
    for entity in entities:
        if entity.is_error:
            warnings.warn(
                f"pxts: Macrobond series '{entity.name}' returned error: "
                f"{entity.error_message}",
                UserWarning,
                stacklevel=4,
            )
            continue
        s = pd.Series(
            data=entity.values,
            index=pd.to_datetime(entity.dates),
            name=entity.name,
        )
        frames[entity.name] = s

    if not frames:
        return pd.DataFrame(index=pd.DatetimeIndex([], name=None))

    data = pd.DataFrame(frames)
    data.index = pd.to_datetime(data.index)

    # Apply date filters if provided
    if start is not None:
        data = data.loc[pd.to_datetime(start):]
    if end is not None:
        data = data.loc[:pd.to_datetime(end)]

    return data


def _read_mb_unified(
    mda, series_names, *, frequency=None, currency=None,
    calendar_merge_mode=None, start=None, end=None,
) -> pd.DataFrame:
    """Fetch aligned series via get_unified_series."""
    from macrobond_data_api.common.types import SeriesEntry, StartOrEndPoint
    from macrobond_data_api.common.enums import SeriesFrequency

    entries = [SeriesEntry(name=n) for n in series_names]

    kwargs = {}
    if frequency is not None:
        kwargs["frequency"] = frequency
    if currency is not None:
        kwargs["currency"] = currency
    if calendar_merge_mode is not None:
        kwargs["calendar_merge_mode"] = calendar_merge_mode

    # Wrap plain date strings/datetimes into StartOrEndPoint
    if start is not None:
        if not isinstance(start, StartOrEndPoint):
            start = StartOrEndPoint(time=str(start), mode=None)
        kwargs["start_point"] = start
    if end is not None:
        if not isinstance(end, StartOrEndPoint):
            end = StartOrEndPoint(time=str(end), mode=None)
        kwargs["end_point"] = end

    result = mda.get_unified_series(*entries, **kwargs)
    df = result.to_pd_data_frame()

    # to_pd_data_frame returns first column as "Date" and rest as series values
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
    elif "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

    df.columns = series_names

    return df