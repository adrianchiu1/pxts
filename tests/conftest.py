"""Shared pytest fixtures for the pxts test suite."""
import pandas as pd
import pytest


@pytest.fixture(scope="session")
def ts_df():
    """Minimal realistic DataFrame with DatetimeIndex for testing pxts functions."""
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame(
        {"A": [1.0, 2.0, 3.0, 4.0, 5.0], "B": [5.0, 4.0, 3.0, 2.0, 1.0]},
        index=dates,
    )


@pytest.fixture(scope="session")
def ts_df2():
    """Second DataFrame with same DatetimeIndex frequency for tsgrid tests."""
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame(
        {"C": [10.0, 12.0, 11.0, 14.0, 13.0], "D": [3.0, 3.5, 2.5, 4.0, 3.8]},
        index=dates,
    )


@pytest.fixture(scope="session")
def bad_df():
    """DataFrame with a plain RangeIndex (no DatetimeIndex) to test validation errors."""
    return pd.DataFrame({"A": [1, 2, 3]})

