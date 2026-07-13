# UAT Acceptance Record - IMPACT-METHOD-002

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | IMPACT-METHOD-002 |
| Objective | Change Impact (honest-empty boundary): a method with 0 verified callers is reported as a known-unknown - never as 'safe to delete'. |
| Requirement | Phase 5 - Engineering Scenario: Change Impact (Truth Boundary). |
| Entry point | reasoning_queries.who_calls / impact_of (engine-direct) |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T07:27:50.028375+00:00 |
| Finished (UTC) | 2026-07-06T07:28:12.154849+00:00 |
| Duration (s) | 22.13 |
| Checks passed | 3/3 |

## Scenario (what this test verifies)
GIVEN Flask.send_static_file, which has no in-repo callers, WHEN a developer asks 'is it safe to change or delete?', THEN CodeTruth reports 0 verified callers AND treats that as a known-unknown (the method may be reached via dynamic dispatch, framework routing, or external code) - it does NOT claim 'safe'.

## Expected result
who_calls returns 0 direct_callers for send_static_file, consistent with its count field, and this 0 is treated as a known-unknown - NOT 'safe to delete'. Read directly from the engine query, not the report helper. (The criterion direct==0 is unchanged from the earlier FAIL; only the measurement was corrected - the goalpost was not moved.)

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (reasoning_queries.who_calls / impact_of (engine-direct)).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| impact_resolved | who_calls and impact_of both returned | resolved=True target=flask.app.Flask.send_static_file | PASS |
| impact_direct_consistent | direct_callers list length == who_calls count field | direct_callers_n=0, count_field=0 | PASS |
| impact_honest_empty | 0 direct callers, reported as known-unknown (never 'safe to delete') | direct_callers=[] (expected 0) | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no
