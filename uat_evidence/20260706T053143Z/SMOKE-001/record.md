# UAT Acceptance Record - SMOKE-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | SMOKE-001 |
| Objective | Full platform runs M1 -> gate -> M2 -> M3 as one governed pass from the single canonical path, producing a structured report with zero fabrications. |
| Requirement | Phase 1 - Platform Integration (one-scan governed pipeline). |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T05:31:43.310719+00:00 |
| Finished (UTC) | 2026-07-06T05:32:05.462635+00:00 |
| Duration (s) | 22.15 |
| Checks passed | 5/5 |

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the validated platform pipeline.
2. Run run_codetruth.run_platform(repo) - one governed M1->M2->M3 pass.
3. Score the returned report against the pre-registered checks.
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
- `result.json` - raw platform output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no
