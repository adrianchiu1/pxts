---
phase: 02-bug-fixes-and-dependencies
plan: 02
subsystem: testing
tags: [pandas, timezone, frequency-detection, datetime]

# Dependency graph
requires:
  - phase: 01-test-suite
    provides: test_core.py with existing set_tz/infer_freq/to_dense tests
provides:
  - Semantic timezone comparison via _tz_equal (UTC vs Etc/UTC are a no-op)
  - infer_freq B-vs-D detection (weekday-only data returns 'B')
  - to_dense freq alias normalization ('1D' and 'D' treated as equivalent)
affects: [any code calling set_tz with equivalent UTC aliases, any code using infer_freq for business-day detection]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "UTC offset comparison at multiple reference points (winter + summer) to handle DST zones"
    - "to_offset() normalization before string comparison for pandas freq aliases"
    - "B-vs-D detection via weekday() check on index timestamps"

key-files:
  created: []
  modified:
    - src/pxts/core.py
    - tests/test_core.py

key-decisions:
  - "Use UTC offset comparison at two reference points (Jan 1 and Jul 1) instead of string key comparison for _tz_equal — handles pytz/zoneinfo/datetime.timezone heterogeneity"
  - "infer_freq B-vs-D check fires only when min_diff == 1 day; all other frequencies fall through to existing to_offset path"
  - "to_dense try/except around to_offset normalization lets invalid freq strings reach asfreq for descriptive errors"

patterns-established:
  - "Timezone equality: compare utcoffset() at two calendar points, not string representations"
  - "Freq alias equality: normalize via to_offset().freqstr before string comparison"

requirements-completed: [FIX-02, FIX-03, FIX-04]

# Metrics
duration: 12min
completed: 2026-03-15
---

# Phase 2 Plan 2: Bug Fixes — set_tz, infer_freq, to_dense Summary

**Three silent correctness bugs fixed in core.py: semantic timezone comparison via UTC-offset helper, B-vs-D business-day detection in infer_freq, and freq alias normalization ('1D' == 'D') in to_dense**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-15T01:56:16Z
- **Completed:** 2026-03-15T02:08:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- FIX-02: `set_tz(df_utc, 'Etc/UTC')` is now a true no-op — `_tz_equal` compares UTC offsets at winter and summer reference points, correctly handling pytz/zoneinfo/datetime.timezone heterogeneity
- FIX-03: `infer_freq` returns `'B'` for weekday-only daily data and `'D'` for data containing weekend timestamps — replaces the always-wrong `'D'` return
- FIX-04: `to_dense(df, freq='1D')` on a `'D'`-frequency DataFrame is now a no-op — `to_offset(freq).freqstr` normalization before comparison

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix set_tz semantic timezone comparison (FIX-02)** - `43eead4` (feat)
2. **Task 2: Fix infer_freq B-vs-D detection and to_dense alias normalization (FIX-03, FIX-04)** - `561cf9a` (feat)

_Note: TDD tasks — RED and GREEN committed together per task (untracked source files prevent stashing)_

## Files Created/Modified

- `src/pxts/core.py` - Added `_tz_equal()` helper; updated `set_tz` elif branch; updated `to_dense` no-op guard; updated `infer_freq` with B-vs-D branch
- `tests/test_core.py` - Added `test_set_tz_etc_utc_is_noop`; replaced `test_infer_freq_daily_returns_D` with `test_infer_freq_daily_weekdays_returns_B`; added `test_infer_freq_daily_with_weekends_returns_D`; replaced `test_to_dense_freqstr_mismatch_not_noop` with `test_to_dense_1D_alias_is_noop`; added `test_to_dense_different_freq_is_not_noop`

## Decisions Made

- Used UTC offset comparison at winter (2000-01-01) and summer (2000-07-01) reference points for `_tz_equal` — avoids pytz zone name heterogeneity while correctly distinguishing DST zones from fixed-offset zones (e.g., `Etc/GMT+5` vs `US/Eastern` diverge in summer)
- The plan originally suggested `pd.Timestamp("2000-01-01", tz=tz).tz` string comparison — this was discovered to fail because pandas preserves the input alias (`'Etc/UTC'` stays `'Etc/UTC'`, not normalized to `'UTC'`). Switched to utcoffset comparison.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] _tz_equal implementation changed from string-key to utcoffset comparison**
- **Found during:** Task 1 (FIX-02 implementation)
- **Issue:** The plan specified normalizing via `str(pd.Timestamp("2000-01-01", tz=tz).tz)` — this returns `'Etc/UTC'` not `'UTC'` on the tested pandas version, so the equality check still fails
- **Fix:** Compare `pd.Timestamp(ref, tz=tz_a).utcoffset()` vs `pd.Timestamp(ref, tz=tz_b).utcoffset()` at two reference points
- **Files modified:** src/pxts/core.py
- **Verification:** All set_tz tests pass including `test_set_tz_etc_utc_is_noop`
- **Committed in:** 43eead4 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in plan's suggested implementation)
**Impact on plan:** Fix achieves the same semantic goal (canonical timezone equality) with a more robust mechanism.

## Issues Encountered

- `pd.Timestamp("2000-01-01", tz=tz).tz` preserves the input alias rather than normalizing — discovered during RED→GREEN phase. Resolved by switching to `utcoffset()` comparison at two calendar points.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All three targeted bugs (FIX-02, FIX-03, FIX-04) are fixed and verified with 89 passing tests
- `infer_freq` behavior change (returns 'B' for business-day data) may require downstream awareness in Phase 2 remaining plans

## Self-Check: PASSED

- src/pxts/core.py: FOUND
- tests/test_core.py: FOUND
- 02-02-SUMMARY.md: FOUND
- Commit 43eead4: FOUND
- Commit 561cf9a: FOUND

---
*Phase: 02-bug-fixes-and-dependencies*
*Completed: 2026-03-15*
