# UAT Acceptance Record - HEALTH-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | HEALTH-001 |
| Objective | health scenario for django |
| Requirement | Phase 5 - Engineering Scenario: Repository Health Check. |
| Entry point | codetruth_report._health + generate (over run_platform) |
| Repository | C:\repos\v3\django |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T10:37:35.217019+00:00 |
| Finished (UTC) | 2026-07-06T10:58:30.286657+00:00 |
| Duration (s) | 1255.07 |
| Checks passed | 4/4 |

## Scenario (what this test verifies)
GIVEN an unfamiliar repository, WHEN a developer asks whether an automated analysis can be trusted, THEN the health verdict is SOUND iff zero fabrications and every decline categorized (integrity, not coverage).

## Expected result
kind=health; rating=SOUND; frozen before the run; identity/consistency-level checks.

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (codetruth_report._health + generate (over run_platform)).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| health_completed | status == COMPLETE | status=COMPLETE | PASS |
| health_rating | health_rating == SOUND | health_rating=SOUND (expected SOUND, risk=LOW) | PASS |
| health_zero_guesses | guesses == 0 | guesses=0 | PASS |
| health_all_declines_categorized | uncategorized_declines == 0 | uncategorized_declines=0 | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\django
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no
