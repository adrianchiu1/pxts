# Concerns

## Critical

### 1. No Test Suite
**Severity: Critical**
The `tests/` directory does not exist. All library functionality is completely untested despite pytest being declared as a dev dependency. Any change to any module risks undetected regressions.
- **File**: `pyproject.toml:18` (`testpaths = ["tests"]` — directory does not exist)

### 2. Undeclared Runtime Dependencies
**Severity: High**
- `cycler` is used in `theme.py:93` (`from cycler import cycler`) but is not declared in `pyproject.toml` dependencies. It is typically installed as a matplotlib transitive dependency, but relying on that is fragile.
- `adjustText` is used in `plots.py:178` (`from adjustText import adjust_text`) — also undeclared. The code has a graceful fallback (`_manual_deconflict`), but users expecting label deconfliction may silently get the inferior fallback without knowing.
- **Files**: `src/pxts/theme.py:93`, `src/pxts/plots.py:178`, `pyproject.toml:9`

## High

### 3. Ambiguous Date Format Detection with Silent US Default
**Severity: High**
`_detect_date_format()` in `io.py` silently defaults to US format (`MM/DD/YYYY`) when a slash-delimited date is ambiguous (both day and month parts ≤ 12). For example, `01/02/2024` is interpreted as January 2nd, not February 1st, with no warning to the user. This can silently corrupt datetime indices for UK/European CSV files.
- **File**: `src/pxts/io.py:60-62`

### 4. IS_JUPYTER Cached at Import Time
**Severity: Medium-High**
`IS_JUPYTER` is a module-level constant set once when `_backend.py` is imported. If `pxts` is imported in a script context and then used inside a Jupyter cell (e.g., via `importlib.reload`), `IS_JUPYTER` will remain `False` and plotly will not be used. Documented as an accepted trade-off, but could surprise users.
- **File**: `src/pxts/_backend.py:42`

### 5. Timezone Comparison Fragility
**Severity: Medium**
`set_tz` uses string comparison to check if the index is already at the target timezone:
```python
str(index.tz) == str(pd.Timestamp("now", tz=tz).tz) or (tz == "UTC" and str(index.tz) == "UTC")
```
This is fragile — `"UTC"` and `"pytz.UTC"` or `"Etc/UTC"` may compare as unequal even when semantically equivalent. This could trigger unnecessary tz conversions with spurious UserWarnings.
- **File**: `src/pxts/core.py:42-44`

## Medium

### 6. B vs D Frequency Ambiguity
**Severity: Medium**
`infer_freq()` cannot distinguish business day (`'B'`) from calendar day (`'D'`) because a 1-day timedelta maps to `Day` offset. This is documented in comments but not surfaced to users at runtime. Users calling `to_dense(df, freq='B')` after `infer_freq()` returns `'D'` will silently get the wrong densification.
- **Files**: `src/pxts/core.py:73-75`, `src/pxts/core.py:90-95`

### 7. Global State Mutation at Import Time
**Severity: Medium**
`apply_theme()` mutates global matplotlib `rcParams` and registers a global plotly template at import time. This is a side effect that affects the entire Python process — any other matplotlib/plotly plots in the same session will use the pxts theme. This could surprise users who import pxts alongside other visualization libraries.
- **File**: `src/pxts/theme.py:89-120`, `src/pxts/__init__.py:45`

### 8. No Input Validation on Plot Parameters
**Severity: Medium**
`plot_ts` validates column names (`_validate_cols`) but does not validate `hlines`, `vlines`, `title`, `subtitle`, or `date_format` types. Passing a wrong type (e.g., `hlines=42` instead of a list) will produce confusing low-level errors deep in matplotlib/plotly internals rather than clear pxts messages.
- **File**: `src/pxts/plots.py:481-517`

## Low

### 9. Manual Deconfliction Approximation
**Severity: Low**
`_manual_deconflict()` uses a simplified spacing algorithm that operates in data coordinates rather than display coordinates. The `min_spacing_pt: float = 12` parameter is labeled as "approximate" in code comments. This fallback (when `adjustText` is not installed) may produce overlapping labels in some cases.
- **File**: `src/pxts/plots.py:136-153`

### 10. No Version Constraint on Upper Bounds
**Severity: Low**
Dependencies in `pyproject.toml` specify only lower bounds (`pandas>=2.0`, `plotly>=5.0`, `matplotlib>=3.5`). A future breaking change in any of these libraries could silently break pxts without a clear signal to users.
- **File**: `pyproject.toml:9-13`

### 11. `_detect_plotly_tickformat` Uses Only First/Last Index Points
**Severity: Low**
The span is calculated as `df.index[-1] - df.index[0]`. For sparse DataFrames with a few data points at extreme dates, this may select an inappropriate tickformat (e.g., showing only years for a sparse 4-year dataset with monthly data points).
- **File**: `src/pxts/plots.py:52-66`

### 12. No Support for Non-CSV File Formats
**Severity: Low (scope)**
The `__init__.py` docstring mentions "CSV/Parquet" for `read_ts`/`write_ts` but only CSV is implemented. The Parquet mention could mislead users expecting Parquet support.
- **File**: `src/pxts/__init__.py:11-12`

### 13. `to_dense` No-op Check Uses `freqstr` String Comparison
**Severity: Low**
`to_dense` checks `df.index.freqstr == freq` to detect no-op cases. If `freq` is a valid alias that normalizes differently (e.g., `'1D'` vs `'D'`), the no-op guard won't trigger even when the index is already at the requested frequency, resulting in a redundant `asfreq` call.
- **File**: `src/pxts/core.py:79`
