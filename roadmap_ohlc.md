# Roadmap: Intraday OHLC bars (TradingView-style) from Bloomberg

Status: **planning — no code yet.** Open questions are at the bottom; the
design below is a proposal to be revised once they are answered.

---

## 1. Goal

Add to pxts:

1. A Bloomberg **intraday bar** reader (`IntradayBarRequest`) alongside the
   existing daily `read_bdh`, supporting 1min / 5min / 30min / 1h / 2h / 4h / 1d.
2. A **candlestick / OHLC chart** that looks like TradingView (candles, volume
   pane, crosshair, last-price marker, compressed time axis) but sits inside the
   pxts chrome (accent line, title/subtitle, Outfit font, no spines, source line)
   and can overlay ordinary pxts line series (moving averages, a second
   instrument, etc.).

---

## 2. What already exists and gets reused

| Existing piece | Reused for |
|---|---|
| `io.read_bdh` (pdblp `BCon`, timeout param, dict-rename convention) | Same connection pattern and ticker/dict API shape for the new intraday reader; daily (1d) bars via BDH multi-field |
| `core.validate_ts`, `set_tz`, `infer_freq` | Index validation, UTC → display-tz conversion, bar-interval detection on plot |
| `plots.LayoutMetrics` + `_draw_accent_line_plotly`, `_draw_title_plotly`, `_draw_source_plotly` | Chrome for the candle chart, extended with a volume row |
| `plots._infer_hover_date_format`, `_estimate_xaxis_pad_px` | Intraday-aware hover and padding (already handle minute/hour data) |
| `theme.py` constants incl. unused `DARK_*` colours | Candle colours, optional dark mode |
| `tests/test_bdh.py` mocking pattern (`patch.dict(sys.modules, {"pdblp": ...})`) | Offline tests for the intraday reader |
| `write_csv` / `read_csv` | Optional on-disk cache of intraday pulls |

---

## 3. Bloomberg intraday facts that shape the design

These are from the Bloomberg API documentation and pdblp/xbbg source; items
marked *(verify)* should be confirmed on a live terminal because I cannot
reach one from here.

- **Request type**: `//blp/refdata` `IntradayBarRequest`. pdblp exposes it as
  `BCon.bdib(ticker, start_datetime, end_datetime, event_type="TRADE",
  interval=1, elms=None)` returning a DataFrame indexed by bar `time` with
  columns `open, high, low, close, volume, numEvents, value`.
- **One security per request.** Multiple tickers = loop of requests on one
  open connection.
- **Interval** is an integer number of minutes, 1 to 1440. So 1/5/30/60/120/240
  are native; 1440 is a UTC-midnight "day", which is *not* an exchange session.
- **Times are UTC** in both the request window and the response. Bars are
  labelled by their *open* time (same convention as TradingView).
- **History depth is limited**: roughly the trailing 140 calendar days of
  intraday bars per security *(verify; some sources say 240 days for bars)*.
  Daily BDH has no such limit. This is the strongest argument for sourcing
  1d bars from BDH, and for an optional local cache that accumulates history.
- **Event types**: `TRADE` (default), `BID`, `ASK`, `BID_BEST`, `ASK_BEST`,
  `BEST_BID`, `BEST_ASK`, `MID_PRICE`, `AT_TRADE`. FX and many rates tickers
  have no `TRADE` events, so the reader needs an `event` parameter and a
  sensible default per asset class.
- **Other request flags** worth exposing via a passthrough: `gapFillInitialBar`,
  `adjustmentSplit` / `adjustmentNormal` / `adjustmentAbnormal`
  (equity corporate actions), `adjustmentFollowDPDF`.
- **Bar alignment of native N-minute bars** appears to follow the request's
  `startDateTime` rather than a fixed clock boundary *(verify)*. Pulling
  1-minute bars and resampling locally gives deterministic, session-anchored
  2h/4h bars at the cost of a bigger download (24h futures ≈ 1,400 bars/day,
  ≈ 200k rows for the full 140-day window, which pandas handles easily).
- **pdblp is in maintenance mode.** Its author recommends the successor
  package `blp` (`BlpQuery.bdib`). `xbbg` is another maintained option with
  built-in exchange-session handling and a parquet cache. All three sit on
  the same `blpapi` SDK. Staying on pdblp is the least-change path and
  matches `read_bdh`; switching is a separate decision (question 2).

---

## 4. Brainstorm: what is possible

Grouped from "core" to "nice to have". Not all of this is proposed for v1.

### 4.1 Data layer
- `read_bdib(tickers, start, end, interval, event, tz, ...)` — intraday bars.
- `1d` routed to BDH (`PX_OPEN, PX_HIGH, PX_LOW, PX_LAST, PX_VOLUME`) for
  session-correct daily bars with unlimited history. Also makes weekly /
  monthly bars trivial later via resampling.
- Two fetch strategies for N-minute bars: **native** (ask Bloomberg for
  interval=N) or **1-min + local resample** (deterministic anchoring, one
  download serves every interval). Could be a parameter, default native.
- Automatic UTC → display timezone conversion (`tz=`), with the exchange
  session optionally supplied for anchoring (`session={"open": "09:30",
  "close": "16:00", "tz": "America/New_York"}`).
- A shared Bloomberg connection helper (`_bbg_connection(timeout)` context
  manager) used by both `read_bdh` and `read_bdib`, plus an optional `con=`
  argument so a notebook can keep one connection open across many pulls.
- History-window guard: warn (not fail) when `start` is older than the
  Bloomberg intraday retention window, and clamp.
- Chunked requests (per week) with progress, so long 1-minute pulls do not
  hit the timeout the user already had to raise on `read_bdh`.
- Optional **local cache** (`cache="path/to/dir"`): append-only CSV or parquet
  per ticker/interval, so history accumulates beyond the 140-day window.
  Parquet was explicitly deferred in v0.1 (pyarrow dependency); CSV via
  `write_csv` is already available.
- `ohlc` as a first-class shape: a `validate_ohlc(df)` helper that accepts
  `open/high/low/close[/volume]` columns case-insensitively and checks
  `high >= max(open, close)` and `low <= min(open, close)`.
- `resample_ohlc(df, freq, *, session=None, origin=...)` in `core.py` with
  the standard aggregation (`open=first, high=max, low=min, close=last,
  volume=sum`) and session-anchored bins, exposed on the `.ts` accessor.
- Live/streaming last bar via `//blp/mktdata` subscriptions — possible with
  Plotly `FigureWidget`, but a big step up in complexity. Out of scope unless
  wanted.

### 4.2 Chart — Plotly backend (primary, Jupyter)
- `go.Candlestick` (candles) or `go.Ohlc` (TradingView "Bars"), selectable
  via `style="candle" | "bar" | "hollow"`.
- TradingView colours by default (up `#26a69a`, down `#ef5350`) with the pxts
  chrome around it; optional dark mode using the existing `DARK_*` constants.
- **Volume pane** below the candles (`make_subplots`, shared x, row heights
  ~75/25), bars coloured by candle direction, hidden automatically when there
  is no volume column (FX, rates).
- **Compressed time axis** so overnight and weekend gaps do not appear:
  - Option A: Plotly date axis + `rangebreaks` (weekend bounds, hour pattern
    for the session, holiday list). Clean for regular sessions; awkward for
    24h futures with a daily one-hour break and DST shifts.
  - Option B: plot against an integer bar index and relabel ticks with
    dates/times (what TradingView and mplfinance actually do). Uniform candle
    width, works for any session, same approach on both backends; costs the
    native date-axis zoom semantics and needs custom tick/hover text.
- Crosshair: x and y spikes with axis labels (`spikemode="across"`), unified
  hover showing O/H/L/C/Vol and bar-to-bar change.
- **Last-price line**: dotted horizontal line at last close with a coloured
  price tag on the y-axis (an `hline` plus annotation).
- Price scale on the **right** (TradingView) vs left (pxts) — a parameter.
- Interaction: `dragmode="pan"` and `scrollZoom` config to feel like
  TradingView; range-selector buttons (1D / 5D / 1M / 3M / All) sized for
  intraday spans.
- Line overlays: reuse the `yaxis={"cols": [...]}` semantics so any extra
  columns on the same DataFrame (SMA, EMA, VWAP, another instrument) draw as
  pxts lines on the candle panel, with the usual legend / `labels=True`
  end-of-line labels. This is the literal "merge with pxts line charts".
- A second y-axis (`yaxis2`) for a comparison series in different units.
- Annotations: reuse `annotations={"hline": ..., "vline": ...}` unchanged.
- Built-in indicators (SMA/EMA/VWAP/Bollinger) as a helper that *adds
  columns* rather than chart magic — keeps the chart function pure.
- Static OHLC readout (O H L C Δ%) in the top-left for the last bar; a
  crosshair-following readout needs JavaScript callbacks and is not possible
  in plain Plotly output.
- Session shading (pre-market / after-hours) as translucent vrects.
- Multi-ticker "compare" overlay as percent-change lines (TradingView
  Compare). Later.

### 4.3 Chart — matplotlib backend (scripts / publication)
- Hand-drawn candles (`Rectangle` bodies + `vlines` wicks) against an integer
  index with date tick labels, plus a volume axis below via `gridspec`.
  No new dependency (mplfinance is heavy and styles everything itself).
- Could be deferred to a second phase if Jupyter/Plotly is the real target.

### 4.4 API surface options
- **New function** `ohlcplot(df, ...)` (and `df.ts.ohlcplot()`), sharing
  the same dict parameters as `tsplot` (`xaxis`, `yaxis`, `yaxis2`, `title`,
  `dim`, `font`, `annotations`, `source`, `labels`, `backend`).
- **Or** extend `tsplot` with `kind="candle"` / an `ohlc={...}` dict.
  Cleaner for discoverability, but `tsplot` is already 1,200 lines and the
  layout logic diverges (two rows, integer x-axis).
- Multi-ticker return shape for `read_bdib`: single wide OHLCV frame for one
  ticker (fits pxts' single-level columns convention); for several tickers
  either a `dict[str, DataFrame]`, a MultiIndex column frame
  `(ticker, field)`, or a long frame. pxts has avoided MultiIndex so far.
- Interval spelling: pandas aliases (`"5min"`, `"1h"`, `"1D"`), TradingView
  style (`"5m"`, `"1H"`, `"D"`), or both (normalised internally).

---

## 5. Proposed design (subject to the questions)

### 5.1 Public API

```python
# I/O
read_bdib(tickers, start, end=None, *, interval="5min", event="TRADE",
          tz="UTC", session=None, source="native" | "1min",
          timeout=30, con=None, cache=None, **bbg_options) -> DataFrame

# Core
resample_ohlc(df, freq, *, session=None) -> DataFrame
validate_ohlc(df) -> DataFrame             # (maybe private)

# Plot
ohlcplot(df, *, ohlc=None, volume=True, style="candle", xaxis=None,
         yaxis=None, yaxis2=None, title=None, annotations=None, source=None,
         dim=None, font=None, labels=False, last_price=True,
         price_axis="right", backend=None, **kwargs) -> Figure

# Accessor
df.ts.ohlcplot(...), df.ts.resample_ohlc(...)
```

`ohlc` defaults to auto-detecting `open/high/low/close[/volume]` columns;
pass `ohlc={"open": "PX_OPEN", ...}` to map other names. `yaxis["cols"]`
keeps its `tsplot` meaning (extra line series on the price panel).

### 5.2 Interval mapping

| pxts interval | Bloomberg request | Notes |
|---|---|---|
| `1min` | `IntradayBarRequest`, interval=1 | |
| `5min` | interval=5 (or 1min + resample) | |
| `30min` | interval=30 | |
| `1h` | interval=60 | |
| `2h` | interval=120 | anchoring to session open: verify native alignment, else resample |
| `4h` | interval=240 | same |
| `1d` | `HistoricalDataRequest` (BDH) fields `PX_OPEN/HIGH/LOW/LAST/VOLUME` | exchange-session days, unlimited history |

Everything maps through one `_parse_interval(str) -> (minutes | "D")` helper
that also accepts pandas aliases.

### 5.3 Data flow

```
read_bdib("ES1 Index", "2026-09-01", interval="5min", tz="Europe/London")
  → _parse_interval → minutes=5
  → _bbg_connection(timeout) → con.bdib(ticker, start_utc, end_utc, event, 5, elms)
     (looped per ticker, optionally chunked per week)
  → rename columns to open/high/low/close/volume, drop numEvents/value
  → index: UTC → tz_convert(tz)
  → validate_ts → return

ohlcplot(df, title={...})
  → validate_ts + validate_ohlc → detect columns
  → infer bar interval (min index diff) → hover format, tick labels
  → build integer x positions (or rangebreaks) → candles + volume + overlays
  → LayoutMetrics (with volume row) → chrome → Figure
```

### 5.4 Module layout

| File | Change |
|---|---|
| `src/pxts/io.py` | `read_bdib`, `_bbg_connection`, `_parse_interval`; `read_bdh` refactored to use the shared connection helper (no behaviour change) |
| `src/pxts/core.py` | `resample_ohlc`, `validate_ohlc` |
| `src/pxts/plots_ohlc.py` (new) | `ohlcplot` + `_plot_ohlc_plotly` / `_plot_ohlc_mpl`; imports chrome helpers from `plots.py` |
| `src/pxts/plots.py` | Small refactor: let `LayoutMetrics` accept an extra bottom panel height; no API change to `tsplot` |
| `src/pxts/theme.py` | `CANDLE_UP_COLOR`, `CANDLE_DOWN_COLOR`, volume alpha |
| `src/pxts/accessor.py`, `__init__.py` | New methods / exports |
| `tests/test_bdib.py`, `tests/test_ohlc_core.py`, `tests/test_ohlc_plots.py` | Mocked pdblp; synthetic OHLC fixtures; figure-structure assertions |
| `examples/` | Notebook + a **synthetic** intraday sample CSV (see risk on data licensing) |
| `README.md`, `pyproject.toml` | Docs; `bloomberg` extra unchanged unless the library decision changes it |

### 5.5 Phases

1. **Decisions** — answer the questions below; freeze API names and defaults.
2. **Data layer** — `_parse_interval`, `_bbg_connection`, `read_bdib`
   (single + multi ticker, UTC → tz, event types, retention-window warning,
   1d via BDH). Fully mocked tests. *Requires one live run on the user's
   terminal to confirm bar alignment, retention and FX event types.*
3. **Core** — `validate_ohlc`, `resample_ohlc` with session anchoring; tests.
4. **Plotly chart** — candles, volume pane, compressed axis, crosshair,
   hover, last-price tag, line overlays, chrome; tests.
5. **matplotlib chart** — parity subset (candles, volume, overlays, chrome).
6. **Accessor, exports, README, example notebook, synthetic sample data.**
7. **Live validation** on the terminal (user) and fixes.
8. *Optional follow-ups*: local cache, indicator helpers, dark mode,
   compare overlay, streaming last bar.

### 5.6 Risks and constraints

- **No Bloomberg here.** Everything in the data layer is written against
  documented behaviour and mocks; the first live run will likely surface
  small fixes (alignment, timezone edge cases, field names).
- **Data licensing.** Bloomberg Terminal data must not be redistributed, and
  the repo is on GitHub. Example data for the notebook and test fixtures
  should be synthetic (random-walk OHLC), not a terminal export.
- **pdblp maintenance.** Works today; if `blpapi` changes break it there is
  no upstream fix. `blp` / `xbbg` are the escape hatches.
- **Plotly rangeslider** is on by default for candlestick traces and must be
  disabled explicitly to match pxts (Phase 8 removed range sliders).
- **Gap handling** is the main visual-quality risk; the integer-index
  approach is the safest route to TradingView's look but needs careful
  tick labelling at each interval (e.g. "09:35", then "Tue 14" at day
  boundaries, "Sep" at month boundaries).
- **Daylight saving.** Session anchoring must be done in the exchange's
  timezone, then converted to the display timezone.

---

## 6. Open questions

### Scope and usage
1. **Asset classes.** Mostly index futures (ES1/NQ1 as in the sample) and
   equities, or also FX (`Curncy`) and rates? This decides the default
   `event` type and whether a volume pane is on by default.
2. **Bloomberg library.** Stay on pdblp (consistent with `read_bdh`, least
   change, maintenance mode), switch to its successor `blp`, or adopt `xbbg`
   (built-in exchange sessions, parquet cache)? A switch would also touch
   `read_bdh`.
3. **Where will this be used?** Jupyter only (Plotly first, matplotlib can
   wait), or do you need static matplotlib candles for reports too?
4. **Chart function name and shape.** New `ohlcplot()` + `df.ts.ohlcplot()`,
   or extend `tsplot` (for example `tsplot(df, kind="candle")`)?
5. **Reader name.** `read_bdib` (Bloomberg's own name for intraday bars) or
   something descriptive like `read_bbg_intraday`?

### Data layer
6. **1d bars**: from BDH (exchange sessions, unlimited history) or from the
   intraday request with interval=1440 (UTC days, 140-day cap)? I recommend
   BDH.
7. **2h / 4h anchoring.** Anchor to the exchange session open (TradingView
   behaviour for stocks and futures) or to midnight UTC? Do you want to
   supply the session explicitly per call, or should pxts carry a small
   built-in table (CME, NYSE, LSE, Eurex, ...)?
8. **Fetch strategy.** Native N-minute bars from Bloomberg, or always pull
   1-minute and resample locally (one download serves every interval,
   deterministic anchoring, bigger pull)? Or both with a parameter?
9. **Display timezone default.** UTC, `Europe/London`, or exchange local?
   Should the returned DataFrame be tz-aware (pxts convention via `set_tz`)
   or tz-naive local time?
10. **Multiple tickers.** Single-ticker only for v1, or multi-ticker now? If
    multi, return a `dict[ticker -> DataFrame]`, a MultiIndex-column frame, or
    a long frame?
11. **Default `end`.** Now (`pd.Timestamp.utcnow()`), like `read_bdh`
    defaults to today?
12. **Default lookback when `start` is omitted.** Something like the last
    5 trading days for 1-min and the full retention window for 1h+?
13. **Local cache.** Do you want history to accumulate on disk beyond the
    Bloomberg retention window? If so CSV (no new dependency) or parquet
    (pyarrow, deferred in v0.1)?
14. **Corporate-action adjustments** for equities (`adjustmentSplit` etc.):
    expose explicitly, or just pass through via `**bbg_options`?
15. **Chunking and timeouts.** Is a 140-day 1-minute pull for a 24h future
    (about 200k bars) a realistic use case for you, or will pulls typically
    be a few days? This decides whether weekly chunking is worth it in v1.

### Chart look and behaviour
16. **Candles or bars** by default: filled candlesticks (TradingView
    default), hollow candles, or OHLC bars? Should `style=` offer all three?
17. **Colours.** TradingView green/red (`#26a69a` / `#ef5350`) or something
    closer to the FT palette? Colourblind-safe alternative (blue/orange)
    as an option?
18. **Volume pane.** On by default when a volume column exists? Height ratio
    (TradingView uses roughly 20 to 25 percent)?
19. **Price axis side.** Right (TradingView) or left (current pxts)?
20. **Gap handling.** Compressed integer axis (true TradingView look, no
    overnight/weekend gaps, custom tick labels) or Plotly date axis with
    `rangebreaks` (keeps native date zoom, needs session/holiday rules)?
21. **Crosshair and hover.** Unified hover showing O/H/L/C/Vol and change,
    plus x/y spike labels on the axes? Anything else from TradingView you
    rely on (for example the O H L C readout row)?
22. **Last-price line and tag.** Wanted by default?
23. **Pan/zoom feel.** Default `dragmode="pan"` with scroll-to-zoom, or keep
    Plotly's box-zoom default used by `tsplot`?
24. **Range-selector buttons** (1D / 5D / 1M / 3M / All) above the chart?
    `tsplot` currently has none.
25. **Line overlays.** Confirm that extra columns via `yaxis={"cols": ...}`
    should draw as pxts lines on the price panel, and whether `yaxis2`
    (second axis) is needed in v1.
26. **Indicators.** Should pxts ship SMA/EMA/VWAP/Bollinger helpers that add
    columns, or will you compute those yourself?
27. **Dark mode.** The theme has unused dark constants from Phase 7. Want a
    TradingView-style dark option, or keep light/FT only?
28. **Default title and source.** `tsplot` infers the DataFrame variable name
    as the title and defaults source to "Own calculations". For OHLC, should
    the default title be the ticker and interval (e.g. "ES1 Index — 5min")
    and the source "Bloomberg"?

### Testing and examples
29. **Can you share a small real intraday export** (even a few days of one
    ticker) for me to eyeball shapes, with the understanding it will *not*
    be committed? Otherwise I will build synthetic fixtures.
30. **Is the GitHub repo public?** If so, example data stays synthetic.
31. **Live testing loop.** Are you able to run the live Bloomberg checks on
    your terminal after each phase and paste results back?

---

## 7. Suggested answers if you want a fast default

If you would rather I pick: pdblp, Plotly first, new `ohlcplot` + `read_bdib`,
1d via BDH, native N-minute bars with session-anchored resampling as a
fallback, tz-aware index converted to `Europe/London`, single ticker in v1,
filled candles in TradingView colours, volume pane on when present, right
price axis, integer-index compressed time axis, unified hover + spikes,
last-price tag on, pan/scroll-zoom on, no range buttons, overlays via
`yaxis["cols"]`, no built-in indicators, light theme only, default title
"<ticker> — <interval>" and source "Bloomberg", synthetic sample data.
