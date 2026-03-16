# Technology Stack

**Analysis Date:** 2026-03-13

## Languages

**Primary:**
- Python 3.9+ - All production and library code

## Runtime

**Environment:**
- Python 3.9 minimum (specified in `pyproject.toml`)

**Package Manager:**
- pip (via setuptools)
- Lockfile: Not detected (no `requirements.txt` or `poetry.lock`)

## Frameworks

**Core:**
- pandas 2.0+ - Time series DataFrame manipulation and datetime operations

**Visualization:**
- plotly 5.0+ (optional) - Interactive web-based visualization in Jupyter environments
- matplotlib 3.5+ (optional) - Static visualization for non-Jupyter environments

**Testing:**
- pytest 7.0+ - Unit test framework (configured in `pyproject.toml`)

**Build/Dev:**
- setuptools 42+ - Package build backend
- cycler - Color cycle management for matplotlib (imported in `src/pxts/theme.py`)

## Key Dependencies

**Critical:**
- pandas >= 2.0 - Core dependency for DatetimeIndex validation and time series operations
  - Used throughout: `src/pxts/core.py`, `src/pxts/io.py`, `src/pxts/accessor.py`
  - Provides DatetimeIndex, frequency inference, and offset aliases

**Visualization:**
- plotly >= 5.0 - Interactive charting backend for Jupyter environments
  - Imported conditionally in `src/pxts/_backend.py` and `src/pxts/plots.py`
  - Used in `src/pxts/plots.py` for plotly trace generation
  - Enables custom template registration via `plotly.io`

- matplotlib >= 3.5 - Static charting backend for scripts
  - Imported conditionally in `src/pxts/_backend.py` and `src/pxts/plots.py`
  - Used in `src/pxts/plots.py` for figure creation and axis manipulation
  - Supports rcParams theming in `src/pxts/theme.py`

**Optional (Dev only):**
- pytest >= 7.0 - Test execution (dev dependency)
- plotly >= 5.0 - Included in dev profile for testing both backends
- matplotlib >= 3.5 - Included in dev profile for testing both backends

## Configuration

**Environment:**
- Configured via `pyproject.toml` - Single source of truth
- Python version constraint: `requires-python = ">=3.9"`
- No `.env` files or environment variables required for runtime
- No configuration files detected (no setup.cfg, tox.ini, pytest.ini separate from pyproject.toml)

**Build:**
- `pyproject.toml` - PEP 518 compliant project metadata
  - Specifies build backend: `setuptools.build_meta`
  - Defines main dependency: pandas >= 2.0
  - Defines optional groups: `plot` (visualization), `dev` (testing + visualization)
  - Specifies package discovery: `src/` layout via `[tool.setuptools.packages.find]`
  - Configures pytest: `[tool.pytest.ini_options]` with testpaths = ["tests"]

## Platform Requirements

**Development:**
- Python 3.9+ with pip
- setuptools >= 42
- Optional: IPython/Jupyter kernel for `IS_JUPYTER` detection and interactive testing

**Production:**
- Python 3.9+
- pandas >= 2.0
- matplotlib (required for non-Jupyter execution; automatically installed if missing, raises ImportError)
- plotly (optional; if missing in Jupyter, falls back to matplotlib with UserWarning)

## Backend Selection

**Automatic Selection Logic:**
- Jupyter (IS_JUPYTER=True) + plotly installed → plotly backend
- Jupyter (IS_JUPYTER=True) + plotly missing → matplotlib backend (UserWarning)
- Non-Jupyter + matplotlib installed → matplotlib backend
- Non-Jupyter + matplotlib missing → raises ImportError

Implementation: `src/pxts/_backend.py` contains `get_backend()` and `_detect_jupyter()`

## Theming & Styling

**Theme Application:**
- Theme applied at import time via `apply_theme()` in `src/pxts/theme.py`
- Okabe-Ito 8-color palette (colorblind-accessible)
- White background (#FFFFFF) with subtle gray grid (#E5E5E5)
- Font: Arial, 12pt default

**plotly Theming:**
- Custom template "pxts" registered to `pio.templates['pxts']` and set as default
- Applied via `_apply_plotly_theme()` in `src/pxts/theme.py`

**matplotlib Theming:**
- rcParams updated globally via `_apply_matplotlib_theme()`
- Color cycle set via `cycler` package
- Axes colors, grid, font sizes configured

---

*Stack analysis: 2026-03-13*
