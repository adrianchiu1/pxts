# Roadmap: Unified `tsplot` API

## Goal

Replace `tsplot` + `tsplot_dual` with a single `tsplot` function. If `yaxis2` is
specified, the plot becomes dual-axis; otherwise it's a standard single-axis plot.

## Design Decisions (agreed)

| # | Decision |
|---|----------|
| 1 | `labels` dropped entirely (can add back later) |
| 2 | `_PLOTLY_TICKFORMATSTOPS` dropped — use default Plotly/mpl date axis handling |
| 3 | `date_format` dropped (was Plotly-only, relied on tickformatstops) |
| 4 | `yaxis2` without `cols` key → `ValueError` |
| 5 | `cols=None` + `yaxis2` → `yaxis2["cols"]` auto-excluded from left axis |
| 6 | Overlap between `cols` and `yaxis2["cols"]` → `ValueError` |
| 7 | `cols` accepts list or `{display_name: col_name}` dict |
| 8 | Old flat params (`hlines`, `vlines`, `ylim`, `xlim`, `left_label`, etc.) replaced by dicts |
| 9 | Verify scripts (`_verify_07_02*.py`, `_verify_07_03.py`) deleted |
| 10 | Legacy `plot_time_series()` deleted |
| 11 | Clean break — no backward compat shims |

## New Signature

```python
def tsplot(df, *,
           xaxis=None, yaxis=None, yaxis2=None,
           font=None, dim=None, titles=None, annot=None,
           backend=None, **kwargs):
```

## Dict Schemas

| Dict | Keys | Notes |
|------|------|-------|
| `xaxis` | `range`, `name` | `range=[date1, date2]` |
| `yaxis` | `cols`, `range`, `name` | Primary (left) y-axis. `cols` is list or `{display: actual}` |
| `yaxis2` | `cols`, `range`, `name` | **Trigger for dual-axis.** `cols` required. |
| `font` | `size`, `family` | Global font override |
| `dim` | `height`, `width` | Pixels; mpl converts via dpi (default 100) |
| `titles` | `title`, `subtitle` | mpl: suptitle+set_title. plotly: `<br><sub>` |
| `annot` | `hline`, `vline` | Each is `{label: value}` or `[value, ...]` |

## Column selection examples

```python
# All columns on single axis (default)
tsplot(df)

# Specific columns on single axis
tsplot(df, yaxis={"cols": ["A", "B", "C"]})

# Dual axis — A,B on left, C on right (auto-excluded from left)
tsplot(df, yaxis={"cols": ["A", "B"]}, yaxis2={"cols": ["C"], "name": "Pressure"})

# No yaxis cols + yaxis2 → left gets all columns EXCEPT yaxis2["cols"]
tsplot(df, yaxis2={"cols": ["C"]})  # left = A, B (assuming df has A, B, C)

# Dict cols with display names
tsplot(df,
       yaxis={"cols": {"Energy": "px_energy", "Gas": "px_gas"}},
       yaxis2={"cols": {"Steam": "px_steam"}, "range": [0, 100]})
```

---

## Phases

### Phase 1 — Cleanup (delete dead code)

**Files changed:** `plots.py`, delete verify scripts

- Delete `plot_time_series()` function
- Delete `_PLOTLY_TICKFORMATSTOPS` references (undefined constant causing NameError)
- Delete `_add_plotly_year_annotation()` (relied on tickformatstops logic)
- Delete `_extend_yaxis_for_legend()` (auto-extending is surprising behavior)
- Delete `_ADJUSTTEXT_WARNED` flag, `_manual_deconflict()`, `_add_mpl_end_labels()` (labels feature dropped)
- Delete `tests/_verify_07_02.py`, `tests/_verify_07_02_dual.py`, `tests/_verify_07_03.py`

### Phase 2 — New `tsplot` implementation

**Files changed:** `plots.py` (rewrite public API section)

1. Add `_resolve_cols()` helper:
   - Normalizes `cols` (list or dict → list of data col names + display name mapping)
   - When `yaxis2` present: validates `cols` key exists, resolves right cols, auto-excludes from left
   - Checks for overlap → `ValueError`
   - Validates all cols exist in df

2. Add `_validate_tsplot_params()` helper:
   - Validates `xaxis`, `yaxis`, `yaxis2`, `font`, `dim`, `titles`, `annot` dict shapes
   - Validates axis ranges (reuse `_validate_axis_limit` logic)
   - Validates `annot["hline"]` / `annot["vline"]` types

3. Rewrite `_plot_ts_mpl()`:
   - Accept new params: `left_cols`, `right_cols`, `col_display_names`, `xaxis`, `yaxis`, `yaxis2`, `font`, `dim`, `titles`, `annot`
   - Single-axis path: plot all cols on one ax
   - Dual-axis path (`right_cols` non-empty): `ax1.twinx()`, color axes, combined legend
   - Apply `dim` → `fig.set_size_inches(w/100, h/100)`
   - Apply `font` → override rcParams locally or set on elements
   - Apply `titles` → `fig.suptitle` + `ax.set_title` for subtitle
   - Apply `annot` → `hline`/`vline` drawing

4. Rewrite `_plot_ts_plotly()`:
   - Single-axis: `go.Figure()` with traces
   - Dual-axis: `make_subplots(specs=[[{"secondary_y": True}]])`
   - Apply `dim` → `fig.update_layout(height=, width=)`
   - Apply `font` → `fig.update_layout(font=)`
   - Apply `titles` → title + subtitle rendering
   - Apply `annot` → hline/vline
   - Range selector buttons (hardcoded 1M/3M/6M/YTD/1Y/All)
   - Rangeslider hidden

5. New `tsplot()` public function:
   - Calls `_resolve_cols()`, `_validate_tsplot_params()`
   - Dispatches to `_plot_ts_mpl()` or `_plot_ts_plotly()`

6. Delete `tsplot_dual()` public function

### Phase 3 — Update `accessor.py`

**Files changed:** `accessor.py`

- Remove `plot_dual()` method
- Update `plot()` to match new `tsplot` signature (keyword-only args)
- Remove `subtitle` and `labels` params

### Phase 4 — Update `__init__.py`

**Files changed:** `__init__.py`

- Remove `tsplot_dual` from import and `__all__`

### Phase 5 — Rewrite tests

**Files changed:** `tests/test_plots.py`, `tests/test_accessor.py`

- Delete all existing test classes in `test_plots.py`
- New test structure:

```
TestTsplotSingleMpl          — single-axis matplotlib
TestTsplotSinglePlotly       — single-axis plotly
TestTsplotDualMpl            — dual-axis matplotlib (yaxis2 present)
TestTsplotDualPlotly         — dual-axis plotly (yaxis2 present)
TestColsResolution           — cols as list/dict/None, yaxis2 exclusion, overlap error
TestValidation               — bad df, bad dict keys, bad ranges, yaxis2 without cols
TestAnnot                    — hline/vline rendering both backends
TestDim                      — dim dict sets figure size
TestFont                     — font dict applied
TestTitles                   — title + subtitle rendering
TestRangeSelector            — plotly range buttons present
```

- Update `test_accessor.py`:
  - Remove `test_plot_dual_delegates`
  - Update `test_plot_delegates` for new signature

### Phase 6 — Final verification

- Run full test suite
- Confirm no references to deleted functions remain
- Confirm `from pxts import *` works
