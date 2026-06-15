# CodeTruth Agent V3 — Module 2
## Components and Capabilities

Module 2 provides deterministic repository connectivity understanding
through the following capabilities:

```
1. Function Graph (V3-004)
   - Discovers functions, methods, async functions, and nested functions.
   - Generates module-qualified identifiers.

2. Class Graph (V3-005)
   - Discovers classes and declared inheritance relationships.
   - Supports cross-module inheritance resolution (D-004).

3. Module Graph (V3-006)
   - Maps package and module structure.
   - Tracks parent/child relationships.

4. Import Graph (V3-007)
   - Tracks internal repository imports.
   - Supports relative import resolution (D-007).

5. Dependency Graph (V3-008)
   - Separates internal imports from external dependencies.
   - Aggregates dependency usage.

6. Call Graph (V3-009)
   - Resolves function and method call relationships.
   - Validated with 1,005,321 resolved calls.

7. Global Symbol Resolution
   - Two-stage build architecture (D-001).
   - Enables cross-module call resolution.

8. Constructor Resolution
   - Resolves local and external constructor calls.
   - Added through D-002.

9. Inheritance Resolution
   - Resolves methods through inheritance chains.
   - Supports cross-file inheritance traversal.

10. Nested Function Resolution
    - Resolves recursive and sibling nested functions.
    - Added through D-006.

11. Qualified Module Resolution
    - Resolves dotted-path calls
      (pkg.utils.helper()).

12. Basic Type-Aware Resolution
    - Handles selected literal and constructor cases.
    - Added through Gap 2.

13. Cycle Detection
    - Detects import/module cycles using Tarjan SCC.
    - Produces cyclic_clusters.

14. Honest Unresolved Logging
    - Never guesses.
    - Records unresolved calls explicitly, with file/line/reason.

15. Governance Validation
    - APPROVED/BLOCKED gate.
    - Correctly BLOCKED non-Python repositories.

16. Repository-Scale Graph Construction
    - Validated across 69 repositories.
    - 49,379 Python files.
    - 515,610 functions.
    - 84,468 classes.

17. Deterministic Processing
    - No LLM.
    - Same repository -> same graph.

18. Multi-Language Extension Architecture
    - Python mature.
    - Java implemented.
    - JavaScript/TypeScript implemented.
    - C/C++ implemented.
    - Go/Rust stubs.

19. Frozen Graph Contract
    - Produces a consistent 6-graph schema for downstream modules,
      shared across all language adapters.

20. Repository Connectivity Intelligence
    - Provides the data needed to answer:
      What calls this?
      What imports this?
      What inherits from this?
      What depends on this?
```

---

## Source of Validation Data

All figures above are drawn from the 69-repository validation run
recorded in `MODULE2_VALIDATION_SUMMARY.md` and
`MODULE2_FULL_SUMMARY.{json,csv,md}` — the same 69-repository set used for
Module 1's validation, for direct comparability.
