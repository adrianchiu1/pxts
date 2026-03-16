# tests/_verify_07_02_dual.py
import pandas as pd
import matplotlib
matplotlib.use("Agg")
from pxts.plots import tsplot_dual, LEFT_COLOR, RIGHT_COLOR

idx = pd.date_range("2024-01-01", periods=5, freq="D")
df = pd.DataFrame({"A": [1.0, 2.0, 3.0, 2.5, 1.5], "B": [5.0, 4.0, 3.0, 4.5, 5.5]}, index=idx)

# Range selector on dual
fig = tsplot_dual(df, left=["A"], right=["B"], backend="plotly")
rs = fig.layout.xaxis.rangeselector
assert rs is not None, "dual: rangeselector missing"
assert len(rs.buttons) == 6, f"expected 6 buttons, got {len(rs.buttons)}"

# Rangeslider default on
assert fig.layout.xaxis.rangeslider.visible is True, "dual: rangeslider should be visible"

# Rangeslider opt-out
fig2 = tsplot_dual(df, left=["A"], right=["B"], rangeslider=False, backend="plotly")
assert fig2.layout.xaxis.rangeslider.visible is False

# left_label
fig3 = tsplot_dual(df, left=["A"], right=["B"], left_label="Energy", backend="plotly")
assert fig3.layout.yaxis.title.text == "Energy", f"left label: {fig3.layout.yaxis.title.text!r}"
assert fig3.layout.yaxis.title.font.color == LEFT_COLOR, (
    f"left label color: {fig3.layout.yaxis.title.font.color!r}"
)

# right_label
fig4 = tsplot_dual(df, left=["A"], right=["B"], right_label="Steam", backend="plotly")
assert fig4.layout.yaxis2.title.text == "Steam", f"right label: {fig4.layout.yaxis2.title.text!r}"
assert fig4.layout.yaxis2.title.font.color == RIGHT_COLOR, (
    f"right label color: {fig4.layout.yaxis2.title.font.color!r}"
)

# Matplotlib no error
import matplotlib.figure
fig5 = tsplot_dual(df, left=["A"], right=["B"], left_label="LHS", right_label="RHS",
                   backend="matplotlib")
assert isinstance(fig5, matplotlib.figure.Figure)
import matplotlib.pyplot as plt
plt.close(fig5)

print("_verify_07_02_dual OK")
