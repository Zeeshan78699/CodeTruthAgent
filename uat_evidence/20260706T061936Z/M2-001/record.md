# UAT Acceptance Record - M2-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Validated

| Field | Value |
|---|---|
| Test ID | M2-001 |
| Objective | Module 2 alone builds a structural model: scans files and returns a governance gate and COMPLETE status (Python). |
| Requirement | Phase 3 - Module 2 Structural Intelligence. |
| Entry point | run_m2.run_module2 (language=python) |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T06:20:00.361900+00:00 |
| Finished (UTC) | 2026-07-06T06:20:02.773977+00:00 |
| Duration (s) | 2.41 |
| Checks passed | 3/3 |

## Scenario (what this test verifies)
GIVEN only Module 2 and a Python repository, WHEN the structural scan runs, THEN it parses files and returns a governance gate and a COMPLETE status.

## Expected result
status=COMPLETE; governance_gate set (not UNKNOWN); files_scanned>0. (Graph MAGNITUDES are informational - the runner return is thin by contract.)

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (run_m2.run_module2 (language=python)).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| m2_status_complete | status == COMPLETE | status=COMPLETE | PASS |
| m2_gate_present | governance_gate is set (not UNKNOWN) | gate=APPROVED | PASS |
| m2_files_scanned | files_scanned > 0 | files_scanned=83 | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no
