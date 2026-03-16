# Phase 6: Plotly Rendering Fixes — Date Axis Autoformatting and Legend - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix two Plotly rendering defects in `tsplot` and `tsplot_dual`: (1) the date x-axis uses a single static format string and doesn't adapt to zoom level or data span; (2) the legend is not visible. Both fixes apply to both functions. No new user-facing parameters are added.

</domain>

<decisions>
## Implementation Decisions

### Date axis — approach
- Replace `_detect_plotly_tickformat()` entirely — remove it, do not keep as fallback
- Use Plotly's `tickformatstops` array on the x-axis instead of a single `tickformat` string
- This makes the format zoom-responsive (changes as user zooms in/out), matching the interactive behaviour of `ConciseDateFormatter`

### Date axis — zoom levels (4 tiers)
Define tickformatstops with 4 levels (from most zoomed-out to most zoomed-in):
1. Decade+ span → `'%Y'`
2. Year view → `'%b %Y'`
3. Month view → `'%b %d'`
4. Day/sub-day view → `'%d'`
This matches ConciseDateFormatter's natural granularities for financial data.

### Date axis — hierarchy
- Aim for ConciseDateFormatter-style hierarchy: year appears only at year transitions, month/day labels fill in between
- The tickformatstops `dtickrange` thresholds should be set to achieve this contextual labelling

### Date axis — year offset annotation
- Show the current year as a small annotation at bottom-right of the chart, equivalent to matplotlib's ConciseDateFormatter offset label
- This appears when viewing sub-year data so the year context is always visible

### Date axis — manual override preserved
- If `date_format` is explicitly passed by the user, use it as a static `tickformat` string (existing behaviour)
- `tickformatstops` is only used when `date_format is None`

### Date axis — scope
- Fix applies to both `_plot_ts_plotly` and `_plot_ts_dual_plotly` (both call the same code path today)

### Legend — fix location
- Add `showlegend=True` to the pxts Plotly template in `theme.py` (not just in the plot functions), so it applies globally to all future plotly output from pxts

### Legend — sort order
- Sort legend entries by last value descending, consistent with the matplotlib backend
- The current plotly code already sorts traces by last value before adding them, so legend order follows naturally

### Legend — position
- Top-right inside the plot (Plotly default, `xanchor='right', x=1`)
- Semi-transparent background already set in the pxts template

### Legend — overlap avoidance
- If any series' last value falls in the top-right quadrant of the chart (top 25% of y-range AND near the right edge of the x-axis), extend the y-axis upward to create headroom
- This is a best-effort approximation since Plotly does not expose legend bounding-box coordinates
- Only applies when `ylim` is not explicitly set by the user (user-set limits are never overridden)

### Legend — dual-axis distinction
- Color only: blue = left axis, orange = right axis (already enforced by LEFT_COLOR/RIGHT_COLOR)
- No '(L)'/'(R)' suffix added to legend labels

### Testing
- Update existing Plotly tests in `tests/test_plots.py`
- Assert `tickformatstops` is set on the x-axis (not a single `tickformat`)
- Assert `showlegend=True` in the figure layout
- Existing test structure (mocked plotly backend) can be extended

### Claude's Discretion
- Exact `dtickrange` threshold values for each tickformatstops tier (millisecond values in Plotly's time system)
- Exact definition of "top-right quadrant" for the overlap check (e.g. top 25% of y-range and last 10% of x-range)
- Implementation of the year offset annotation (static annotation vs. dynamic based on visible range)

</decisions>

<specifics>
## Specific Ideas

- "Feels like Bloomberg/TradingView" — interactive zoom should update the date format naturally
- The year annotation at bottom-right is the ConciseDateFormatter offset label equivalent — small, unobtrusive

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_detect_plotly_tickformat(df)` in `plots.py:160` — to be removed and replaced by tickformatstops logic
- `_sorted_cols_by_last_value(df, cols)` in `plots.py:186` — already used for trace ordering; used for legend sort
- `pxts` Plotly template in `theme.py:49` (`_apply_plotly_theme`) — add `showlegend=True` here
- `LEFT_COLOR`, `RIGHT_COLOR` constants — legend color distinction for dual-axis is already handled

### Established Patterns
- `date_format` parameter already plumbed through both `_plot_ts_plotly` and `_plot_ts_dual_plotly` — override path is clear
- `tickformatstops` replaces the single `tickformat` key in `xaxis=dict(type="date", tickformat=...)` calls

### Integration Points
- `_plot_ts_plotly` (`plots.py:377`): replace `tickformat=tickformat` with `tickformatstops=[...]` when `date_format is None`
- `_plot_ts_dual_plotly` (`plots.py:564`): same change in `fig.update_xaxes(type="date", tickformat=tickformat)`
- `theme.py:62` (`go.Layout` inside `_apply_plotly_theme`): add `showlegend=True`

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-plotly-rendering-fixes-date-axis-autoformatting-and-legend*
*Context gathered: 2026-03-16*
