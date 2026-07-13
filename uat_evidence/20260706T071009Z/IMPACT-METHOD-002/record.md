# UAT Acceptance Record - IMPACT-METHOD-002

**Status:** FAIL  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | IMPACT-METHOD-002 |
| Objective | Change Impact (honest-empty boundary): a method with 0 verified callers is reported as a known-unknown - never as 'safe to delete'. |
| Requirement | Phase 5 - Engineering Scenario: Change Impact (Truth Boundary). |
| Entry point | codetruth_report._impact (RQ who-calls / impact-of) |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T07:10:53.141378+00:00 |
| Finished (UTC) | 2026-07-06T07:11:06.264353+00:00 |
| Duration (s) | 13.12 |
| Checks passed | 2/3 |

## Scenario (what this test verifies)
GIVEN Flask.send_static_file, which has no in-repo callers, WHEN a developer asks 'is it safe to change or delete?', THEN CodeTruth reports 0 verified callers AND treats that as a known-unknown (the method may be reached via dynamic dispatch, framework routing, or external code) - it does NOT claim 'safe'.

## Expected result
result resolves without error; impact well-formed; direct == 0. This is the sharpest integrity test: '0 verified callers' is a known-unknown, not a safe-to-delete verdict. A non-zero result would mean this is not the empty case (spec target needs review), not a tool fault.

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (codetruth_report._impact (RQ who-calls / impact-of)).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| impact_target_resolved | target found in call index (result is not None) | resolved=True target=flask.app.Flask.send_static_file | PASS |
| impact_wellformed | impact = {int direct, int transitive, list sample} | direct=5, transitive=6, sample_n=5 | PASS |
| impact_honest_empty | direct == 0, reported as a known-unknown (never 'safe to delete') | direct=5 (0 verified callers = KNOWN-UNKNOWN, not 'safe to delete') | FAIL |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** FAIL
- **Severity:** HIGH
- **Root cause:** Failed checks: impact_honest_empty. See result.json for runner output.
- **Resolution:** Investigate runner output; re-run after fix.
- **Regression required:** yes
