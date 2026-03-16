# tests/_verify_07_03.py
import pandas as pd
import matplotlib
matplotlib.use("Agg")
from pxts.plots import tsplot, tsplot_dual, _validate_plot_params, add_annotation
import pytest

idx = pd.date_range("2024-01-01", periods=5, freq="D")
df = pd.DataFrame({"A": [1.0, 2.0, 3.0, 2.5, 1.5], "B": [5.0, 4.0, 3.0, 4.5, 5.5]}, index=idx)

# tsplot annotation adds text
fig = tsplot(df, annotations=[{"x": "2024-01-03", "text": "Peak"}], backend="plotly")
texts = [a.text for a in fig.layout.annotations]
assert any("Peak" in t for t in texts), f"'Peak' not found in {texts}"

# tsplot_dual annotation with col
fig2 = tsplot_dual(df, left=["A"], right=["B"],
                   annotations=[{"x": "2024-01-03", "text": "E", "col": "A"}],
                   backend="plotly")
texts2 = [a.text for a in fig2.layout.annotations]
assert any("E" in t for t in texts2), f"'E' not found in {texts2}"

# add_annotation adds to existing figure
fig3 = tsplot(df, backend="plotly")
count_before = len(fig3.layout.annotations)
add_annotation(fig3, "2024-01-03", text="Event")
assert len(fig3.layout.annotations) == count_before + 1

# _validate_plot_params raises ValueError for bad annotations
try:
    _validate_plot_params(None, None, "", "", None, caller="tsplot", annotations="bad")
    assert False, "should have raised ValueError"
except ValueError as e:
    assert "annotations" in str(e)

try:
    _validate_plot_params(None, None, "", "", None, caller="tsplot",
                          annotations=[{"x": "2024"}])
    assert False, "should have raised ValueError"
except ValueError as e:
    assert "annotations" in str(e)

print("_verify_07_03 OK")
