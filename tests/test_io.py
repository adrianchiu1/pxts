"""Unit and integration tests for pxts.io: read_ts, write_ts, _detect_date_format."""
import pandas as pd
import pytest
from pathlib import Path

from pxts.io import read_ts, write_ts, _detect_date_format
from pxts.exceptions import pxtsValidationError


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def write_csv(tmp_path, rows, filename="test.csv"):
    """Write a list of row strings to a temp CSV file, return the Path."""
    path = tmp_path / filename
    path.write_text("\n".join(rows))
    return path


# ---------------------------------------------------------------------------
# _detect_date_format — unit tests (no file I/O)
# ---------------------------------------------------------------------------

class TestDetectDateFormat:
    def test_iso_hyphen(self):
        assert _detect_date_format("2024-01-15") == ("ISO8601", False)

    def test_iso_slash(self):
        assert _detect_date_format("2024/01/15") == ("ISO8601", False)

    def test_uk_format_first_gt_12(self):
        """First part > 12 → DD/MM/YYYY (UK)."""
        assert _detect_date_format("15/01/2024") == ("%d/%m/%Y", True)

    def test_us_format_second_gt_12(self):
        """Second part > 12 → MM/DD/YYYY (US)."""
        assert _detect_date_format("01/15/2024") == ("%m/%d/%Y", False)

    def test_ambiguous_defaults_to_us(self):
        """Both parts ≤ 12 → ambiguous → defaults to US format."""
        # TODO(Phase-2): update to assert UserWarning when FIX-01 lands
        assert _detect_date_format("01/02/2024") == ("%m/%d/%Y", False)

    def test_fallback_non_date(self):
        """Unrecognised string → fallback mixed."""
        assert _detect_date_format("not-a-date") == ("mixed", False)


# ---------------------------------------------------------------------------
# read_ts — integration tests using tmp files
# ---------------------------------------------------------------------------

class TestReadTs:
    def test_iso_csv(self, tmp_path):
        """ISO 8601 (YYYY-MM-DD) CSV produces correct DatetimeIndex."""
        rows = ["date,A,B", "2024-01-15,1.0,5.0", "2024-01-16,2.0,4.0"]
        path = write_csv(tmp_path, rows)
        df = read_ts(path)
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index[0] == pd.Timestamp("2024-01-15")
        assert df.index[1] == pd.Timestamp("2024-01-16")

    def test_us_slash_csv(self, tmp_path):
        """US slash format (MM/DD/YYYY, second > 12) → correct dates."""
        rows = ["date,A,B", "01/15/2024,1.0,5.0", "01/16/2024,2.0,4.0"]
        path = write_csv(tmp_path, rows)
        df = read_ts(path)
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index[0] == pd.Timestamp("2024-01-15")

    def test_uk_slash_csv(self, tmp_path):
        """UK slash format (DD/MM/YYYY, first > 12) → correct dates."""
        rows = ["date,A,B", "15/01/2024,1.0,5.0", "16/01/2024,2.0,4.0"]
        path = write_csv(tmp_path, rows)
        df = read_ts(path)
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index[0] == pd.Timestamp("2024-01-15")

    def test_ambiguous_slash_csv_treated_as_us(self, tmp_path):
        """Ambiguous slash date (01/02/2024) silently defaults to US — no crash."""
        # TODO(Phase-2): update to assert UserWarning when FIX-01 lands
        rows = ["date,A,B", "01/02/2024,1.0,5.0", "01/03/2024,2.0,4.0"]
        path = write_csv(tmp_path, rows)
        df = read_ts(path)
        assert isinstance(df.index, pd.DatetimeIndex)
        # US default: 01/02/2024 → January 2, 2024
        assert df.index[0] == pd.Timestamp("2024-01-02")

    def test_explicit_date_format_overrides_detection(self, tmp_path):
        """Explicit date_format param bypasses auto-detection."""
        rows = ["date,A,B", "2024-01-15,1.0,5.0", "2024-01-16,2.0,4.0"]
        path = write_csv(tmp_path, rows)
        df = read_ts(path, date_format="%Y-%m-%d")
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index[0] == pd.Timestamp("2024-01-15")

    def test_tz_param_produces_tz_aware_index(self, tmp_path):
        """tz param localizes a tz-naive index to the specified timezone."""
        rows = ["date,A,B", "2024-01-15,1.0,5.0", "2024-01-16,2.0,4.0"]
        path = write_csv(tmp_path, rows)
        df = read_ts(path, tz="UTC")
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.tz is not None
        assert str(df.index.tz) == "UTC"


# ---------------------------------------------------------------------------
# write_ts — tests
# ---------------------------------------------------------------------------

class TestWriteTs:
    def test_valid_df_creates_csv(self, ts_df, tmp_path):
        """write_ts creates a CSV file at the given path."""
        path = tmp_path / "out.csv"
        write_ts(ts_df, path)
        assert path.exists()

    def test_first_column_is_iso_datetime(self, ts_df, tmp_path):
        """Default output has ISO-formatted datetime strings in the first column."""
        path = tmp_path / "out.csv"
        write_ts(ts_df, path)
        content = path.read_text()
        lines = content.strip().split("\n")
        # First data row's first column should be ISO 8601-like
        first_data = lines[1].split(",")[0]
        # Should start with the year
        assert first_data.startswith("2024-01-01")

    def test_non_datetime_index_raises(self, bad_df, tmp_path):
        """write_ts raises pxtsValidationError for a non-DatetimeIndex DataFrame."""
        path = tmp_path / "bad.csv"
        with pytest.raises(pxtsValidationError):
            write_ts(bad_df, path)

    def test_custom_date_format_respected(self, ts_df, tmp_path):
        """Custom date_format is written to the CSV output."""
        path = tmp_path / "out.csv"
        write_ts(ts_df, path, date_format="%Y-%m-%d")
        content = path.read_text()
        lines = content.strip().split("\n")
        first_data = lines[1].split(",")[0]
        # Should match YYYY-MM-DD exactly (no time component)
        assert first_data == "2024-01-01"

    def test_round_trip(self, ts_df, tmp_path):
        """Round-trip: write_ts then read_ts produces index equal to original."""
        path = tmp_path / "round_trip.csv"
        write_ts(ts_df, path)
        result = read_ts(path)
        # Compare normalized dates (strip time/tz for comparison)
        assert (result.index.normalize() == ts_df.index.normalize()).all()
        # Column values should match
        for col in ts_df.columns:
            assert list(result[col]) == list(ts_df[col])
