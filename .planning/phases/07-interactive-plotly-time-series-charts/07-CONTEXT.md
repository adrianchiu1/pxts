# Phase 7: Interactive Plotly Time Series Charts - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Upgrade the Plotly backend of `tsplot` and `tsplot_dual` to be visually polished and interactive:
- Fix excessive whitespace/margins in the Plotly layout
- Add range selector buttons (1M/3M/6M/YTD/1Y/All) and a rangeslider
- Add data point annotation capability (annotations= parameter + helper function)
- Add left_label= / right_label= axis title parameters to tsplot_dual

Matplotlib backend is untouched. No new chart types. Annotation for matplotlib is out of scope.

</domain>

<decisions>
## Implementation Decisions

### Annotation API
- Add `annotations=` parameter to both `tsplot()` and `tsplot_dual()`
- Also provide a standalone `add_annotation(fig, x, y=None, text='', col=None)` helper for post-call flexibility
- Each annotation is a dict: `{'x': date, 'text': 'label'}` — x and text are required
- `'y'` is optional: if omitted, y is auto-looked up from the nearest data point at x
- `'col'` key: optional on tsplot (single series), **required on tsplot_dual** to specify which series drives y lookup and which yaxis to reference
- **No arrow** — text only (showarrow=False). Clean floating label above the data point.

### Range navigation
- Range selector buttons **on by default** — 1M, 3M, 6M, YTD, 1Y, All
- Rangeslider **on by default**, opt-out via `rangeslider=False` parameter on tsplot/tsplot_dual
- Both apply to Plotly backend only

### Visual polish
- Primary fix: reduce excessive whitespace in Plotly layout (tighter margins)
- Light background by default; `theme='dark'` parameter enables dark background variant
- Fully responsive sizing — no fixed height or width defaults (let Plotly auto-fit)
- Claude's Discretion: exact margin values, line width defaults, font sizes in the pxts template

### Dual-axis visual identity
- Colored axis title text (not spines): left y-axis title colored to match LEFT_COLOR (blue), right y-axis title colored to match RIGHT_COLOR (orange)
- New parameters: `left_label=None` and `right_label=None` on `tsplot_dual()` — user supplies axis label text (e.g., `left_label='Energy (kWh)'`)
- When left_label/right_label are None: no axis title shown (existing behavior preserved)
- No fill-under-line feature

### Claude's Discretion
- Exact margin reduction values in the pxts Plotly template
- Rangeslider height and styling
- Range selector button styling (position, font)
- How `add_annotation` handles x values that don't exactly match an index timestamp (nearest vs exact)
- dark theme implementation (separate template or parameter override)

</decisions>

<specifics>
## Specific Ideas

- User referenced: https://willkoehrsen.github.io/python/data%20visualization/introduction-to-interactive-time-series-visualizations-with-plotly-in-python/
  - Energy and steam dual-axis chart: dual y-axes with colored labels — the target aesthetic
  - Annotation section: daily peak callouts with text positioned near data points
- The "ugly" complaint is specifically about whitespace/margins — the chart doesn't fill the available space well
- Light default, dark opt-in — user wants flexibility without it being the default

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_plot_ts_plotly` (`plots.py:435`) — existing single-axis Plotly renderer; annotations= slots in here
- `_plot_ts_dual_plotly` (`plots.py:631`) — existing dual-axis Plotly renderer; left_label/right_label slot in here
- `_PLOTLY_TICKFORMATSTOPS` (`plots.py:175`) — zoom-responsive date format stops; preserved as-is
- `_add_plotly_year_annotation` (`plots.py:372`) — existing annotation helper; annotation feature extends this pattern
- `pxts` Plotly template (`theme.py`) — where margin/layout defaults live; margins get tightened here
- `LEFT_COLOR`, `RIGHT_COLOR` constants (`plots.py:29-30`) — axis title colors for dual chart

### Established Patterns
- `annotations=` follows the same pattern as `hlines=` and `vlines=`: list or dict, validated in `_validate_plot_params`, processed in the backend-specific helper
- `rangeslider=True` follows the opt-out pattern of other boolean parameters
- `theme='dark'` is a new parameter shape — no existing precedent; Claude decides implementation

### Integration Points
- `tsplot()` public signature gets: `annotations=None`, `rangeslider=True`, `theme='light'`
- `tsplot_dual()` public signature gets: `annotations=None`, `rangeslider=True`, `theme='light'`, `left_label=None`, `right_label=None`
- `add_annotation(fig, x, text, y=None, col=None)` — new standalone public function in `plots.py`, exported via `__init__.py`
- `_validate_plot_params` gets updated to validate annotations list shape

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-interactive-plotly-time-series-charts*
*Context gathered: 2026-03-17*
