"""Backend detection module for pxts.

Detects the execution environment once at import time and exposes:
  - IS_JUPYTER: bool — True if running inside any IPython kernel (Jupyter-family)
  - _detect_jupyter(): internal detection function
  - get_backend(): returns 'plotly' or 'matplotlib' for the current environment

Every plot function calls get_backend() to know which library to use.
IS_JUPYTER is the fast cached path; get_backend() adds the library-availability check.

IS_JUPYTER is evaluated exactly once at module import time (module-level constant).
Subsequent calls to get_backend() read the cached value — they do NOT re-detect
the environment on each call. This makes backend selection a zero-cost lookup
after the first import.

Reload scenario: if pxts is first imported in a plain Python context and then a
script is run inside a Jupyter kernel without re-importing, IS_JUPYTER will still
reflect the environment at first import (False), not the current Jupyter context.
Conversely, if pxts was imported in a Jupyter session and a non-interactive script
then calls plot functions, IS_JUPYTER will be True from the earlier import. Users
who need dynamic re-detection must manually set `pxts._backend.IS_JUPYTER = True`
or `False` before calling plot functions rather than relying on the cached value.

Source: IPython documentation + https://github.com/ipython/ipython/issues/9732
Decision: use `get_ipython() is not None` (any non-None shell = Jupyter), per
user decision. Do NOT use ZMQInteractiveShell class name check — that is brittle
across IPython versions.
"""

import warnings


def _detect_jupyter() -> bool:
    """Return True if running inside any IPython kernel (Jupyter-family environment).

    Returns False if:
    - IPython is not installed (ImportError caught)
    - get_ipython() returns None (plain Python / script context)

    Returns True if:
    - get_ipython() returns any non-None value (Jupyter Notebook, JupyterLab,
      VS Code Jupyter extension, nteract, Google Colab, or any IPython kernel)
    """
    try:
        from IPython import get_ipython
        shell = get_ipython()
        return shell is not None
    except ImportError:
        return False  # IPython not installed — definitely not Jupyter


# Module-level constant: evaluated once at import time.
# No per-call overhead. Accepted trade-off: scripts that dynamically enter a
# notebook context won't re-detect (extremely rare in practice).
IS_JUPYTER: bool = _detect_jupyter()


def get_backend() -> str:
    """Return the active backend name: 'plotly' or 'matplotlib'.

    Backend selection logic:
    - IS_JUPYTER=True, plotly installed  → 'plotly'
    - IS_JUPYTER=True, plotly missing    → UserWarning, returns 'matplotlib'
    - IS_JUPYTER=False, matplotlib installed → 'matplotlib'
    - IS_JUPYTER=False, matplotlib missing   → raises ImportError

    Notes:
    - IS_JUPYTER is the module-level constant set at import time; get_backend()
      reads it but does NOT recompute it.
    - stacklevel=3: user code -> plot_ts -> get_backend -> warn, surfaces warning at plot_ts.
    """
    if IS_JUPYTER:
        try:
            import plotly  # noqa: F401
            return "plotly"
        except ImportError:
            warnings.warn(
                "pxts: plotly is not installed. Falling back to matplotlib for "
                "inline rendering. Install plotly with: pip install plotly",
                UserWarning,
                # stacklevel=3: user -> plot_ts -> get_backend -> warn; surfaces at plot_ts
                stacklevel=3,
            )
            return "matplotlib"
    else:
        try:
            import matplotlib  # noqa: F401
            return "matplotlib"
        except ImportError:
            raise ImportError(
                "pxts: matplotlib is required for non-Jupyter environments. "
                "Install it with: pip install matplotlib"
            )
