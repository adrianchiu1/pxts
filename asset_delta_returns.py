"""
Asset delta-returns probability distribution explorer.

Distribution family: two-piece (split) t with ν=5 degrees of freedom.
  - Median fixed analytically at p50.
  - Left scale σ_lo solved so that CDF(p25) = 0.25 exactly.
  - Right scale σ_hi solved so that CDF(p75) = 0.75 exactly.
  - No numerical optimisation required; all parameters are in closed form.

CDF:
    F(x) = T_5((x - m) / σ_lo)   for x < m
    F(x) = T_5((x - m) / σ_hi)   for x ≥ m

PPF:
    Q(p) = m + σ_lo * t5.ppf(p)  for p < 0.5
    Q(p) = m + σ_hi * t5.ppf(p)  for p ≥ 0.5
"""

import numpy as np
import plotly.graph_objects as go
from scipy.stats import t as scipy_t
from scipy.interpolate import CubicSpline

# ─── Data ─────────────────────────────────────────────────────────────────────
# Columns: 25d_up, 50d (baseline), 25d_down — values are return percentages.
DATA = {
    "Asset 1": {"25d_up": 1.5,  "50d": 2.0,  "25d_down": 0.1},
    "Asset 2": {"25d_up": 2.3,  "50d": 2.5,  "25d_down": 0.3},
    "Asset 3": {"25d_up": 6.0,  "50d": 3.3,  "25d_down": 0.9},
    "Asset 4": {"25d_up": 7.55, "50d": 4.8,  "25d_down": 1.15},
}
ASSET_NAMES = list(DATA.keys())
DF = 5  # degrees of freedom (fat tails)


# ─── Split-t distribution ─────────────────────────────────────────────────────

class SplitT:
    """
    Analytically fitted two-piece t-distribution.
    p25 and p75 are matched exactly; p50 is the median by construction.
    """

    def __init__(self, p25: float, p50: float, p75: float, df: int = DF):
        self.m = p50
        self.df = df
        q25 = scipy_t.ppf(0.25, df)  # < 0
        q75 = scipy_t.ppf(0.75, df)  # > 0
        self.sigma_lo = (p25 - p50) / q25   # both negative → positive result
        self.sigma_hi = (p75 - p50) / q75   # both positive → positive result

    def pdf(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        return np.where(
            x < self.m,
            scipy_t.pdf((x - self.m) / self.sigma_lo, self.df) / self.sigma_lo,
            scipy_t.pdf((x - self.m) / self.sigma_hi, self.df) / self.sigma_hi,
        )

    def cdf(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        return np.where(
            x < self.m,
            scipy_t.cdf((x - self.m) / self.sigma_lo, self.df),
            scipy_t.cdf((x - self.m) / self.sigma_hi, self.df),
        )

    def ppf(self, p: np.ndarray) -> np.ndarray:
        p = np.asarray(p, dtype=float)
        return np.where(
            p < 0.5,
            self.m + self.sigma_lo * scipy_t.ppf(p, self.df),
            self.m + self.sigma_hi * scipy_t.ppf(p, self.df),
        )


# ─── Fit distributions ────────────────────────────────────────────────────────

def extract_percentiles(d: dict) -> tuple:
    """Sort raw scenario values: smallest→p25, middle→p50, largest→p75."""
    vals = sorted([d["25d_up"], d["50d"], d["25d_down"]])
    return vals[0], vals[1], vals[2]


fitted: dict[str, SplitT] = {}
for name in ASSET_NAMES:
    p25, p50, p75 = extract_percentiles(DATA[name])
    fitted[name] = SplitT(p25, p50, p75)
    dist = fitted[name]
    print(
        f"{name}: p25={p25}, p50={p50}, p75={p75}"
        f" | σ_lo={dist.sigma_lo:.3f}, σ_hi={dist.sigma_hi:.3f}"
    )
    print(
        f"  verify: p25={dist.ppf(0.25):.4f}, "
        f"p50={dist.ppf(0.50):.4f}, p75={dist.ppf(0.75):.4f}"
    )


# ─── Chart 1: Overlapping PDFs ────────────────────────────────────────────────

COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

x_lo = min(d.ppf(0.001) for d in fitted.values())
x_hi = max(d.ppf(0.999) for d in fitted.values())
x_pdf = np.linspace(x_lo, x_hi, 600)

fig1 = go.Figure()
for i, name in enumerate(ASSET_NAMES):
    hex_c = COLORS[i].lstrip("#")
    r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
    fig1.add_trace(
        go.Scatter(
            x=x_pdf,
            y=fitted[name].pdf(x_pdf),
            mode="lines",
            name=name,
            line=dict(color=COLORS[i], width=2.5),
            fill="tozeroy",
            fillcolor=f"rgba({r},{g},{b},0.12)",
        )
    )

fig1.update_layout(
    title="Asset Return Distributions (Split-t, ν=5)",
    xaxis_title="Return (%)",
    yaxis_title="Probability Density",
    template="plotly_white",
    legend=dict(x=0.75, y=0.98),
    font=dict(size=13),
)


# ─── Chart 2: Continuous blue gradient band + 3 scenario lines ───────────────

X_POS = np.array([0, 1, 2, 3])   # asset x positions
x_fine = np.linspace(0, 3, 400)  # dense interpolation grid

N_BANDS = 200
p_edges = np.linspace(0.05, 0.95, N_BANDS + 1)

# Precompute quantiles at every band edge for each asset (vectorised)
quantile_matrix = {name: fitted[name].ppf(p_edges) for name in ASSET_NAMES}


def p_to_blue(p_mid: float) -> str:
    """
    Map a percentile to a blue shade.
    p50 → darkest blue  (8, 48, 107)
    p5 / p95 → lightest blue (198, 219, 239)
    """
    t = float(np.clip(abs(p_mid - 0.5) / 0.45, 0, 1))
    r = int(8   + t * (198 - 8))
    g = int(48  + t * (219 - 48))
    b = int(107 + t * (239 - 107))
    return f"rgb({r},{g},{b})"


fig2 = go.Figure()

# --- Gradient bands (p5 → p95) -----------------------------------------------
for i in range(N_BANDS):
    p_lo = p_edges[i]
    p_hi = p_edges[i + 1]
    color = p_to_blue((p_lo + p_hi) / 2.0)

    y_lo = np.array([quantile_matrix[name][i]     for name in ASSET_NAMES])
    y_hi = np.array([quantile_matrix[name][i + 1] for name in ASSET_NAMES])

    y_lo_f = CubicSpline(X_POS, y_lo, bc_type="natural")(x_fine)
    y_hi_f = CubicSpline(X_POS, y_hi, bc_type="natural")(x_fine)

    fig2.add_trace(
        go.Scatter(
            x=np.concatenate([x_fine, x_fine[::-1]]),
            y=np.concatenate([y_hi_f, y_lo_f[::-1]]),
            fill="toself",
            fillcolor=color,
            line=dict(width=0, color=color),
            showlegend=False,
            hoverinfo="skip",
        )
    )

# --- 3 scenario lines (raw column values, straight lines) ---------------------
SCENARIO_STYLES = {
    "25d Up":       dict(color="#e6550d", width=2,   dash="solid"),   # orange
    "50d Baseline": dict(color="#31a354", width=2.5, dash="solid"),   # green
    "25d Down":     dict(color="#756bb1", width=2,   dash="solid"),   # purple
}
SCENARIO_KEYS = {
    "25d Up":       "25d_up",
    "50d Baseline": "50d",
    "25d Down":     "25d_down",
}

for label, col_key in SCENARIO_KEYS.items():
    y_vals = [DATA[name][col_key] for name in ASSET_NAMES]
    style = SCENARIO_STYLES[label]
    fig2.add_trace(
        go.Scatter(
            x=X_POS,
            y=y_vals,
            mode="lines+markers",
            name=label,
            line=dict(color=style["color"], width=style["width"], dash=style["dash"]),
            marker=dict(size=8, color=style["color"]),
        )
    )

fig2.update_layout(
    title="Asset Returns: Probability Bands & Scenarios (Split-t, ν=5)",
    xaxis=dict(
        title="Asset",
        tickmode="array",
        tickvals=list(X_POS),
        ticktext=ASSET_NAMES,
    ),
    yaxis_title="Return (%)",
    template="plotly_white",
    legend=dict(x=0.02, y=0.98),
    font=dict(size=13),
)

fig1.show()
fig2.show()
