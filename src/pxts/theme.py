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

# Primary "pxts branded" colors: Finance-themed Okabe-Ito adaptation.
# Blue (#0072B2) leads per finance convention (Bloomberg/TradingView primary series).
# All 8 colors are distinguishable for deuteranopia and protanopia (red-green weakness).
# Source: Wong (2011) Nature Methods 8(6):441, doi:10.1038/nmeth.1618
pxts_COLORS: list = [
    "#0072B2",  # Blue — primary series, matches finance convention
    "#E69F00",  # Orange
    "#56B4E9",  # Sky Blue
    "#009E73",  # Bluish Green
    "#D55E00",  # Vermillion (distinguishable from green for red-green weakness)
    "#CC79A7",  # Reddish Purple
    "#F0E442",  # Yellow (use last — low contrast on white background)
    "#000000",  # Black
]

# Fallback: plotly's built-in qualitative.Safe palette (24 colors, colorblind-friendly).
# Used when series count exceeds len(pxts_COLORS).
FALLBACK_PALETTE_NAME: str = "Safe"  # pc.qualitative.Safe

# Grid and background
BACKGROUND_COLOR: str = "#FFFFFF"  # White background
GRID_COLOR: str = "#E5E5E5"        # Subtle gray gridlines
GRID_ALPHA: float = 0.6

# Font
DEFAULT_FONT_SIZE: int = 12
FONT_FAMILY: str = "Arial, sans-serif"


# ---------------------------------------------------------------------------
# Backend-specific theme application
# ---------------------------------------------------------------------------

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
                font=dict(family=FONT_FAMILY, size=DEFAULT_FONT_SIZE),
                xaxis=dict(
                    showgrid=True,
                    gridcolor=GRID_COLOR,
                    zeroline=False,
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=GRID_COLOR,
                    zeroline=False,
                ),
                legend=dict(bgcolor="rgba(255,255,255,0.8)"),
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
            # Background and grid
            "axes.facecolor":   BACKGROUND_COLOR,
            "figure.facecolor": BACKGROUND_COLOR,
            "axes.edgecolor":   "#CCCCCC",
            "axes.grid":        True,
            "grid.color":       GRID_COLOR,
            "grid.alpha":       GRID_ALPHA,
            "grid.linestyle":   "-",
            "grid.linewidth":   0.6,
            # Font
            "font.size":        DEFAULT_FONT_SIZE,
            "axes.labelsize":   DEFAULT_FONT_SIZE,
            "axes.titlesize":   DEFAULT_FONT_SIZE + 1,
            "legend.fontsize":  DEFAULT_FONT_SIZE - 1,
            # Color cycle
            "axes.prop_cycle":  cycler(color=pxts_COLORS),
            # Figure size: NOT set — let matplotlib be window-responsive (per user decision)
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
    _apply_plotly_theme()
    _apply_matplotlib_theme()
