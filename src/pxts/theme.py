"""pxts theme module: shared visual theme for plotly and matplotlib backends.

Apply the pxts finance-themed, colorblind-accessible palette and consistent
styling to both backends. Called once at pxts import time via apply_theme().

Color palette source: Wong, B. (2011). Points of view: Color blindness.
Nature Methods, 8(6), 441. doi:10.1038/nmeth.1618
Okabe-Ito/Wong 8-color palette — verified for deuteranopia and protanopia.
Blue leads per finance convention (Bloomberg/TradingView primary series color).
"""

# ---------------------------------------------------------------------------
# Color palette constants
# ---------------------------------------------------------------------------

# FT data visualization palette (default).
# Source: FT Visual Vocabulary / o-colors.
FT_COLORS: list = [
    "#0F5499",  # Oxford (dark blue) — primary series
    "#EB5E8D",  # Candy (pink)
    "#00A0AF",  # Teal
    "#FF764D",  # Mandarin (orange)
    "#990F3D",  # Claret (dark red)
    "#96CC28",  # Wasabi (green)
]

# Okabe-Ito colorblind-safe palette (alternative).
# Source: Wong (2011) Nature Methods 8(6):441, doi:10.1038/nmeth.1618
# All 7 colors are distinguishable for deuteranopia and protanopia.
OKABE_ITO_COLORS: list = [
    "#0072B2",  # Blue
    "#D55E00",  # Vermillion
    "#56B4E9",  # Sky Blue
    "#009E73",  # Bluish Green
    "#E69F00",  # Orange
    "#CC79A7",  # Reddish Purple
    "#000000",  # Black
]

# Default palette — FT style.
pxts_COLORS: list = list(FT_COLORS)

# Fallback: plotly's built-in qualitative.Safe palette (24 colors, colorblind-friendly).
# Used when series count exceeds len(pxts_COLORS).
FALLBACK_PALETTE_NAME: str = "Safe"  # pc.qualitative.Safe

# Grid and background
BACKGROUND_COLOR: str = "#FFFFFF"  # White background
GRID_COLOR: str = "#E5E5E5"        # Subtle gray gridlines
GRID_ALPHA: float = 0.6

# FT-style constants
FT_FONT_COLOR: str = "#33302E"     # Warm dark charcoal (Financial Times style)
ACCENT_LINE_WIDTH: float = 3.0     # Top accent line thickness

# Dark theme colors (used when theme='dark' is passed to tsplot/tsplot_dual)
DARK_BACKGROUND_COLOR: str = "#1a1a2e"    # Deep navy background
DARK_PLOT_COLOR: str = "#16213e"          # Slightly lighter navy for plot area
DARK_GRID_COLOR: str = "#2d2d5a"          # Muted purple-navy grid
DARK_FONT_COLOR: str = "#e0e0e0"          # Light gray text for readability

# Font — Outfit from Google Fonts; degrades to Helvetica/Arial.
DEFAULT_FONT_SIZE: int = 14
FONT_FAMILY: str = "Outfit, Helvetica Neue, Helvetica, Arial, sans-serif"
OUTFIT_FONT_URL: str = "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap"

# Chart dimension defaults (FT-style: 600px wide, 1.5 aspect ratio)
DEFAULT_CHART_WIDTH: int = 550
DEFAULT_ASPECT_RATIO: float = 1.5

# Accent line: short bar at top-left (pixels)
ACCENT_LINE_LENGTH: int = 60


# ---------------------------------------------------------------------------
# Backend-specific theme application
# ---------------------------------------------------------------------------

def _load_outfit_font() -> None:
    """Load the Outfit Google Font for use in notebooks and matplotlib.

    In Jupyter: injects a <style> tag with @import for the font.
    For matplotlib: downloads the .ttf and registers it with font_manager.
    Silently skips on any failure (network, permissions, etc.).
    """
    # Jupyter / IPython — inject CSS @import
    try:
        from IPython.display import display, HTML
        display(HTML(
            f'<style>@import url("{OUTFIT_FONT_URL}");</style>'
        ))
    except Exception:
        pass

    # matplotlib — download and register the font
    try:
        import matplotlib.font_manager as fm
        from pathlib import Path
        import urllib.request
        import tempfile

        # Check if Outfit is already registered
        available = {f.name for f in fm.fontManager.ttflist}
        if "Outfit" in available:
            return

        # Download a single weight (400 regular) .ttf from Google Fonts
        ttf_url = "https://fonts.gstatic.com/s/outfit/v11/QGYyz_MVcBeNP4NjuGObqx1XmO1I4e.ttf"
        font_dir = Path(tempfile.gettempdir()) / "pxts_fonts"
        font_dir.mkdir(exist_ok=True)
        font_path = font_dir / "Outfit-Regular.ttf"
        if not font_path.exists():
            urllib.request.urlretrieve(ttf_url, font_path)
        fm.fontManager.addfont(str(font_path))
    except Exception:
        pass


def _apply_plotly_theme() -> None:
    """Register and set the pxts plotly template as the session default."""
    try:
        import plotly.graph_objects as go
        import plotly.io as pio
        import plotly.colors as pc

        # Build combined colorway: pxts_colors + Safe fallback (deduplicated).
        safe_fallback = pc.qualitative.Safe  # List of hex strings
        combined_colorway = pxts_COLORS + [
            c for c in safe_fallback if c not in pxts_COLORS
        ]

        template = go.layout.Template(
            layout=go.Layout(
                paper_bgcolor=BACKGROUND_COLOR,
                plot_bgcolor=BACKGROUND_COLOR,
                colorway=combined_colorway,
                font=dict(family=FONT_FAMILY, size=DEFAULT_FONT_SIZE,
                          color=FT_FONT_COLOR),
                xaxis=dict(
                    showgrid=False,
                    zeroline=False,
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=GRID_COLOR,
                    zeroline=False,
                ),
                legend=dict(
                    orientation="h",
                    bgcolor="rgba(0,0,0,0)",
                    xanchor="left",
                    x=0,
                ),
                showlegend=True,
                margin=dict(l=60, r=40, t=50, b=50),
                autosize=True,
            )
        )

        pio.templates["pxts"] = template
        pio.templates.default = "pxts"

    except ImportError:
        pass  # plotly not installed; silently skip — backend module handles warning


def _apply_matplotlib_theme() -> None:
    """Apply the pxts visual theme to matplotlib via rcParams.update()."""
    try:
        import matplotlib.pyplot as plt
        from cycler import cycler

        plt.rcParams.update({
            # Font
            "font.size":        DEFAULT_FONT_SIZE,
            "axes.labelsize":   DEFAULT_FONT_SIZE,
            "axes.titlesize":   DEFAULT_FONT_SIZE + 1,
            "legend.fontsize":  DEFAULT_FONT_SIZE - 1,
            # Color cycle — FT palette, aligned with Plotly colorway
            "axes.prop_cycle":  cycler(color=pxts_COLORS),
        })

        # Apply date.converter rcParam inside its own try/except KeyError.
        # This key may not exist on matplotlib < ~3.7 (Pitfall 3 in RESEARCH.md).
        try:
            plt.rcParams["date.converter"] = "concise"
        except KeyError:
            pass  # matplotlib < ~3.7; plot functions apply per-axes formatter instead

    except ImportError:
        pass  # matplotlib not installed; silently skip


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_theme() -> None:
    """Apply the pxts visual theme to all available backends.

    Called once at pxts import time. Safe to call multiple times (idempotent).
    Silently skips backends that are not installed.

    Applies:
    - plotly: registers pio.templates['pxts'] and sets it as pio.templates.default
    - matplotlib: updates rcParams (white background, gray grid, pxts color cycle)

    Note: figure.figsize is NOT set — matplotlib is window-responsive per user decision.
    """
    _load_outfit_font()
    _apply_plotly_theme()
    _apply_matplotlib_theme()
