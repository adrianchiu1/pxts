---
phase: quick
plan: 6
type: execute
wave: 1
depends_on: []
files_modified: [README.md]
autonomous: true
requirements: [QUICK-6]
must_haves:
  truths:
    - "A financial researcher reading the README knows exactly what pxts does in one paragraph"
    - "Install instructions cover base package, optional plot extras, and Bloomberg extra"
    - "Usage examples show read_ts, tsplot, tsplot_dual, and read_bdh with realistic financial data"
    - "API reference covers all public symbols with one-line descriptions"
    - "A reader knows about the .ts accessor and the auto-applied Okabe-Ito theme"
  artifacts:
    - path: "README.md"
      provides: "Public-facing GitHub README"
      min_lines: 120
  key_links:
    - from: "README.md install section"
      to: "pyproject.toml optional-dependencies"
      via: "pip install pxts[bloomberg] and pip install pxts[plot]"
      pattern: "pxts\\[bloomberg\\]"
---

<objective>
Write a public-facing README.md for the pxts package suitable for GitHub.

Purpose: Give financial researchers and quants a clear, scannable entry point — what pxts is, how to install it, and concrete usage examples they can copy-paste.
Output: README.md at the repo root covering purpose, installation (core + extras), usage examples (read_ts, tsplot, tsplot_dual, read_bdh), the .ts accessor, and a brief API reference table.
</objective>

<execution_context>
@C:/Users/adria/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/adria/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md
@src/pxts/__init__.py
@src/pxts/io.py
@pyproject.toml
</context>

<tasks>

<task type="auto">
  <name>Task 1: Write README.md</name>
  <files>README.md</files>
  <action>
Create README.md at the repo root. Write for a financial researcher / quant audience — concise, precise, no fluff. Structure:

**1. Header**
- Package name `pxts` as H1
- One-sentence tagline: "Financial time series utilities for pandas — load, manipulate, and visualize with no boilerplate."
- Python >= 3.9 badge (static shield) and pandas >= 2.0 badge

**2. What it is (2–3 sentences)**
- A Python library wrapping pandas for financial time series workflows
- Auto-detects date formats (ISO 8601, UK DD/MM/YYYY, US MM/DD/YYYY) on CSV read
- Dual-backend visualization (matplotlib for scripts, plotly for Jupyter) applied automatically; Okabe-Ito color theme applied at import

**3. Installation**
Three pip commands in a code block:
```bash
# Core (validation, I/O, no plotting)
pip install pxts

# With plotting backends
pip install pxts[plot]

# With Bloomberg BDH support (requires Bloomberg Terminal + API)
pip install pxts[bloomberg]
```

**4. Quick start — four usage examples**

Example 1 — Read a CSV:
```python
from pxts import read_ts, write_ts

df = read_ts("prices.csv")            # date format auto-detected
df = read_ts("prices.csv", tz="UTC")  # localize to UTC
write_ts(df, "prices_out.csv")        # ISO 8601 round-trip
```

Example 2 — Core utilities:
```python
from pxts import validate_ts, set_tz, to_dense, infer_freq

validate_ts(df)                      # raises pxtsValidationError if no DatetimeIndex
df = set_tz(df, tz="US/Eastern")     # normalize timezone
df = to_dense(df, freq="B")          # fill to business-day frequency
freq = infer_freq(df)                # returns "B", "D", "W", etc.
```

Example 3 — Plot time series (use realistic equity column names like "AAPL", "MSFT"):
```python
from pxts import tsplot, tsplot_dual

# Single-axis: all columns or a subset
tsplot(df, title="Equity Prices")
tsplot(df, cols=["AAPL", "MSFT"], hlines=[100.0], labels=True)

# Dual-axis: left vs right y-axis
tsplot_dual(df, left=["AAPL"], right=["10Y_YIELD"],
            title="Price vs Yield", ylim_lhs=[80, 200], ylim_rhs=[0, 5])
```

Example 4 — Bloomberg BDH (requires `pxts[bloomberg]` and a live Bloomberg Terminal):
```python
from pxts import read_bdh

df = read_bdh(
    tickers=["AAPL US Equity", "MSFT US Equity"],
    start="2023-01-01",
    end="2024-01-01",
    field="PX_LAST",          # default
)
# Returns wide-format DataFrame: rows = dates, columns = tickers
```

**5. The .ts accessor**
Short paragraph + example:
```python
import pxts  # registers .ts on pd.DataFrame

df = df.ts.set_tz("UTC")
df = df.ts.to_dense(freq="D")
freq = df.ts.infer_freq()
```

**6. API reference**
Markdown table with columns: Function/Name | Description | Notes

Rows (one per public symbol from __all__):
- read_ts(path, *, tz, date_format) | Read CSV into DatetimeIndex DataFrame | Auto-detects ISO/UK/US dates
- write_ts(df, path, *, date_format) | Write DataFrame to CSV | Defaults to ISO 8601
- read_bdh(tickers, start, field, end) | Fetch Bloomberg BDH historical data | Requires pxts[bloomberg]
- validate_ts(df) | Assert DatetimeIndex; raises pxtsValidationError | Also returns df for chaining
- set_tz(df, tz) | Localize or convert index timezone | tz='UTC', 'US/Eastern', etc.
- to_dense(df, freq, fill) | Regularize sparse index to uniform freq | fill=None → forward-fill
- infer_freq(df) | Infer minimum interval of index | Returns 'B', 'D', 'W', 'M', etc.
- tsplot(df, cols, ...) | Single-axis time series line chart | Auto-selects matplotlib/plotly
- tsplot_dual(df, left, right, ...) | Dual y-axis line chart | left/right are column lists
- pxtsValidationError | Exception raised on invalid DatetimeIndex | Subclass of ValueError
- get_backend() | Returns active backend: 'plotly' or 'matplotlib' | Auto-detected from environment
- IS_JUPYTER | True if running in Jupyter/IPython | Cached at import time

**7. Date format behavior**
One short paragraph noting:
- ISO 8601 (YYYY-MM-DD) is detected automatically and unambiguous
- Slash-delimited dates (DD/MM/YYYY or MM/DD/YYYY): defaults to British (DD/MM/YYYY) when ambiguous; emits UserWarning; override with `date_format='%m/%d/%Y'`

**8. Theme**
One sentence: pxts applies the Okabe-Ito colorblind-safe palette and a clean white/gray-grid style to both matplotlib and plotly at import time.

**9. Requirements**
- Python >= 3.9
- pandas >= 2.0
- cycler (bundled with matplotlib, listed explicitly)
- Optional: plotly >= 5.0, matplotlib >= 3.5 (`pxts[plot]`)
- Optional: pdblp (`pxts[bloomberg]`) — requires Bloomberg Terminal

Do NOT include: contributing guide, changelog, license section (no LICENSE file exists yet), CI badges, or roadmap items.
  </action>
  <verify>
    <automated>python -c "import pathlib; c = pathlib.Path('README.md').read_text(); assert 'pxts[bloomberg]' in c; assert 'read_bdh' in c; assert 'tsplot' in c; assert 'read_ts' in c; assert 'DD/MM/YYYY' in c; print('README validation passed')"</automated>
  </verify>
  <done>README.md exists at repo root; contains install instructions for all three extras; has four usage examples; has API reference table; passes automated content check</done>
</task>

</tasks>

<verification>
Run the automated verify command above. Then visually confirm:
- README renders cleanly as markdown (no broken code fences)
- All code examples are syntactically valid Python
- install commands reference correct extras: pxts[plot], pxts[bloomberg]
</verification>

<success_criteria>
A financial researcher or quant can read README.md on GitHub and immediately understand: (1) what pxts is, (2) how to install it for their use case, (3) how to load data from CSV or Bloomberg, (4) how to plot it, and (5) what every public symbol does.
</success_criteria>

<output>
After completion, create `.planning/quick/6-write-readme-md-for-pxts-package/6-SUMMARY.md` with what was built, key decisions made, and the file path created.
</output>
