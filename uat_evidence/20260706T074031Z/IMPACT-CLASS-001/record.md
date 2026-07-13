# UAT Acceptance Record - IMPACT-CLASS-001

**Status:** PASS  
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
| Started (UTC) | 2026-07-06T07:41:39.059348+00:00 |
| Finished (UTC) | 2026-07-06T07:41:52.042449+00:00 |
| Duration (s) | 12.98 |
| Checks passed | 5/5 |

## Scenario (what this test verifies)
GIVEN a developer about to refactor the Flask class, WHEN they ask 'what depends on this class?', THEN CodeTruth returns the in-repo callers of the class's methods (excluding the class's own methods), bounded to static/in-repo reach - and reports 0 external dependents honestly when the only callers are internal or dynamically-typed (never fabricating a dependency).

## Expected result
query=depends_on_class; target echoes flask.app.Flask (qualified name resolves - 30 methods found); methods and external_dependents are lists; boundary present; count == number of external_dependents. For flask this is 0 external dependents - VERIFIED HONEST via diag_depends_on_class.py: the reference who_calls aggregation also yields 0 (every resolved caller is a Flask-own method, excluded; external test-callers use dynamic receivers, correctly unresolved). count>0 was a wrong earlier expectation and was removed.

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
| class_target_echoed | target echoes flask.app.Flask (qualified name resolves) | target=flask.app.Flask (expected flask.app.Flask) | PASS |
| class_lists_present | methods and external_dependents are lists | methods_is_list=True(n=30), external_is_list=True(n=0) | PASS |
| class_boundary_stated | boundary note present (Truth Boundary) | boundary_present=True | PASS |
| class_count_consistent | count == number of external_dependents returned | count=0, external_dependents_n=0 | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no
