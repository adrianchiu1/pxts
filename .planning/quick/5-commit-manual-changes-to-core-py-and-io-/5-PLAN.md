---
phase: quick-5
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - src/pxts/core.py
  - src/pxts/io.py
  - tests/test_bdh.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "All 117 tests pass with no failures"
    - "core.py and io.py manual changes are committed to git"
  artifacts:
    - path: "src/pxts/core.py"
      provides: "validate_ts with UniqueIndex and non-MultiIndex checks"
    - path: "src/pxts/io.py"
      provides: "read_bdh with updated ImportError message, str ticker coercion, timeout=5000, direct column selection"
    - path: "tests/test_bdh.py"
      provides: "test_importerror_without_pdblp matching updated error message"
  key_links:
    - from: "tests/test_bdh.py::test_importerror_without_pdblp"
      to: "src/pxts/io.py ImportError message"
      via: "pytest.raises(ImportError, match=...)"
      pattern: "pip install pdblp"
---

<objective>
Fix the one broken test caused by the changed ImportError message in io.py, then stage and commit all manual changes to core.py and io.py.

Purpose: The manual edits to core.py and io.py are solid but broke one test assertion that checks the old ImportError message text. Align the test to the new message, verify all tests pass, then commit.
Output: A single git commit containing core.py, io.py, and tests/test_bdh.py changes.
</objective>

<execution_context>
@C:/Users/adria/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/adria/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix broken test assertion for updated ImportError message</name>
  <files>tests/test_bdh.py</files>
  <action>
In tests/test_bdh.py, find the test `test_importerror_without_pdblp`. It currently asserts:

    pytest.raises(ImportError, match=r"pip install pxts\[bloomberg\]")

The io.py ImportError message was changed to:

    "pdblp required for read_bdh(). Install with: pip install pdblp and https://www.bloomberg.com/professional/support/api-library/"

Update the `match=` regex to match the new message. Use a substring that will not break if the URL changes slightly:

    match=r"pip install pdblp"

Do not change anything else in the test file.
  </action>
  <verify>
    <automated>python -m pytest tests/test_bdh.py::TestReadBdh::test_importerror_without_pdblp -v</automated>
  </verify>
  <done>test_importerror_without_pdblp passes (1 passed, 0 failed)</done>
</task>

<task type="auto">
  <name>Task 2: Verify full test suite and commit all changes</name>
  <files>src/pxts/core.py, src/pxts/io.py, tests/test_bdh.py</files>
  <action>
1. Run the full test suite to confirm 0 failures.
2. Stage exactly these three files:
   - src/pxts/core.py
   - src/pxts/io.py
   - tests/test_bdh.py
3. Commit with the message:

   fix(core,io): validate_ts uniqueness/MultiIndex checks; read_bdh ticker coercion and timeout

   Details:
   - core.py: validate_ts raises AttributeError on MultiIndex or duplicate index; updated error message wording
   - io.py: coerce str ticker to list; timeout 20 -> 5000; updated ImportError install hint; replace xs() with direct .loc column selection; convert index to DatetimeIndex; return validate_ts(data)
   - tests/test_bdh.py: align ImportError match regex to new message

Do NOT stage untracked files (.planning/, .claude/, pycache, egg-info).
  </action>
  <verify>
    <automated>python -m pytest tests/ -q && git log --oneline -1</automated>
  </verify>
  <done>All 117 tests pass; git log shows the new commit at HEAD with correct message</done>
</task>

</tasks>

<verification>
Run `python -m pytest tests/ -q` — expect "117 passed" with 0 failures.
Run `git show --stat HEAD` — expect core.py, io.py, test_bdh.py in the diff.
</verification>

<success_criteria>
- 117 tests pass (0 failures, 0 errors)
- Exactly one new commit containing src/pxts/core.py, src/pxts/io.py, tests/test_bdh.py
- No untracked planning/cache files included in the commit
</success_criteria>

<output>
After completion, create `.planning/quick/5-commit-manual-changes-to-core-py-and-io-/5-SUMMARY.md` following the summary template.
</output>
