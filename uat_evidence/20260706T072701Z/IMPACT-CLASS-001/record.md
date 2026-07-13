# UAT Acceptance Record - IMPACT-CLASS-001

**Status:** FAIL  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | IMPACT-CLASS-001 |
| Objective | Safe Refactoring / Class Impact: before restructuring a class, show what in-repo code depends on its methods. |
| Requirement | Phase 5 - Engineering Scenario: Safe Refactoring (class impact). |
| Entry point | reasoning_queries.depends_on_class (engine-direct) |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T07:28:33.306843+00:00 |
| Finished (UTC) | 2026-07-06T07:28:49.802564+00:00 |
| Duration (s) | 16.50 |
| Checks passed | 4/5 |

## Scenario (what this test verifies)
GIVEN a developer about to refactor the Flask class, WHEN they ask 'what depends on this class?', THEN CodeTruth returns the in-repo callers of the class's methods (excluding the class's own methods), bounded to static/in-repo reach.

## Expected result
query=depends_on_class; target echoes flask.app.Flask; methods and external_dependents are lists; boundary present; and count>0 (a core class must have in-repo dependents). NOTE: this uses the QUALIFIED name after the bare 'Flask' returned 0 - a 0 HERE would confirm an index / target-format defect, not a passing test. Identity-level method checks will be added once a populated result is observed.

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (reasoning_queries.depends_on_class (engine-direct)).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| class_query | query == depends_on_class | query=depends_on_class | PASS |
| class_target_echoed | target echoes flask.app.Flask (qualified name) | target=flask.app.Flask (expected flask.app.Flask) | PASS |
| class_lists_present | methods and external_dependents are lists | methods_is_list=True(n=30), external_is_list=True(n=0) | PASS |
| class_boundary_stated | boundary note present (Truth Boundary) | boundary_present=True | PASS |
| class_has_dependents | a core class has >=1 in-repo dependent (count > 0) | count=0, methods_n=30, external_n=0 -> dependents NONE (investigate: qualified target or index gap) | FAIL |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** FAIL
- **Severity:** HIGH
- **Root cause:** Failed checks: class_has_dependents. See result.json for runner output.
- **Resolution:** Investigate runner output; re-run after fix.
- **Regression required:** yes
