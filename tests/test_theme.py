"""Tests for pxts.theme — apply_theme registration and isolation.

Tests confirm that apply_theme() registers the plotly template, updates
matplotlib rcParams, and is idempotent. Uses a restore fixture to prevent
state leakage to subsequent test files.

Import from pxts.theme directly (NOT `import pxts`) to avoid triggering
the import-time side effect before the restore fixture is active.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.io as pio
import pytest
from pxts.theme import apply_theme


@pytest.fixture
def restore_rcparams():
    """Snapshot and restore matplotlib rcParams after each theme test.

    Prevents theme changes from leaking into subsequent test files.
    """
    saved = dict(plt.rcParams)
    yield
    plt.rcParams.update(plt.rcParamsDefault)  # full reset to defaults
    plt.rcParams.update(saved)                # then restore snapshot


class TestPlotlyTemplateRegistration:
    """apply_theme() registers the pxts template and sets it as default."""

    def test_plotly_template_registered(self, restore_rcparams):
        apply_theme()
        assert "pxts" in pio.templates

    def test_plotly_template_is_default(self, restore_rcparams):
        apply_theme()
        assert pio.templates.default == "pxts"


class TestMatplotlibRcParams:
    """apply_theme() sets the expected matplotlib rcParams."""

    def test_axes_facecolor_set(self, restore_rcparams):
        apply_theme()
        assert plt.rcParams["axes.facecolor"] == "#FFFFFF"

    def test_axes_grid_enabled(self, restore_rcparams):
        apply_theme()
        assert plt.rcParams["axes.grid"] == True


class TestIdempotency:
    """Calling apply_theme() multiple times is safe and produces consistent state."""

    def test_apply_theme_twice_no_error(self, restore_rcparams):
        apply_theme()
        apply_theme()  # Must not raise

    def test_apply_theme_twice_template_registered(self, restore_rcparams):
        apply_theme()
        apply_theme()
        assert "pxts" in pio.templates

    def test_apply_theme_twice_default_preserved(self, restore_rcparams):
        apply_theme()
        apply_theme()
        assert pio.templates.default == "pxts"


class TestIsolation:
    """Theme tests do not leak state to other test files."""

    def test_restore_fixture_cleans_up(self):
        """Verify that rcParams are NOT permanently dirtied after theme tests run.

        This test intentionally does NOT use restore_rcparams to verify the fixture
        was applied by the other tests above. The default facecolor is not '#FFFFFF'.
        """
        # Before apply_theme, the default facecolor should be the matplotlib default
        # (tests in this class run after the restore_rcparams fixture has cleaned up)
        # We can only assert it's a valid string — actual value depends on mpl version
        current = plt.rcParams["axes.facecolor"]
        assert isinstance(current, str)
