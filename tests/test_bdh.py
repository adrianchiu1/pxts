"""Unit tests for pxts.io.read_bdh — Bloomberg BDH historical data fetcher.

pdblp is mocked throughout so no Bloomberg terminal is required.
"""
from __future__ import annotations

import sys
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from pxts.io import read_bdh


def _make_bdh_response(tickers: list[str], field: str, dates: list[str]) -> pd.DataFrame:
    """Build a fake pdblp BCon.bdh() MultiIndex response.

    Returns a DataFrame with:
    - DatetimeIndex as index (rows = dates)
    - MultiIndex columns (ticker, field)
    matching the real pdblp.BCon.bdh() output format.
    """
    index = pd.to_datetime(dates)
    columns = pd.MultiIndex.from_tuples(
        [(t, field) for t in tickers], names=[None, None]
    )
    data = {
        (t, field): [float(i + j) for j, _ in enumerate(dates)]
        for i, t in enumerate(tickers)
    }
    return pd.DataFrame(data, index=index, columns=columns)


def _make_mock_pdblp(bdh_return_value):
    """Create a mock pdblp module with a BCon that returns bdh_return_value."""
    mock_pdblp = MagicMock()
    mock_con = MagicMock()
    mock_pdblp.BCon.return_value = mock_con
    mock_con.bdh.return_value = bdh_return_value
    return mock_pdblp, mock_con


class TestReadBdh:
    def test_happy_path_single_ticker(self):
        """Single ticker: result has correct column name and DatetimeIndex."""
        mock_pdblp, mock_con = _make_mock_pdblp(
            _make_bdh_response(["AAPL US Equity"], "PX_LAST", ["2024-01-02", "2024-01-03"])
        )
        with patch.dict(sys.modules, {"pdblp": mock_pdblp}):
            df = read_bdh(["AAPL US Equity"], "20240101")

        assert list(df.columns) == ["AAPL US Equity"]
        assert isinstance(df.index, pd.DatetimeIndex)
        assert len(df) == 2

    def test_multi_ticker(self):
        """Two tickers: result has two columns named after each ticker."""
        mock_pdblp, mock_con = _make_mock_pdblp(
            _make_bdh_response(
                ["AAPL US Equity", "MSFT US Equity"],
                "PX_LAST",
                ["2024-01-02", "2024-01-03"],
            )
        )
        with patch.dict(sys.modules, {"pdblp": mock_pdblp}):
            df = read_bdh(["AAPL US Equity", "MSFT US Equity"], "20240101")

        assert list(df.columns) == ["AAPL US Equity", "MSFT US Equity"]
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_start_date_conversion(self):
        """pd.Timestamp and string start dates both reach BCon.bdh() as 'YYYYMMDD'."""
        for start_input in [pd.Timestamp("2024-01-01"), "2024-01-01"]:
            mock_pdblp, mock_con = _make_mock_pdblp(
                _make_bdh_response(["AAPL US Equity"], "PX_LAST", ["2024-01-02"])
            )
            with patch.dict(sys.modules, {"pdblp": mock_pdblp}):
                read_bdh(["AAPL US Equity"], start_input)

            call_args = mock_con.bdh.call_args
            start_arg = call_args[0][2]
            assert start_arg == "20240101", (
                f"Expected '20240101' for input {start_input!r}, got {start_arg!r}"
            )

    def test_end_defaults_to_today(self):
        """When end=None, BCon.bdh() receives today's date as 'YYYYMMDD'."""
        expected_today = pd.Timestamp.today().strftime("%Y%m%d")
        mock_pdblp, mock_con = _make_mock_pdblp(
            _make_bdh_response(["AAPL US Equity"], "PX_LAST", ["2024-01-02"])
        )
        with patch.dict(sys.modules, {"pdblp": mock_pdblp}):
            read_bdh(["AAPL US Equity"], "20240101", end=None)

        call_args = mock_con.bdh.call_args
        end_arg = call_args[0][3]
        assert end_arg == expected_today

    def test_field_passthrough(self):
        """Custom field argument is forwarded to BCon.bdh()."""
        mock_pdblp, mock_con = _make_mock_pdblp(
            _make_bdh_response(["AAPL US Equity"], "PX_VOLUME", ["2024-01-02"])
        )
        with patch.dict(sys.modules, {"pdblp": mock_pdblp}):
            read_bdh(["AAPL US Equity"], "20240101", field="PX_VOLUME")

        call_args = mock_con.bdh.call_args
        field_arg = call_args[0][1]
        assert field_arg == "PX_VOLUME"

    def test_con_always_stopped(self):
        """BCon.stop() is called even when bdh() raises an exception."""
        mock_pdblp = MagicMock()
        mock_con = MagicMock()
        mock_pdblp.BCon.return_value = mock_con
        mock_con.bdh.side_effect = RuntimeError("connection lost")

        with patch.dict(sys.modules, {"pdblp": mock_pdblp}):
            with pytest.raises(RuntimeError, match="connection lost"):
                read_bdh(["AAPL US Equity"], "20240101")

        assert mock_con.stop.called, "BCon.stop() must be called even after bdh() raises"

    def test_importerror_without_pdblp(self):
        """ImportError with pip install hint is raised when pdblp is absent."""
        with patch.dict(sys.modules, {"pdblp": None}):
            with pytest.raises(ImportError, match=r"pip install pxts\[bloomberg\]"):
                read_bdh(["AAPL US Equity"], "20240101")

    def test_output_passes_validate_ts(self):
        """Output DataFrame has pd.DatetimeIndex (validate_ts compliant)."""
        mock_pdblp, mock_con = _make_mock_pdblp(
            _make_bdh_response(
                ["AAPL US Equity"],
                "PX_LAST",
                ["2024-01-02", "2024-01-03", "2024-01-04"],
            )
        )
        with patch.dict(sys.modules, {"pdblp": mock_pdblp}):
            df = read_bdh(["AAPL US Equity"], "20240101")

        assert isinstance(df.index, pd.DatetimeIndex)
        # validate_ts is called internally — if it raised, we'd never reach here
        assert df.index.dtype.kind == "M"  # 'M' = datetime64
