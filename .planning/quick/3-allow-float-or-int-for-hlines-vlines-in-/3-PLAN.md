---
phase: quick-3
plan: 3
type: execute
wave: 1
depends_on: []
files_modified:
  - src/pxts/plots.py
  - tests/test_plots.py
autonomous: true
requirements: [QUICK-3]

must_haves:
  truths:
    - "tsplot(hlines=1.5) draws a single horizontal line without error"
    - "tsplot(vlines=some_timestamp) is unaffected (timestamps are not int/float)"
    - "tsplot(hlines='bad') still raises ValueError"
    - "tsplot(hlines=[1.0, 2.0]) and tsplot(hlines={'label': 1.0}) still work"
  artifacts:
    - path: "src/pxts/plots.py"
      provides: "Normalized hlines/vlines scalar handling"
      contains: "_normalize_lines"
    - path: "tests/test_plots.py"
      provides: "Tests for scalar hlines/vlines"
  key_links:
    - from: "_validate_plot_params"
      to: "_draw_hlines_mpl / _draw_hlines_plotly"
      via: "normalization before draw calls"
      pattern: "isinstance.*int.*float"
---

<objective>
Allow users to pass a single float or int directly as hlines/vlines (e.g., hlines=1.5)
instead of requiring a list wrapper (e.g., hlines=[1.5]).

Purpose: Convenience — a single reference line is the common case and wrapping in a list
is friction with no benefit.
Output: plots.py normalizes scalar int/float to [value] before validation and drawing.
Tests updated to cover the new scalar path and remove the now-incorrect raises assertion.
</objective>

<execution_context>
@C:/Users/adria/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/adria/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Normalize scalar hlines/vlines in plots.py and update tests</name>
  <files>src/pxts/plots.py, tests/test_plots.py</files>
  <behavior>
    - tsplot(ts_df, hlines=1.5, backend="matplotlib") succeeds and draws one hline
    - tsplot(ts_df, hlines=0, backend="matplotlib") succeeds (int zero treated as scalar)
    - tsplot(ts_df, hlines="bad", ...) still raises ValueError mentioning "hlines"
    - tsplot(ts_df, hlines=[1.0, 2.0], ...) unchanged — list still works
    - tsplot(ts_df, hlines={"low": 1.0}, ...) unchanged — dict still works
    - tsplot_dual scalar hlines/vlines behave the same as tsplot
  </behavior>
  <action>
In src/pxts/plots.py:

1. Add a helper function _normalize_lines(value, name) after the imports / before
   _validate_plot_params. It should:
   - If value is int or float → return [value]
   - Otherwise → return value unchanged
   Do NOT accept bool as numeric (bool is subclass of int — exclude explicitly with
   `isinstance(value, bool)` guard so True/False still fail validation downstream).

2. In tsplot() and tsplot_dual(), call _normalize_lines on both hlines and vlines
   BEFORE calling _validate_plot_params. Assign the result back to hlines/vlines
   so the draw functions receive the normalised value.

3. In _validate_plot_params, no change needed to the isinstance check — after
   normalization a scalar will already be a list. The docstring should be updated to
   reflect that scalars are normalized upstream (not validated here).

In tests/test_plots.py:

4. Remove (or rewrite) the existing test test_tsplot_hlines_wrong_type_raises that
   asserts tsplot(ts_df, hlines=42.0) raises ValueError. Replace it with:
   - test_hlines_scalar_float: tsplot(ts_df, hlines=42.0, ...) succeeds, returns a figure
   - test_hlines_scalar_int: tsplot(ts_df, hlines=0, ...) succeeds, returns a figure
   - test_hlines_bool_raises: tsplot(ts_df, hlines=True, ...) raises ValueError (bool excluded)
   Keep test_tsplot_dual_vlines_wrong_type_raises unchanged (vlines="bad" still errors).
  </action>
  <verify>
    <automated>cd C:/Users/adria/Desktop/pxts && python -m pytest tests/test_plots.py -x -q 2>&1 | tail -20</automated>
  </verify>
  <done>
    All test_plots.py tests pass. tsplot(hlines=1.5) and tsplot(hlines=0) both return
    figures without error. tsplot(hlines=True) raises ValueError. Existing list/dict/None
    tests still green.
  </done>
</task>

</tasks>

<verification>
Run full test suite to confirm no regressions:

    cd C:/Users/adria/Desktop/pxts && python -m pytest tests/ -x -q
</verification>

<success_criteria>
- pytest tests/ passes with 0 failures
- tsplot(hlines=1.5) accepted (scalar float normalized to [1.5])
- tsplot(hlines=0) accepted (scalar int zero normalized to [0])
- tsplot(hlines=True) rejected (bool excluded from scalar normalization)
- No existing list/dict/None behavior changed
</success_criteria>

<output>
After completion, create .planning/quick/3-allow-float-or-int-for-hlines-vlines-in-/3-SUMMARY.md
</output>
