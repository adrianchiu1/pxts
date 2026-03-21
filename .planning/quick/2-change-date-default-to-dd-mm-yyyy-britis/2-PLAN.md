---
phase: quick
plan: 2
type: execute
wave: 1
depends_on: []
files_modified:
  - src/pxts/io.py
  - tests/test_io.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Ambiguous slash-delimited dates (e.g. 01/02/2024) are parsed as DD/MM/YYYY (British)"
    - "A UserWarning is still emitted for ambiguous dates, now pointing to the British assumption"
    - "All existing tests pass"
  artifacts:
    - path: "src/pxts/io.py"
      provides: "British default in _detect_date_format ambiguous branch"
      contains: "return (\"%d/%m/%Y\", True)"
    - path: "tests/test_io.py"
      provides: "Updated assertions reflecting British default"
  key_links:
    - from: "src/pxts/io.py"
      to: "_detect_date_format ambiguous branch"
      via: "return statement"
      pattern: "return.*%d/%m/%Y.*True"
---

<objective>
Change the ambiguous date fallback in `_detect_date_format` from US (MM/DD/YYYY) to British (DD/MM/YYYY). Update the warning message and the two tests that assert the old US default.

Purpose: Align the library's default with British date conventions, as requested.
Output: Updated `io.py` and `test_io.py` with British-first ambiguous date handling.
</objective>

<execution_context>
@C:/Users/adria/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/adria/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@src/pxts/io.py
@tests/test_io.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Switch ambiguous date default to British (DD/MM/YYYY)</name>
  <files>src/pxts/io.py</files>
  <action>
In `_detect_date_format`, locate the ambiguous branch (the `else` block at line 62, where both `first` and `second` are <= 12).

Make three changes:

1. Update the docstring comment on line 43:
   - Old: `ambiguous (both <= 12) -> default to US ("%m/%d/%Y", False)`
   - New: `ambiguous (both <= 12) -> default to British ("%d/%m/%Y", True)`

2. Update the warning message (lines 63-65):
   - Old: `"pxts: ambiguous date '{sample}' — assumed MM/DD/YYYY (US). Pass date_format='%d/%m/%Y' to override."`
   - New: `"pxts: ambiguous date '{sample}' — assumed DD/MM/YYYY (British). Pass date_format='%m/%d/%Y' to override."`

3. Change the return value (line 69):
   - Old: `return ("%m/%d/%Y", False)`
   - New: `return ("%d/%m/%Y", True)`

Do NOT touch any other branches (ISO, unambiguous UK, unambiguous US, or fallback).
  </action>
  <verify>
    <automated>cd /c/Users/adria/Desktop/pxts && python -c "from pxts.io import _detect_date_format; import warnings; r = warnings.catch_warnings(record=True); warnings.simplefilter('always'); result = _detect_date_format('01/02/2024'); print('Result:', result); assert result == ('%d/%m/%Y', True), f'Expected British default, got {result}'; print('PASS')"</automated>
  </verify>
  <done>Ambiguous dates return ("%d/%m/%Y", True) and the warning message references "British" convention.</done>
</task>

<task type="auto">
  <name>Task 2: Update tests to assert British default</name>
  <files>tests/test_io.py</files>
  <action>
Update the two tests that asserted the old US default behaviour:

**Test 1 — `test_ambiguous_defaults_to_us` (line 41):**
- Rename to: `test_ambiguous_defaults_to_british`
- Update docstring: `Both parts ≤ 12 → ambiguous → defaults to British format with a UserWarning.`
- Change assertion: `assert result == ("%d/%m/%Y", True)`
- Update `pytest.warns` match to: `match="ambiguous date"` (unchanged — warning still fires)

**Test 2 — `test_ambiguous_slash_csv_treated_as_us` (line 103):**
- Rename to: `test_ambiguous_slash_csv_treated_as_british`
- Update docstring: `Ambiguous slash date (01/02/2024) defaults to British with a UserWarning.`
- Update comment on line 110: `# British default: 01/02/2024 → February 1, 2024`
- Change Timestamp assertion: `assert df.index[0] == pd.Timestamp("2024-02-01")`

Do NOT modify any other tests. The `test_explicit_date_format_suppresses_warning` test at line 113 is unaffected.
  </action>
  <verify>
    <automated>cd /c/Users/adria/Desktop/pxts && python -m pytest tests/test_io.py -x -q 2>&1 | tail -10</automated>
  </verify>
  <done>All tests in `test_io.py` pass with no failures or warnings about unexpected test names.</done>
</task>

</tasks>

<verification>
Run the full test suite to confirm no regressions:

```
cd /c/Users/adria/Desktop/pxts && python -m pytest tests/ -x -q
```

Expected: all tests pass. The two renamed tests now assert British default behaviour.
</verification>

<success_criteria>
- `_detect_date_format("01/02/2024")` returns `("%d/%m/%Y", True)` and emits a UserWarning mentioning "British"
- `read_ts` on a file with `01/02/2024` produces `pd.Timestamp("2024-02-01")` (February 1, not January 2)
- Full `pytest tests/` run exits 0
</success_criteria>

<output>
After completion, create `.planning/quick/2-change-date-default-to-dd-mm-yyyy-britis/2-SUMMARY.md`
</output>
