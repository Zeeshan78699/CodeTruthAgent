# UAT Acceptance Record - TRUTH-BOUNDARY-002

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | TRUTH-BOUNDARY-002 |
| Objective | truth_boundary scenario for flask |
| Requirement | Phase 5 - Product Front-Door: Truth Boundary (honest-empty case). |
| Entry point | v3.repository_reasoning.truth_boundary_demo.classify |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T12:21:51.304085+00:00 |
| Finished (UTC) | 2026-07-06T12:22:09.409470+00:00 |
| Duration (s) | 18.11 |
| Checks passed | 5/5 |

## Scenario (what this test verifies)
GIVEN the front-door demo on flask.app.Flask.send_static_file, WHEN it has 0 verified callers, THEN CodeTruth reports KNOWN-UNKNOWN (never 'safe to delete'); when it has callers, it reports them as verified edges - proving zero-guess behavior.

## Expected result
kind=truth_boundary; target=flask.app.Flask.send_static_file; verdict=KNOWN_UNKNOWN; direct_count=0; frozen before the run; identity/consistency-level checks.

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (v3.repository_reasoning.truth_boundary_demo.classify).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| tb_resolved | target resolved (verdict not NOT_FOUND) | verdict=KNOWN_UNKNOWN | PASS |
| tb_guesses_zero | guesses == 0 | guesses=0 | PASS |
| tb_never_asserts_safe | CodeTruth reading never asserts 'safe to delete' | 'safe to delete' asserted in CodeTruth reading? no | PASS |
| tb_verdict | verdict == KNOWN_UNKNOWN | verdict=KNOWN_UNKNOWN (expected KNOWN_UNKNOWN) | PASS |
| tb_direct_count | direct_count == 0 | direct_count=0 (expected 0) | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no
