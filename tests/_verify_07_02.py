# tests/_verify_07_02.py
import pandas as pd
import numpy as np
from pxts.plots import tsplot
from pxts.theme import DARK_BACKGROUND_COLOR
import matplotlib
matplotlib.use("Agg")

idx = pd.date_range("2024-01-01", periods=5, freq="D")
df = pd.DataFrame({"A": [1.0, 2.0, 3.0, 2.5, 1.5], "B": [5.0, 4.0, 3.0, 4.5, 5.5]}, index=idx)

# Range selector
fig = tsplot(df, backend="plotly")
rs = fig.layout.xaxis.rangeselector
assert rs is not None, "rangeselector missing"
assert len(rs.buttons) == 6, f"expected 6 buttons, got {len(rs.buttons)}"
labels = [b.label for b in rs.buttons]
for lbl in ["1M", "3M", "6M", "YTD", "1Y", "All"]:
    assert lbl in labels, f"button {lbl!r} missing"

# Rangeslider default on
assert fig.layout.xaxis.rangeslider.visible is True, "rangeslider should be visible by default"

# Rangeslider opt-out
fig2 = tsplot(df, rangeslider=False, backend="plotly")
assert fig2.layout.xaxis.rangeslider.visible is False, "rangeslider should be hidden"

# Dark theme
fig3 = tsplot(df, theme="dark", backend="plotly")
assert fig3.layout.paper_bgcolor == DARK_BACKGROUND_COLOR, (
    f"dark paper_bgcolor: {fig3.layout.paper_bgcolor}"
)

# Matplotlib no error
import matplotlib.figure
fig4 = tsplot(df, rangeslider=False, backend="matplotlib")
assert isinstance(fig4, matplotlib.figure.Figure)
import matplotlib.pyplot as plt
plt.close(fig4)

print("_verify_07_02 OK")
