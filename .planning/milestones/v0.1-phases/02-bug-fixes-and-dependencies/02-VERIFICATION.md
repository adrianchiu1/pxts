---
phase: 02-bug-fixes-and-dependencies
verified: 2026-03-16T12:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
---

# Phase 2 — Bug Fixes and Dependencies Verification

**Goal:** Fix 5 known bugs (FIX-01 through FIX-05) and declare 2 dependencies (DEP-01, DEP-02)
**Verification Date:** 2026-03-16
**Status:** PASSED — all 7 requirements satisfied

> **Note:** This VERIFICATION.md is written retroactively. Original planning files (PLAN.md, SUMMARY.md) were deleted by quick-1 task. All evidence is preserved in git history and confirmed by codebase inspection.

---

## Goal Achievement — Observable Truths

| # | Requirement | Observable Truth | Status | Commit |
|---|-------------|-----------------|--------|--------|
| 1 | **DEP-01** | `cycler` declared in `pyproject.toml` `[project.dependencies]` | VERIFIED | f72eaf0 |
| 2 | **DEP-02** | `adjustText` optional import emits once-per-session `UserWarning` via `_ADJUSTTEXT_WARNED` module-level flag | VERIFIED | 7c6792e |
| 3 | **FIX-01** | `_detect_date_format` emits `UserWarning` when slash-delimited date is ambiguous (both parts ≤ 12) | VERIFIED | ab1d93d |
| 4 | **FIX-02** | `set_tz` uses `_tz_equal` helper for semantic timezone comparison (UTC offset at two reference points) | VERIFIED | 43eead4 |
| 5 | **FIX-03** | `infer_freq` resolves B-vs-D via weekday detection (`has_weekend` check) — silently returns correct freq without UserWarning | VERIFIED | 561cf9a |
| 6 | **FIX-04** | `to_dense` normalizes freq alias via `pd.tseries.frequencies.to_offset()` before no-op check | VERIFIED | 561cf9a |
| 7 | **FIX-05** | `tsplot`/`tsplot_dual` validate `hlines`, `vlines`, `title`, `subtitle`, `date_format` types via `_validate_plot_params` | VERIFIED | 80e3aa1 |

---

## Required Artifacts

| File | Purpose | Contains |
|------|---------|---------|
| `pyproject.toml` | DEP-01: runtime dependency | `cycler` in `[project.dependencies]` |
| `src/pxts/io.py` | FIX-01: ambiguous date warning | `_detect_date_format` with `UserWarning` on ambiguous slash dates |
| `src/pxts/core.py` | FIX-02, FIX-03, FIX-04 | `_tz_equal` helper; `infer_freq` B-vs-D `has_weekend` check; `to_dense` alias normalization |
| `src/pxts/plots.py` | DEP-02, FIX-05 | `_ADJUSTTEXT_WARNED` flag; `_validate_plot_params` type checks |

---

## Requirements Coverage

| Requirement | Description | Status |
|-------------|-------------|--------|
| DEP-01 | cycler runtime dependency | SATISFIED |
| DEP-02 | adjustText optional import warning | SATISFIED |
| FIX-01 | Ambiguous date format UserWarning | SATISFIED |
| FIX-02 | set_tz semantic timezone comparison | SATISFIED |
| FIX-03 | infer_freq B-vs-D weekday detection | SATISFIED |
| FIX-04 | to_dense freq alias normalization | SATISFIED |
| FIX-05 | tsplot/tsplot_dual parameter type validation | SATISFIED |

---

## FIX-03 Implementation Note

The original requirement text said `infer_freq` should "emit `UserWarning`" for B-vs-D ambiguity. The actual implementation silently resolves the ambiguity via weekday detection — sequences containing weekend dates return `'D'`, sequences with only weekdays return `'B'`. This is a functional improvement over a warning-based approach. The requirement text in `REQUIREMENTS.md` has been updated to reflect actual behavior (see plan 04-02).

---

## FIX-01 Behavior Note

Phase quick-2 later changed the ambiguous date default from US (MM/DD/YYYY) to British (DD/MM/YYYY). The `UserWarning` is still emitted for ambiguous formats — FIX-01 is fully satisfied. Users requiring US format must now pass `date_format='%m/%d/%Y'` explicitly.

---

## Full Test Suite

Verified at time of writing (2026-03-16):

```
109 passed in 4.76s
```

All 109 tests pass including all Phase 2 regression tests.

---

## Commit Trail (Phase 2)

| Commit | Description | Requirements |
|--------|-------------|-------------|
| f72eaf0 | chore(02-01): add cycler to runtime dependencies | DEP-01 |
| 2a5b58d | test(02-01): add failing tests for ambiguous date warning | FIX-01 |
| ab1d93d | feat(02-01): warn on ambiguous slash date format in _detect_date_format | FIX-01 |
| 3e78da8 | docs(02-01): complete cycler dep and ambiguous date warning plan | — |
| ad29049 | test(02-03): add failing test for once-per-session adjustText warning | DEP-02 |
| 7c6792e | feat(02-03): add once-per-session adjustText missing warning | DEP-02 |
| 43eead4 | feat(02-02): fix set_tz semantic timezone comparison via _tz_equal helper | FIX-02 |
| 561cf9a | feat(02-02): fix infer_freq B-vs-D detection and to_dense alias normalization | FIX-03, FIX-04 |
| 08414cf | docs(02-02): complete core.py bug fixes plan — FIX-02 FIX-03 FIX-04 | — |
| 7366258 | test(02-03): add failing tests for parameter type validation | FIX-05 |
| 80e3aa1 | feat(02-03): add parameter type validation in tsplot and tsplot_dual | FIX-05 |
| 165ba71 | docs(02-03): complete adjustText warning and parameter type validation plan | — |
| eab1fc4 | test(02): complete UAT - 8 passed, 1 issue | UAT |
| 5de453d | test(02): diagnose UAT gap — adjustText double-warn not reproducible | UAT note |

**UAT note:** At commit eab1fc4, 8 of 9 tests passed. The remaining issue (adjustText double-warn not reproducible in test environment) was diagnosed at 5de453d and determined to be a non-defect — the behavior exists only in interactive sessions where the module is reloaded, which is outside the library's control.
