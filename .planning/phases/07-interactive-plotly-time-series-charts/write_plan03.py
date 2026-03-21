#!/usr/bin/env python3
"""Write Phase 7 Plan 03."""
import os

BASE = r"C:/Users/adria/Desktop/pxts/.planning/phases/07-interactive-plotly-time-series-charts"

plan03 = """\
---
phase: 07-interactive-plotly-time-series-charts
plan: 03
type: execute
wave: 2
depends_on:
  - 07-02
files_modified:
  - src/pxts/plots.py
  - src/pxts/__init__.py
autonomous: true
requirements:
  - PLT7-05
  - PLT7-06

must_haves:
  truths:
    - "tsplot(annotations=[{'x': date, 'text': 'label'}]) shows text annotation near data point on Plotly chart"
    - "tsplot_dual with annotations and col key routes annotation to correct y-axis"
    - "Annotations with no y key auto-lookup the nearest y value from the data"
    - "add_annotation(fig, x, text) adds an annotation to an existing Plotly figure"
    - "add_annotation(fig, x, text, col='A') works when col is specified"
    - "Invalid annotations input raises ValueError with clear message"
    - "from pxts import add_annotation works after __init__.py update"
    - "Matplotlib backend is unaffected"
  artifacts:
    - path: "src/pxts/plots.py"
      provides: "Annotation processing helpers and add_annotation public function"
      contains: "add_annotation"
    - path: "src/pxts/__init__.py"
      provides: "add_annotation exported in __all__"
      contains: "add_annotation"
  key_links:
    - from: "tsplot() / tsplot_dual()"
      to: "_apply_plotly_annotations(fig, annotations, df, cols)"
      via: "annotations list forwarded from public API to private helper"
      pattern: "_apply_plotly_annotations"
    - from: "add_annotation(fig, x, text)"
      to: "fig.add_annotation(x=x_str, y=y_val, text=text, showarrow=False)"
      via: "x converted to str, y looked up from nearest row in df if not supplied"
      pattern: "showarrow=False"
    - from: "_validate_plot_params"
      to: "annotations type check"
      via: "annotations validated as list or None; each item must be dict with x and text"
      pattern: "annotations"
---

<objective>
Implement the annotation feature: add annotations= parameter processing to both Plotly renderers,
add the add_annotation() standalone public helper, validate annotation shapes in _validate_plot_params,
and export add_annotation via __init__.py.

Purpose: Users can annotate significant events (earnings releases, rate decisions, etc.) directly
on the chart without post-processing. The standalone helper supports workflow flexibility.

Output: Annotation processing in plots.py, add_annotation exported from __init__.py.
</objective>

<execution_context>
@C:/Users/adria/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/adria/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/07-interactive-plotly-time-series-charts/07-CONTEXT.md
@.planning/phases/07-interactive-plotly-time-series-charts/07-02-SUMMARY.md

Annotation spec from CONTEXT.md:
  - Each annotation dict: {"x": date, "text": "label"} — x and text are required
  - "y" is optional: if omitted, auto-lookup from nearest data point at x
  - "col" key: optional for tsplot (single series), required for tsplot_dual
  - No arrow (showarrow=False). Clean floating label above the data point.

After Plan 02, tsplot and tsplot_dual already accept annotations= in their signatures,
and _plot_ts_plotly/_plot_ts_dual_plotly already accept annotations= as a no-op.
This plan replaces the no-op with actual processing.

_validate_plot_params current signature (plots.py line 119):
    def _validate_plot_params(hlines, vlines, title, subtitle, date_format, caller,
                              ylim=None, xlim=None, ylim_lhs=None, ylim_rhs=None):

tsplot() caller validation line (plots.py ~line 746):
    _validate_plot_params(hlines, vlines, title, subtitle, date_format, caller="tsplot",
                          ylim=ylim, xlim=xlim)

tsplot_dual() caller validation line (plots.py ~line 796):
    _validate_plot_params(hlines, vlines, title, subtitle, date_format, caller="tsplot_dual",
                          ylim=None, xlim=xlim, ylim_lhs=ylim_lhs, ylim_rhs=ylim_rhs)

__init__.py current imports (line 49):
    from pxts.plots import tsplot, tsplot_dual
__all__ currently includes: tsplot, tsplot_dual (but not add_annotation)

_add_plotly_year_annotation (plots.py line 372) — pattern to follow:
    fig.add_annotation(
        text=str(year), xref="paper", yref="paper",
        x=1.0, y=-0.08, showarrow=False,
        font=dict(size=DEFAULT_FONT_SIZE - 2),
        xanchor="right", yanchor="top",
    )
"""

plan03 += """
</context>

<tasks>

<task type="auto">
  <name>Task 1: Annotation validation, processing helper, and add_annotation() function</name>
  <files>src/pxts/plots.py</files>
  <action>
Step 1 - Update _validate_plot_params to validate annotations.

Add annotations=None parameter to the function signature, after ylim_rhs=None:
    def _validate_plot_params(hlines, vlines, title, subtitle, date_format, caller,
                              ylim=None, xlim=None, ylim_lhs=None, ylim_rhs=None,
                              annotations=None):

Add validation at the end of the function body (before the _validate_axis_limit calls):
    if annotations is not None:
        if not isinstance(annotations, list):
            raise ValueError(
                f"{caller}: annotations must be list or None, got {type(annotations).__name__}"
            )
        for i, ann in enumerate(annotations):
            if not isinstance(ann, dict):
                raise ValueError(
                    f"{caller}: annotations[{i}] must be a dict, got {type(ann).__name__}"
                )
            if "x" not in ann:
                raise ValueError(
                    f"{caller}: annotations[{i}] missing required key 'x'"
                )
            if "text" not in ann:
                raise ValueError(
                    f"{caller}: annotations[{i}] missing required key 'text'"
                )

Update both callers to pass annotations:
  In tsplot():
    _validate_plot_params(hlines, vlines, title, subtitle, date_format, caller="tsplot",
                          ylim=ylim, xlim=xlim, annotations=annotations)
  In tsplot_dual():
    _validate_plot_params(hlines, vlines, title, subtitle, date_format, caller="tsplot_dual",
                          ylim=None, xlim=xlim, ylim_lhs=ylim_lhs, ylim_rhs=ylim_rhs,
                          annotations=annotations)

Step 2 - Add _apply_plotly_annotations() private helper near the Plotly helpers section
(after _draw_vlines_plotly, before the public API section). This helper adds Plotly
annotations from the annotations list to an existing figure:

    def _apply_plotly_annotations(fig, annotations, df, cols, secondary_y_cols=None) -> None:
        \"\"\"Add data-point annotations to a Plotly figure.

        Each annotation dict must have "x" and "text" keys. "y" is optional — if absent,
        y is auto-looked up from the nearest row to x in df[col]. "col" is optional for
        single-axis charts but required for dual-axis charts (secondary_y_cols provided).

        Args:
            fig: Plotly figure to annotate.
            annotations: list of dicts with keys "x", "text", optionally "y" and "col".
            df: DataFrame used for y auto-lookup (must have DatetimeIndex).
            cols: list of column names available for y lookup.
            secondary_y_cols: if not None, list of column names on secondary y-axis;
                used to set yref="y2" for those annotations.
        \"\"\"
        if not annotations:
            return
        for ann in annotations:
            x_val = ann["x"]
            text = ann["text"]
            x_ts = pd.Timestamp(x_val)

            # Determine which column to use for y-lookup
            col = ann.get("col", None)
            if col is None:
                col = cols[0]  # default to first column for single-axis charts

            # y auto-lookup: find nearest row index to x_ts
            if "y" in ann:
                y_val = ann["y"]
            else:
                # Find index of nearest timestamp
                if col in df.columns:
                    idx = (df.index - x_ts).abs().argmin()
                    y_val = df[col].iloc[idx]
                else:
                    y_val = 0

            # Determine yref based on whether col is on secondary axis
            if secondary_y_cols and col in secondary_y_cols:
                yref = "y2"
            else:
                yref = "y"

            fig.add_annotation(
                x=str(x_ts),
                xref="x",
                y=y_val,
                yref=yref,
                text=str(text),
                showarrow=False,
                font=dict(size=DEFAULT_FONT_SIZE - 1),
                yanchor="bottom",
                bgcolor="rgba(255,255,255,0.7)",
            )

Step 3 - Wire _apply_plotly_annotations into _plot_ts_plotly. After the hlines/vlines
processing block (the "if hlines:" / "if vlines:" calls), add:

    if annotations:
        _apply_plotly_annotations(fig, annotations, df, cols)

Step 4 - Wire _apply_plotly_annotations into _plot_ts_dual_plotly. After the hlines/vlines
processing block, add:

    if annotations:
        _apply_plotly_annotations(fig, annotations, df, left + right,
                                   secondary_y_cols=right)

Step 5 - Add add_annotation() public function at the end of the Plotly helpers section
(after _apply_plotly_annotations, before the matplotlib dual-axis helpers section):

    def add_annotation(fig, x, text: str, y=None, col: str = None) -> None:
        \"\"\"Add a single annotation to an existing Plotly figure.

        Standalone helper for post-call annotation. Useful when you want to annotate
        a figure returned by tsplot() or tsplot_dual() without rebuilding it.

        Args:
            fig: plotly.graph_objects.Figure to annotate.
            x: x-position as a date-like value (str, pd.Timestamp, datetime).
            text: annotation label text.
            y: y-position. If None, the annotation is placed at y=0 with yref="paper"
               (you should provide y for accurate positioning).
            col: column name hint — not used for positioning here (caller is responsible
               for passing the correct y value), but included for API symmetry with
               the annotations= dict format.

        Returns:
            None. Modifies fig in place.
        \"\"\"
        x_str = str(pd.Timestamp(x))
        if y is None:
            yref = "paper"
            y_val = 0.5
        else:
            yref = "y"
            y_val = y

        fig.add_annotation(
            x=x_str,
            xref="x",
            y=y_val,
            yref=yref,
            text=str(text),
            showarrow=False,
            font=dict(size=DEFAULT_FONT_SIZE - 1),
            yanchor="bottom",
            bgcolor="rgba(255,255,255,0.7)",
        )
  </action>
  <verify>
    <automated>cd /c/Users/adria/Desktop/pxts && python -c "exec(open('tests/_verify_07_03.py').read())"</automated>
  </verify>
  <done>
    - _apply_plotly_annotations helper exists in plots.py
    - add_annotation() function exists and can be imported from pxts.plots
    - tsplot(annotations=[{"x": "2024-01-03", "text": "Event"}], backend="plotly") adds annotation to figure
    - tsplot_dual(annotations=[{"x": date, "text": "E", "col": "A"}], backend="plotly") adds annotation on correct axis
    - Annotation has showarrow=False, text visible, positioned near data point
    - _validate_plot_params raises ValueError on invalid annotations input
    - All existing tests pass: pytest tests/ -x -q
  </done>
</task>

<task type="auto">
  <name>Task 2: Export add_annotation via __init__.py</name>
  <files>src/pxts/__init__.py</files>
  <action>
1. Update the import line for plots (line 49):
    from pxts.plots import tsplot, tsplot_dual, add_annotation

2. Add "add_annotation" to __all__ (after "tsplot_dual"):
    "add_annotation",

3. Update the module docstring to mention add_annotation in the Public API block:
    add_annotation(fig, x, text, y=None, col=None) -- add annotation to an existing Plotly figure
  </action>
  <verify>
    <automated>cd /c/Users/adria/Desktop/pxts && python -c "from pxts import add_annotation; import pxts; assert 'add_annotation' in pxts.__all__; print('add_annotation exported OK')"</automated>
  </verify>
  <done>
    - "from pxts import add_annotation" works without ImportError
    - add_annotation in pxts.__all__
    - Module docstring mentions add_annotation
  </done>
</task>

</tasks>

<verification>
Create tests/_verify_07_03.py before running it. It should assert:
  - tsplot(annotations=[{"x": "2024-01-03", "text": "Peak"}], backend="plotly") returns figure
    with at least one non-year annotation containing "Peak"
  - tsplot_dual(annotations=[{"x": "2024-01-03", "text": "E", "col": "A"}], backend="plotly")
    returns figure with annotation containing "E"
  - add_annotation(fig, "2024-01-03", "Event") adds annotation to existing figure (annotations count increases)
  - _validate_plot_params raises ValueError for annotations="bad" (not a list)
  - _validate_plot_params raises ValueError for annotations=[{"x": "2024"}] (missing "text")
  - print("Task 03 OK")

Full regression: pytest tests/ -x -q
</verification>

<success_criteria>
- annotations= parameter is processed in both Plotly renderers (no longer a no-op)
- add_annotation() function available as pxts.add_annotation
- Invalid annotation inputs raise clear ValueError messages
- Annotations appear as showarrow=False floating text labels near data points
- All 56 existing tests pass
</success_criteria>

<output>
After completion, create .planning/phases/07-interactive-plotly-time-series-charts/07-03-SUMMARY.md
</output>
"""

with open(os.path.join(BASE, "07-03-PLAN.md"), "w") as f:
    f.write(plan03)

print("Plan 03 written:", len(plan03), "chars")
