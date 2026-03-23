"""Unit tests for pxts.io.read_mb — Macrobond time series data fetcher.

macrobond_data_api is mocked throughout so no Macrobond subscription is required.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

import pandas as pd
import pytest
from unittest.mock import MagicMock, patch, call

from pxts.io import read_mb


# ---------------------------------------------------------------------------
# Helpers — build mock Macrobond series entities
# ---------------------------------------------------------------------------


def _make_series_entity(name: str, dates: list[str], values: list[float], *, is_error=False, error_message=None):
    """Build a mock Macrobond Series entity."""
    entity = MagicMock()
    entity.name = name
    entity.is_error = is_error
    entity.error_message = error_message
    entity.dates = [datetime.fromisoformat(d) for d in dates]
    entity.values = values
    return entity


def _make_mock_mda(entities: list):
    """Create a mock macrobond_data_api module whose get_series returns entities."""
    mock_mda = MagicMock()
    mock_mda.get_series.return_value = entities
    return mock_mda


def _make_unified_df(series_names: list[str], dates: list[str], data: dict):
    """Build the DataFrame that get_unified_series().to_pd_data_frame() returns.

    Macrobond unified results have a 'Date' column followed by value columns.
    """
    df = pd.DataFrame({"Date": dates, **data})
    return df


# ---------------------------------------------------------------------------
# Tests — simple mode (get_series)
# ---------------------------------------------------------------------------


class TestReadMbSimple:
    def test_single_series(self):
        """Single series: result has correct column and DatetimeIndex."""
        entities = [
            _make_series_entity("usgdp", ["2024-01-01", "2024-04-01"], [100.0, 101.0]),
        ]
        mock_mda = _make_mock_mda(entities)
        with patch.dict(sys.modules, {"macrobond_data_api": mock_mda}):
            df = read_mb("usgdp")

        assert list(df.columns) == ["usgdp"]
        assert isinstance(df.index, pd.DatetimeIndex)
        assert len(df) == 2

    def test_multi_series(self):
        """Multiple series: outer join produces all dates from both."""
        entities = [
            _make_series_entity("usgdp", ["2024-01-01", "2024-04-01"], [100.0, 101.0]),
            _make_series_entity("gbgdp", ["2024-01-01", "2024-04-01", "2024-07-01"], [200.0, 201.0, 202.0]),
        ]
        mock_mda = _make_mock_mda(entities)
        with patch.dict(sys.modules, {"macrobond_data_api": mock_mda}):
            df = read_mb(["usgdp", "gbgdp"])

        assert list(df.columns) == ["usgdp", "gbgdp"]
        assert isinstance(df.index, pd.DatetimeIndex)
        # Outer join: 3 dates (usgdp has NaN for 2024-07-01)
        assert len(df) == 3
        assert pd.isna(df.loc[pd.Timestamp("2024-07-01"), "usgdp"])

    def test_string_ticker_coerced_to_list(self):
        """A single string series_name is coerced to a list."""
        entities = [
            _make_series_entity("usgdp", ["2024-01-01"], [100.0]),
        ]
        mock_mda = _make_mock_mda(entities)
        with patch.dict(sys.modules, {"macrobond_data_api": mock_mda}):
            df = read_mb("usgdp")

        mock_mda.get_series.assert_called_once_with(["usgdp"])

    def test_start_filter(self):
        """Start date filters the result in simple mode."""
        entities = [
            _make_series_entity("usgdp", ["2024-01-01", "2024-04-01", "2024-07-01"], [100.0, 101.0, 102.0]),
        ]
        mock_mda = _make_mock_mda(entities)
        with patch.dict(sys.modules, {"macrobond_data_api": mock_mda}):
            df = read_mb(["usgdp"], start="2024-04-01")

        assert len(df) == 2
        assert df.index[0] == pd.Timestamp("2024-04-01")

    def test_end_filter(self):
        """End date filters the result in simple mode."""
        entities = [
            _make_series_entity("usgdp", ["2024-01-01", "2024-04-01", "2024-07-01"], [100.0, 101.0, 102.0]),
        ]
        mock_mda = _make_mock_mda(entities)
        with patch.dict(sys.modules, {"macrobond_data_api": mock_mda}):
            df = read_mb(["usgdp"], end="2024-04-01")

        assert len(df) == 2
        assert df.index[-1] == pd.Timestamp("2024-04-01")

    def test_error_series_skipped_with_warning(self):
        """Series that return errors are skipped and a warning is issued."""
        entities = [
            _make_series_entity("usgdp", ["2024-01-01"], [100.0]),
            _make_series_entity("badname", [], [], is_error=True, error_message="Not found"),
        ]
        mock_mda = _make_mock_mda(entities)
        with patch.dict(sys.modules, {"macrobond_data_api": mock_mda}):
            with pytest.warns(UserWarning, match="badname"):
                df = read_mb(["usgdp", "badname"])

        assert list(df.columns) == ["usgdp"]

    def test_all_errors_returns_empty(self):
        """If all series error, return an empty DataFrame."""
        entities = [
            _make_series_entity("bad1", [], [], is_error=True, error_message="Not found"),
        ]
        mock_mda = _make_mock_mda(entities)
        with patch.dict(sys.modules, {"macrobond_data_api": mock_mda}):
            with pytest.warns(UserWarning):
                df = read_mb(["bad1"])

        assert len(df) == 0

    def test_importerror_without_macrobond(self):
        """ImportError with install hint is raised when macrobond-data-api is absent."""
        with patch.dict(sys.modules, {"macrobond_data_api": None}):
            with pytest.raises(ImportError, match=r"macrobond-data-api"):
                read_mb(["usgdp"])

    def test_output_passes_validate_ts(self):
        """Output DataFrame has pd.DatetimeIndex (validate_ts compliant)."""
        entities = [
            _make_series_entity("usgdp", ["2024-01-01", "2024-04-01", "2024-07-01"], [100.0, 101.0, 102.0]),
        ]
        mock_mda = _make_mock_mda(entities)
        with patch.dict(sys.modules, {"macrobond_data_api": mock_mda}):
            df = read_mb(["usgdp"])

        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.dtype.kind == "M"


# ---------------------------------------------------------------------------
# Tests — unified mode (get_unified_series)
# ---------------------------------------------------------------------------


class TestReadMbUnified:
    def _make_unified_mock(self, series_names, dates, data):
        """Set up a mock mda with get_unified_series returning a DataFrame."""
        mock_mda = MagicMock()
        result_df = _make_unified_df(series_names, dates, data)
        mock_result = MagicMock()
        mock_result.to_pd_data_frame.return_value = result_df
        mock_mda.get_unified_series.return_value = mock_result

        # Also mock the types/enums submodules so they can be imported
        mock_types = MagicMock()
        mock_enums = MagicMock()
        mock_common = MagicMock()
        mock_common.types = mock_types
        mock_common.enums = mock_enums
        return mock_mda, mock_types, mock_enums, mock_common

    def _patch_modules(self, mock_mda, mock_types, mock_enums, mock_common):
        return patch.dict(sys.modules, {
            "macrobond_data_api": mock_mda,
            "macrobond_data_api.common": mock_common,
            "macrobond_data_api.common.types": mock_types,
            "macrobond_data_api.common.enums": mock_enums,
        })

    def test_unified_basic(self):
        """Unified mode: returns aligned DataFrame with correct columns."""
        mock_mda, mock_types, mock_enums, mock_common = self._make_unified_mock(
            ["usgdp", "gbgdp"],
            ["2024-01-01", "2024-04-01"],
            {"usgdp": [100.0, 101.0], "gbgdp": [200.0, 201.0]},
        )
        with self._patch_modules(mock_mda, mock_types, mock_enums, mock_common):
            df = read_mb(["usgdp", "gbgdp"], unified=True)

        assert list(df.columns) == ["usgdp", "gbgdp"]
        assert isinstance(df.index, pd.DatetimeIndex)
        assert len(df) == 2

    def test_unified_calls_get_unified_series(self):
        """Unified mode calls get_unified_series, not get_series."""
        mock_mda, mock_types, mock_enums, mock_common = self._make_unified_mock(
            ["usgdp"],
            ["2024-01-01"],
            {"usgdp": [100.0]},
        )
        with self._patch_modules(mock_mda, mock_types, mock_enums, mock_common):
            read_mb(["usgdp"], unified=True)

        mock_mda.get_unified_series.assert_called_once()
        mock_mda.get_series.assert_not_called()

    def test_unified_passes_frequency(self):
        """Frequency kwarg is forwarded to get_unified_series."""
        mock_mda, mock_types, mock_enums, mock_common = self._make_unified_mock(
            ["usgdp"],
            ["2024-01-01"],
            {"usgdp": [100.0]},
        )
        mock_freq = MagicMock()
        with self._patch_modules(mock_mda, mock_types, mock_enums, mock_common):
            read_mb(["usgdp"], unified=True, frequency=mock_freq)

        call_kwargs = mock_mda.get_unified_series.call_args[1]
        assert call_kwargs["frequency"] is mock_freq

    def test_unified_passes_currency(self):
        """Currency kwarg is forwarded to get_unified_series."""
        mock_mda, mock_types, mock_enums, mock_common = self._make_unified_mock(
            ["usgdp"],
            ["2024-01-01"],
            {"usgdp": [100.0]},
        )
        with self._patch_modules(mock_mda, mock_types, mock_enums, mock_common):
            read_mb(["usgdp"], unified=True, currency="USD")

        call_kwargs = mock_mda.get_unified_series.call_args[1]
        assert call_kwargs["currency"] == "USD"

    def test_unified_passes_calendar_merge_mode(self):
        """CalendarMergeMode kwarg is forwarded to get_unified_series."""
        mock_mda, mock_types, mock_enums, mock_common = self._make_unified_mock(
            ["usgdp"],
            ["2024-01-01"],
            {"usgdp": [100.0]},
        )
        mock_mode = MagicMock()
        with self._patch_modules(mock_mda, mock_types, mock_enums, mock_common):
            read_mb(["usgdp"], unified=True, calendar_merge_mode=mock_mode)

        call_kwargs = mock_mda.get_unified_series.call_args[1]
        assert call_kwargs["calendar_merge_mode"] is mock_mode

    def test_simple_mode_does_not_call_unified(self):
        """Simple mode (unified=False) calls get_series, not get_unified_series."""
        entities = [
            _make_series_entity("usgdp", ["2024-01-01"], [100.0]),
        ]
        mock_mda = _make_mock_mda(entities)
        with patch.dict(sys.modules, {"macrobond_data_api": mock_mda}):
            read_mb(["usgdp"], unified=False)

        mock_mda.get_series.assert_called_once()
        mock_mda.get_unified_series.assert_not_called()
