# UAT Acceptance Record - SMOKE-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | SMOKE-001 |
| Objective | Full platform runs M1 -> gate -> M2 -> M3 as one governed pass from the single canonical path, producing a structured report with zero fabrications. |
| Requirement | Phase 1 - Platform Integration (one-scan governed pipeline). |
| Entry point | run_codetruth.run_platform |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T06:19:36.947063+00:00 |
| Finished (UTC) | 2026-07-06T06:19:58.678922+00:00 |
| Duration (s) | 21.73 |
| Checks passed | 5/5 |

## Scenario (what this test verifies)
GIVEN the full CodeTruth platform and a real repository, WHEN it is run in one governed pass (M1 -> gate -> M2 -> M3), THEN the pipeline completes end-to-end, the gate is a real decision, structure is scanned, and reasoning fabricates nothing.

## Expected result
status=COMPLETE; gate in {APPROVED, REVIEW_REQUIRED}; M1 emits an identity; M2 scans >=1 file; M3 guesses=0.

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (run_codetruth.run_platform).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| pipeline_completed | status == COMPLETE | status=COMPLETE | PASS |
| gate_not_blocking | gate in {APPROVED, REVIEW_REQUIRED} | gate=APPROVED | PASS |
| m1_produced_identity | module1 has non-empty application_type and framework | application_type=WEB_APPLICATION, framework=Flask, arch=LIBRARY | PASS |
| m2_scanned_structure | module2.files_scanned > 0 | files_scanned=83, functions=1460, edges=686 | PASS |
| m3_zero_guesses | module3.truth_boundary.guesses == 0 (Python); honest note otherwise | guesses=0 | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no
