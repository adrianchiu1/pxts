---
phase: quick-4
plan: 4
type: execute
wave: 1
depends_on: []
files_modified:
  - src/pxts/plots.py
  - tests/test_plots.py
autonomous: true
requirements: [QUICK-4]

must_haves:
  truths:
    - "tsplot(ylim=[0, 10]) restricts the y-axis to [0, 10] on both backends"
    - "tsplot(xlim=[date1, date2]) restricts the x-axis to that date range on both backends"
    - "tsplot_dual(ylim_lhs=[0, 5], ylim_rhs=[100, 200]) applies limits to each y-axis independently"
    - "tsplot_dual(xlim=[date1, date2]) restricts the x-axis on both backends"
    - "ylim/xlim=None applies no limit (current default behaviour preserved)"
    - "Passing a non-list/tuple or wrong-length value raises ValueError"
    - "Passing non-date-like values for xlim raises ValueError"
  artifacts:
    - path: "src/pxts/plots.py"
      provides: "ylim/xlim/ylim_lhs/ylim_rhs parameter handling"
      contains: "_validate_axis_limit"
    - path: "tests/test_plots.py"
      provides: "Tests for ylim/xlim/ylim_lhs/ylim_rhs"
  key_links:
    - from: "tsplot / tsplot_dual"
      to: "_plot_ts_mpl / _plot_ts_plotly / _plot_ts_dual_mpl / _plot_ts_dual_plotly"
      via: "ylim, xlim, ylim_lhs, ylim_rhs kwargs forwarded to helpers"
      pattern: "set_ylim|set_xlim|yaxis_range|xaxis_range"
---

<objective>
Add axis limit parameters to tsplot and tsplot_dual so users can control the visible
range of each axis without manual post-processing of the returned figure.

Purpose: Common researcher need — zooming in on a date range or y-axis band without
discarding other data. Cleaner than mutating the returned figure.
Output: plots.py accepts ylim/xlim (tsplot) and ylim_lhs/ylim_rhs/xlim (tsplot_dual),
validates them, and applies them in both matplotlib and plotly backends. Tests cover
valid use, None passthrough, and validation errors.
</objective>

<execution_context>
@C:/Users/adria/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/adria/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md
</context>

<interfaces>
<!-- Key signatures the executor needs from src/pxts/plots.py -->

Current tsplot signature:
```python
def tsplot(df, cols=None, title: str = "", subtitle: str = "",
           labels: bool = False, hlines=None, vlines=None,
           date_format=None, backend=None, **kwargs):
```

Current tsplot_dual signature:
```python
def tsplot_dual(df, left, right, title: str = "", subtitle: str = "",
                labels: bool = False, hlines=None, vlines=None,
                date_format=None, backend=None, **kwargs):
```

Existing validation helper pattern (to extend):
```python
def _validate_plot_params(hlines, vlines, title, subtitle, date_format, caller: str) -> None:
    ...
```

matplotlib apply pattern:
- ax.set_ylim([lo, hi])   # or ax.set_ylim(lo, hi)
- ax.set_xlim([date1, date2])

plotly apply pattern:
- fig.update_layout(yaxis=dict(range=[lo, hi]))
- fig.update_xaxes(range=[date1, date2])
- for secondary y: fig.update_layout(yaxis2=dict(range=[lo, hi]))
</interfaces>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add axis limit validation helper and update plots.py signatures</name>
  <files>src/pxts/plots.py, tests/test_plots.py</files>
  <behavior>
    - tsplot(ts_df, ylim=[0, 10], backend="matplotlib") returns a Figure, ax ylim is (0, 10)
    - tsplot(ts_df, ylim=(0, 10), backend="matplotlib") tuple also accepted
    - tsplot(ts_df, ylim=None, backend="matplotlib") no error, default limits preserved
    - tsplot(ts_df, xlim=[pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-05")], backend="matplotlib") returns Figure
    - tsplot(ts_df, ylim=[0, 10], backend="plotly") returns plotly Figure with yaxis.range == [0, 10]
    - tsplot(ts_df, xlim=[pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-05")], backend="plotly") returns plotly Figure
    - tsplot(ts_df, ylim="bad") raises ValueError mentioning "ylim"
    - tsplot(ts_df, ylim=[1, 2, 3]) raises ValueError mentioning "ylim" (length != 2)
    - tsplot(ts_df, xlim=[1, 2]) raises ValueError mentioning "xlim" (not date-like)
    - tsplot_dual(ts_df, left=["A"], right=["B"], ylim_lhs=[0, 5], ylim_rhs=[0, 5], backend="matplotlib") returns Figure
    - tsplot_dual(ts_df, left=["A"], right=["B"], ylim_lhs=[0, 5], backend="plotly") returns plotly Figure
    - tsplot_dual ylim_lhs controls primary y-axis, ylim_rhs controls secondary y-axis (independent)
    - All existing tests continue to pass
  </behavior>
  <action>
In src/pxts/plots.py:

1. Add a validation helper _validate_axis_limit(value, name: str, is_date: bool = False) -> None
   after _validate_plot_params. Rules:
   - If value is None: return immediately (no limit applied).
   - If value is not a list or tuple: raise ValueError(f"{name} must be list or tuple of 2 values, got {type(value).__name__}")
   - If len(value) != 2: raise ValueError(f"{name} must have exactly 2 elements, got {len(value)}")
   - If is_date=True: for each element, attempt pd.Timestamp(element). If either raises, raise
     ValueError(f"{name} values must be date-like (e.g., pd.Timestamp, str date), got {type(element).__name__}")
     Import pandas as pd at the top of the file if not already present (it is not — add it).

2. Update _validate_plot_params to accept and validate ylim, xlim (for tsplot) and
   ylim_lhs, ylim_rhs, xlim (for tsplot_dual). Since both functions call this helper,
   add ALL five as optional parameters with default None. Call _validate_axis_limit for each.
   Keep existing hlines/vlines/title/subtitle/date_format checks unchanged.

   Updated signature:
   def _validate_plot_params(hlines, vlines, title, subtitle, date_format, caller: str,
                              ylim=None, xlim=None, ylim_lhs=None, ylim_rhs=None, ylim_rhs_=None) -> None:
   NOTE: use keyword arguments for the new params to keep backward compatibility.

3. Update tsplot() signature to add ylim=None, xlim=None after date_format.
   - Call _validate_plot_params(..., ylim=ylim, xlim=xlim)
   - Pass ylim and xlim to _plot_ts_mpl and _plot_ts_plotly as kwargs.

4. Update tsplot_dual() signature to add ylim_lhs=None, ylim_rhs=None, xlim=None after date_format.
   - Call _validate_plot_params(..., ylim=None, xlim=xlim, ylim_lhs=ylim_lhs, ylim_rhs=ylim_rhs)
   - Pass ylim_lhs, ylim_rhs, xlim to _plot_ts_dual_mpl and _plot_ts_dual_plotly.

5. Update _plot_ts_mpl(... , ylim=None, xlim=None, ...) to apply limits after plotting:
   After fig.tight_layout() (but before return):
     if ylim is not None:
         ax.set_ylim(ylim[0], ylim[1])
     if xlim is not None:
         ax.set_xlim(pd.Timestamp(xlim[0]), pd.Timestamp(xlim[1]))

6. Update _plot_ts_plotly(... , ylim=None, xlim=None, ...) to apply limits:
   After existing fig.update_layout(**layout_kwargs):
     if ylim is not None:
         fig.update_layout(yaxis=dict(range=list(ylim)))
     if xlim is not None:
         fig.update_xaxes(range=[str(pd.Timestamp(xlim[0])), str(pd.Timestamp(xlim[1]))])

7. Update _plot_ts_dual_mpl(... , ylim_lhs=None, ylim_rhs=None, xlim=None, ...) to apply limits:
   After fig.tight_layout():
     if ylim_lhs is not None:
         ax1.set_ylim(ylim_lhs[0], ylim_lhs[1])
     if ylim_rhs is not None:
         ax2.set_ylim(ylim_rhs[0], ylim_rhs[1])
     if xlim is not None:
         ax1.set_xlim(pd.Timestamp(xlim[0]), pd.Timestamp(xlim[1]))

8. Update _plot_ts_dual_plotly(... , ylim_lhs=None, ylim_rhs=None, xlim=None, ...) to apply limits:
   After existing update calls:
     if ylim_lhs is not None:
         fig.update_layout(yaxis=dict(range=list(ylim_lhs)))
     if ylim_rhs is not None:
         fig.update_layout(yaxis2=dict(range=list(ylim_rhs)))
     if xlim is not None:
         fig.update_xaxes(range=[str(pd.Timestamp(xlim[0])), str(pd.Timestamp(xlim[1]))])

9. Add `import pandas as pd` at the top of plots.py (currently absent).

In tests/test_plots.py, add a new class TestAxisLimits at the end of the file:

class TestAxisLimits:
    # --- tsplot ylim/xlim matplotlib ---
    def test_tsplot_ylim_list_mpl(ts_df): ylim=[0,10] returns Figure
    def test_tsplot_ylim_tuple_mpl(ts_df): ylim=(0,10) tuple accepted
    def test_tsplot_xlim_mpl(ts_df): xlim=[pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-05")] returns Figure
    def test_tsplot_ylim_none_mpl(ts_df): ylim=None returns Figure (no error)

    # --- tsplot ylim/xlim plotly ---
    def test_tsplot_ylim_plotly(ts_df): ylim=[0,10], backend="plotly", fig.layout.yaxis.range == (0, 10)
    def test_tsplot_xlim_plotly(ts_df): xlim=[...], backend="plotly" returns go.Figure

    # --- tsplot_dual ylim_lhs/ylim_rhs/xlim ---
    def test_tsplot_dual_ylim_lhs_mpl(ts_df): ylim_lhs=[0,5] returns Figure
    def test_tsplot_dual_ylim_rhs_mpl(ts_df): ylim_rhs=[0,5] returns Figure
    def test_tsplot_dual_xlim_mpl(ts_df): xlim=[...] returns Figure
    def test_tsplot_dual_ylim_lhs_plotly(ts_df): ylim_lhs=[0,5] returns go.Figure

    # --- validation errors ---
    def test_tsplot_ylim_wrong_type_raises(ts_df): ylim="bad" raises ValueError matching "ylim"
    def test_tsplot_ylim_wrong_length_raises(ts_df): ylim=[1,2,3] raises ValueError matching "ylim"
    def test_tsplot_xlim_not_date_raises(ts_df): xlim=[1, 2] raises ValueError matching "xlim"
    def test_tsplot_dual_ylim_lhs_wrong_type_raises(ts_df): ylim_lhs=42 raises ValueError matching "ylim_lhs"
  </action>
  <verify>
    <automated>cd C:/Users/adria/Desktop/pxts && python -m pytest tests/test_plots.py -x -q 2>&1 | tail -30</automated>
  </verify>
  <done>
    All test_plots.py tests pass including the new TestAxisLimits class.
    tsplot(ylim=[0,10]) and tsplot(xlim=[date1,date2]) work on both backends.
    tsplot_dual(ylim_lhs=[0,5], ylim_rhs=[0,5], xlim=[date1,date2]) works on both backends.
    Invalid values raise ValueError with the parameter name in the message.
    ylim/xlim=None preserves default axis behaviour.
  </done>
</task>

</tasks>

<verification>
Run full test suite to confirm no regressions:

    cd C:/Users/adria/Desktop/pxts && python -m pytest tests/ -x -q
</verification>

<success_criteria>
- pytest tests/ passes with 0 failures
- tsplot(ylim=[lo, hi]) restricts y-axis on matplotlib and plotly
- tsplot(xlim=[date1, date2]) restricts x-axis on matplotlib and plotly
- tsplot_dual(ylim_lhs=[lo, hi], ylim_rhs=[lo, hi], xlim=[date1, date2]) applies limits independently per axis
- ylim/xlim=None (default) applies no limit — existing behaviour unchanged
- Non-list/tuple, wrong-length, or non-date xlim values raise ValueError with the parameter name
</success_criteria>

<output>
After completion, create .planning/quick/4-add-ylim-xlim-to-tsplot-and-ylim-lhs-yli/4-SUMMARY.md
</output>
