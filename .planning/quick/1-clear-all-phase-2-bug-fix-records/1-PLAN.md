---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - .planning/phases/02-bug-fixes-and-dependencies/02-01-PLAN.md
  - .planning/phases/02-bug-fixes-and-dependencies/02-01-SUMMARY.md
  - .planning/phases/02-bug-fixes-and-dependencies/02-02-PLAN.md
  - .planning/phases/02-bug-fixes-and-dependencies/02-02-SUMMARY.md
  - .planning/phases/02-bug-fixes-and-dependencies/02-03-PLAN.md
  - .planning/phases/02-bug-fixes-and-dependencies/02-03-SUMMARY.md
  - .planning/phases/02-bug-fixes-and-dependencies/02-CONTEXT.md
  - .planning/phases/02-bug-fixes-and-dependencies/02-UAT.md
  - .planning/phases/02-bug-fixes-and-dependencies/02-VERIFICATION.md
  - .planning/STATE.md
autonomous: true
requirements: []

must_haves:
  truths:
    - "The .planning/phases/02-bug-fixes-and-dependencies/ directory is empty (all files deleted)"
    - "STATE.md no longer references phase 2 plan records or summaries"
  artifacts:
    - path: ".planning/phases/02-bug-fixes-and-dependencies/"
      provides: "Empty directory (all phase 2 records removed)"
  key_links: []
---

<objective>
Delete all phase 2 (Bug Fixes and Dependencies) planning records from the filesystem and update STATE.md to reflect the cleared state.

Purpose: Phase 2 is fully complete and verified. Clearing its records frees up context and keeps the planning directory clean for active work.
Output: Empty phase 2 directory, updated STATE.md.
</objective>

<execution_context>
@C:/Users/adria/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/adria/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Delete all phase 2 planning files</name>
  <files>
    .planning/phases/02-bug-fixes-and-dependencies/02-01-PLAN.md,
    .planning/phases/02-bug-fixes-and-dependencies/02-01-SUMMARY.md,
    .planning/phases/02-bug-fixes-and-dependencies/02-02-PLAN.md,
    .planning/phases/02-bug-fixes-and-dependencies/02-02-SUMMARY.md,
    .planning/phases/02-bug-fixes-and-dependencies/02-03-PLAN.md,
    .planning/phases/02-bug-fixes-and-dependencies/02-03-SUMMARY.md,
    .planning/phases/02-bug-fixes-and-dependencies/02-CONTEXT.md,
    .planning/phases/02-bug-fixes-and-dependencies/02-UAT.md,
    .planning/phases/02-bug-fixes-and-dependencies/02-VERIFICATION.md
  </files>
  <action>
    Delete every file in .planning/phases/02-bug-fixes-and-dependencies/. Do not delete the directory itself, only its contents.

    Run: rm .planning/phases/02-bug-fixes-and-dependencies/02-01-PLAN.md .planning/phases/02-bug-fixes-and-dependencies/02-01-SUMMARY.md .planning/phases/02-bug-fixes-and-dependencies/02-02-PLAN.md .planning/phases/02-bug-fixes-and-dependencies/02-02-SUMMARY.md .planning/phases/02-bug-fixes-and-dependencies/02-03-PLAN.md .planning/phases/02-bug-fixes-and-dependencies/02-03-SUMMARY.md .planning/phases/02-bug-fixes-and-dependencies/02-CONTEXT.md .planning/phases/02-bug-fixes-and-dependencies/02-UAT.md .planning/phases/02-bug-fixes-and-dependencies/02-VERIFICATION.md
  </action>
  <verify>
    <automated>ls .planning/phases/02-bug-fixes-and-dependencies/ | wc -l</automated>
    Expected output: 0 (directory is empty).
  </verify>
  <done>All 9 phase 2 files are deleted. Directory exists but is empty.</done>
</task>

<task type="auto">
  <name>Task 2: Update STATE.md to reflect cleared phase 2 records</name>
  <files>.planning/STATE.md</files>
  <action>
    Read .planning/STATE.md and remove all references to phase 2 plan/summary records from the performance metrics table rows and the "Last activity" / "Stopped at" lines that describe phase 2 work.

    Specifically:
    1. Remove these four rows from the performance metrics table (they track phase 2 plan sizes):
       - "| Phase 02-bug-fixes-and-dependencies P02 | 12 | 2 tasks | 2 files |"
       - "| Phase 02-bug-fixes-and-dependencies P03 | 5 | 2 tasks | 2 files |"
       - "| Phase 02-bug-fixes-and-dependencies P01 | 5 | 2 tasks | 3 files |"
    2. Update "Current Position" section:
       - Change "Phase: 2 of 3 (Bug Fixes and Dependencies)" to "Phase: 3 of 3 (Documentation and Polish)"
       - Change "Plan: 2 of 3 in current phase" to "Plan: 0 of ? in current phase"
       - Change "Status: Phase 2 in progress" to "Status: Phase 3 not started"
       - Update "Last activity" line to: "Last activity: 2026-03-16 — Phase 2 records cleared"
    3. Update "Current focus" in Project Reference:
       - Change "**Current focus:** Phase 1 — Test Suite" to "**Current focus:** Phase 3 — Documentation and Polish"
    4. Update "Stopped at" in Session Continuity:
       - Change to: "Stopped at: Phase 2 complete and records cleared — ready for Phase 3"
       - Change "Resume file: None" — leave as is.
    5. Leave all other content (Decisions, Pending Todos, Blockers/Concerns, velocity metrics) unchanged.

    Write the updated STATE.md using the Write tool.
  </action>
  <verify>
    <automated>grep -c "02-bug-fixes-and-dependencies" .planning/STATE.md || echo "0"</automated>
    Expected output: 0 — no remaining phase 2 references in STATE.md.
  </verify>
  <done>STATE.md no longer references phase 2 plan records. Current position reflects phase 3 as the active phase.</done>
</task>

</tasks>

<verification>
After both tasks:
- ls .planning/phases/02-bug-fixes-and-dependencies/ returns empty
- grep "02-bug-fixes-and-dependencies" .planning/STATE.md returns no matches
</verification>

<success_criteria>
- All 9 phase 2 planning files are deleted
- STATE.md current position points to Phase 3
- STATE.md performance table has no phase 2 rows
- Directory .planning/phases/02-bug-fixes-and-dependencies/ still exists but is empty
</success_criteria>

<output>
No SUMMARY.md needed for this quick task. Changes are self-evidencing from the deleted files and updated STATE.md.
</output>
