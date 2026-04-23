"""pxts I/O layer — read_csv, write_csv, read_bdh, and read_mb.

Public API:
    read_csv(path, *, tz=None, date_format=None) -> pd.DataFrame
    write_csv(df, path, *, date_format=None) -> None
    read_bdh(tickers, start, field='PX_LAST', end=None) -> pd.DataFrame
    read_mb(series) -> pd.DataFrame

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
                stacklevel=3,  # _detect_date_format -> read_csv -> user call site
            )
            return ("%d/%m/%Y", True)

    return ("mixed", False)


def read_csv(
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


def write_csv(
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
    start="2000-01-01",
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
    tickers : list of str, str, or dict
        Bloomberg ticker strings, e.g. ['AAPL US Equity', 'MSFT US Equity'].
        If a dict is provided, keys are the desired output column names and
        values are the Bloomberg tickers, e.g.
        {'Apple': 'AAPL US Equity', 'Microsoft': 'MSFT US Equity'}.
    start : str, datetime, or pd.Timestamp
        Start date (inclusive). Defaults to '2000-01-01'. Converted to 'YYYYMMDD' string internally.
    field : str
        Bloomberg field name. Defaults to 'PX_LAST'.
    end : str, datetime, pd.Timestamp, or None
        End date (inclusive). Defaults to today when None.

    Returns
    -------
    pd.DataFrame
        Wide-format DataFrame with DatetimeIndex (rows = dates,
        columns = Bloomberg ticker strings, or renamed columns when tickers
        is a dict).

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

    if isinstance(tickers, dict):
        rename_map = tickers  # {new_name: bloomberg_ticker}
        ticker_list = list(tickers.values())
    else:
        rename_map = None
        if isinstance(tickers, str):
            tickers = [tickers]
        ticker_list = tickers

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
        raw = con.bdh(ticker_list, field, start_date, end_date)
    finally:
        con.stop()

    data = raw.loc[:, ticker_list]
    data.columns = ticker_list
    data.index = pd.to_datetime(data.index)

    if rename_map is not None:
        # rename_map is {new_name: bloomberg_ticker}; invert for DataFrame.rename
        data = data.rename(columns={v: k for k, v in rename_map.items()})

    return validate_ts(data)


def read_mb(series) -> pd.DataFrame:
    """Fetch Macrobond historical time series data.

    Calls mda.get_series, normalises the response, and returns a validated
    wide-format DataFrame with a DatetimeIndex and one column per series.
    The full available history is returned; slice the result as needed.

    Requires macrobond_data_api (optional dependency). Install with:
        pip install macrobond-data-api

    Parameters
    ----------
    series : list of str, str, or dict
        Macrobond series identifiers, e.g. ['hg_c1_cl', 'hg_c2_cl'].
        If a dict is provided, keys are the desired output column names and
        values are the Macrobond series identifiers, e.g.
        {'Copper 1M': 'hg_c1_cl', 'Copper 2M': 'hg_c2_cl'}.

    Returns
    -------
    pd.DataFrame
        Wide-format DataFrame with DatetimeIndex (rows = dates, columns =
        FullDescription from Macrobond metadata, or dict keys when series is
        a dict). Series with disjoint date ranges are aligned on the union of
        all dates; missing observations are NaN.

    Raises
    ------
    ImportError
        If macrobond_data_api is not installed.
    ValueError
        If any requested series returns an error from the Macrobond API.
    RuntimeError
        If the get_series call itself raises an unexpected exception.
    pxtsValidationError
        If the returned DataFrame does not have a DatetimeIndex.
    """
    try:
        import macrobond_data_api as mda
    except ImportError:
        raise ImportError(
            "macrobond_data_api required for read_mb(). "
            "Install with: pip install macrobond-data-api"
        )

    if isinstance(series, dict):
        rename_map = series  # {new_name: macrobond_id}
        series_list = list(series.values())
    else:
        rename_map = None
        if isinstance(series, str):
            series = [series]
        series_list = list(series)

    # Fetch entities from Macrobond (notebook cell 1)
    try:
        entities = mda.get_series(series_list)
    except Exception as exc:
        raise RuntimeError(f"macrobond_data_api.get_series failed: {exc}") from exc

    # Defensive error check — get_series may return error entities rather than raising
    for entity in entities:
        if getattr(entity, "is_error", False):
            name = getattr(entity, "name", "(unknown)")
            msg = getattr(entity, "error_message", str(entity))
            raise ValueError(f"Macrobond series error — '{name}': {msg}")

    # Normalise to a flat DataFrame (notebook cell 2)
    df_raw = pd.json_normalize([x.to_dict() for x in entities])

    # Explode Dates and Values into long format (notebook cell 3)
    df_long = (
        df_raw.set_index(["metadata.PrimName", "metadata.FullDescription"])[
            ["Dates", "Values"]
        ]
        .apply(pd.Series.explode)
        .reset_index()
    )

    # PrimName → FullDescription mapping used for column ordering
    prim_to_full = dict(
        zip(df_raw["metadata.PrimName"], df_raw["metadata.FullDescription"])
    )

    # Pivot to wide format; mismatched date ranges produce NaN automatically
    df_wide = df_long.pivot(
        index="Dates", columns="metadata.FullDescription", values="Values"
    )
    df_wide.index = pd.to_datetime(df_wide.index)
    df_wide.index.name = "date"
    df_wide.columns.name = None
    df_wide = df_wide.astype(float)

    if rename_map is not None:
        full_to_new = {prim_to_full[v]: k for k, v in rename_map.items()}
        df_wide = df_wide.rename(columns=full_to_new)
        df_wide = df_wide[list(rename_map.keys())]
    else:
        ordered_cols = [prim_to_full[p] for p in series_list]
        df_wide = df_wide[ordered_cols]

    return validate_ts(df_wide)