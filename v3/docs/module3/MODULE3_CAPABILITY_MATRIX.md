# CodeTruth V3 — Module 3 Capability Matrix

**Date:** 2026-07-10
**Standard:** Implementation status and validation status are tracked separately.
No capability is claimed without empirical evidence from a real repository.

---

## Reading This Document

| Column | Means |
|---|---|
| **Implemented** | Code exists and imports |
| **Pipeline-validated** | Ran through `run_codetruth.py` on a real repository and produced artifacts |
| **Depth** | How much reasoning the engine performs, relative to Python |

A ✅ in *Implemented* and a ⚠️ in *Pipeline-validated* means the code runs but has
not been demonstrated end-to-end. That distinction is load-bearing: on 2026-07-09
three Module 2 adapters (Java, JavaScript, C/C++) were marked "Available" while
being unreachable from the pipeline — `get_adapter()` returned `PythonAdapter`
for all three. They produced nothing for weeks. Availability is not reachability.

---

## Reasoning Engine Dispatch

| Language | Engine | Implemented | Pipeline-validated | Evidence |
|---|---|---|---|---|
| Python | frozen M3 (Phase 3A/3B) | ✅ | ✅ | flask · `guesses: 0` · edge provenance exact |
| Java | `bridge.answer` | ✅ | ✅ | elasticsearch · 30,291-function index |
| JavaScript | `bridge.answer` | ✅ | ✅ | react · COMPLETE |
| C/C++ | `bridge.answer` | ✅ | ✅ | nginx · 401 files · COMPLETE |
| Go | `bridge.advanced_reparsed` | ✅ | ✅ | Go compiler · 33,428-function index |
| C# | `bridge.advanced_reparsed` | ✅ | ✅ | ccxt/cs · 8,493-function index |
| SQL | `bridge.sql_lineage` | ✅ | ✅ | camel · 2 reads / 2 writes / 1 data_flow |
| Rust | — | ⚠️ Declared stub | ✅ (honest refusal) | 36,176 files · `NOT_IMPLEMENTED` · zero capabilities |

**Eight languages route. Seven reason. One refuses honestly.**

---

## Reasoning Depth — Not Equal

Depth differs by language and must never be flattened into a single claim.

| Tier | Languages | What the engine performs |
|---|---|---|
| **Full resolution** | Python | Phase 3A attribute-call resolution · C3 MRO · `super()` chains · local/imported receiver typing · edge provenance · guess counting |
| **Call graph + queries** | Java, JavaScript, C/C++ | Directed call graph · who-calls · impact · dead-code · depends-on-class |
| **Caller-recovery re-parse** | Go, C# | Module 2's adapter records callees **without** enclosing callers, so Module 3 re-parses source to recover them. Same query surface, heuristic parse. |
| **Data lineage** | SQL | Reads/writes attributed to enclosing objects. A data-flow model, not a call graph. Regex + scope heuristic, no SQL grammar. |
| **None** | Rust | Adapter is a declared stub. `scan()` returns an empty report. |

### Why Go and C# need a re-parse

The frozen Go and C# adapters in Module 2 emit call records **without the
enclosing function**. A directed `{caller → callee}` edge cannot be built from
that output. Measured in the live pipeline:

```
go     — Module 2:  11,437 files scanned →      0 functions,  0 edges
       — Module 3:  caller-aware re-parse → 33,428 functions

csharp — Module 2:                         →      0 functions
       — Module 3:  caller-aware re-parse →  8,493 functions
```

This is a **Module 2 limitation worked around additively in Module 3**, not a
Module 3 feature. The root fix belongs in the adapters and would require a
freeze break.

---

## Confidence Tiers

| Tier | Languages | Basis |
|---|---|---|
| **Multi-repo UAT + frozen** | Python | 76-repo corpus, full Phase 3A/3B validation |
| **Demonstrated on one real repository** | Java, JavaScript, C/C++, Go, C# | Single production codebase each |
| **Demonstrated, heuristic engine** | SQL | Regex + scope; adapter declares its own limits |
| **Declared stub** | Rust | Refuses, claims nothing |

**Java, JavaScript, C/C++, Go, and C# have not received multi-repo UAT.**
Each is proven on one real codebase. That is real evidence and a real limit.

---

## The Common Envelope

Every non-Python language emits the same structure. No language borrows
Python's vocabulary.

```json
{
  "language": "java",
  "engine": "bridge.answer",
  "status": "COMPLETE",
  "capabilities": ["call_graph", "who_calls", "impact", "dead_code", "depends_on_class"],
  "truth_boundary": {
    "scope": "Java structural reasoning over the verified call graph",
    "limitations": ["reflection", "runtime bytecode generation", "dynamic proxies",
                    "cross-file calls not type-resolvable", "annotation-driven invocation"]
  },
  "graph": {"functions_in_index": 30291, "callers_in_index": 12044}
}
```

**`truth_boundary.guesses` and `edge_provenance` appear only under Python.**
They are Phase 3A/3B *measurements*. Emitting `guesses: 0` for Java would assert
a guarantee that engine never computed. The envelope makes that impossible by
construction.

### Envelope failure modes

| Status | When | Capabilities |
|---|---|---|
| `COMPLETE` | Engine ran, produced a graph or lineage | listed |
| `ENGINE_ERROR` | Engine exists, could not complete on this repository | **`[]`** |
| `NOT_IMPLEMENTED` | No engine for this language (rust) | **`[]`** |

An invariant enforces the last two: a module3 block reporting `ENGINE_ERROR` or
`NOT_IMPLEMENTED` **must** claim zero capabilities. Verified on real data —
rust exercises it in every corpus run.

---

## Per-Language Truth Boundaries

Declared by the engine itself, not by this document.

| Language | Cannot see |
|---|---|
| Python | dynamic dispatch · `getattr` chains · decorator/framework invocation · external callers |
| Java | reflection · runtime bytecode generation · dynamic proxies · annotation-driven invocation |
| JavaScript | dynamic dispatch · `eval` / dynamic import · prototype mutation · framework-injected callbacks |
| C/C++ | function pointers · preprocessor-conditional code · template instantiation · linker-resolved symbols |
| Go | cross-package calls · interface dispatch · struct embedding · generics · brace-heuristic parse (no Go AST) |
| C# | overloads · inheritance · partial classes · generics · interface dispatch · regex + brace heuristic (no C# AST) |
| SQL | dynamic SQL (`EXECUTE IMMEDIATE`) · CTEs · dialect-specific constructs · regex + scope heuristic (no SQL grammar) |

---

## Not Claimed

- **Multi-repo UAT for any non-Python language.** One repository each.
- **Deep resolution outside Python.** No attribute resolution, no MRO, no
  `super()` chains, no edge provenance, no guess counting.
- **Rust reasoning.** Stub. Registers `.rs` files so they are counted, refuses to analyze.
- **Complete caller sets.** Every result is a verified in-repo **floor**.
  External, dynamic, decorator-, and framework-invoked callers are outside the graph.
- **Runtime behavior.** Module 3 reads structure. It does not execute code.

---

## Known Limitations

| Limitation | Measured |
|---|---|
| **Near-parity language routing is unreliable** | PyTorch: 4,733 C/C++ vs 4,609 Python files — a **1.3% margin** decides between a 143,436-function Python analysis and a 17,625-function C/C++ one. All 74 corpus repositories have decisive margins. |
| **C/C++ under-extraction** | nginx: 401 files → 15 functions. The bridge engine finds more. Cause not yet investigated. |
| **javalang recursion limit** | elasticsearch (22,101 Java files) exceeds Python's default recursion cap and aborts the scan. Mitigated by a scoped pipeline-level guard (`_deep_recursion(20000)`, always restored). **Not fixed at source.** A pathological file could still exhaust the C stack. |
| **Go/C# require re-parse** | Duplicated parsing work: Go's 11,437 files are read by Module 2 (producing nothing usable) and again by Module 3. |

---

## Truth Boundary Statement

```
Claimed only:
  What has been measured in the live pipeline on real repositories.

Not claimed:
  Capabilities implemented but not exercised end-to-end.
  Depth equivalence between Python and any other language.
  Complete caller sets for any language.

Tracked separately:
  Implemented         — code exists and imports
  Pipeline-validated  — ran and produced artifacts
  Depth               — what the engine actually performs
```

---

*CodeTruth Agent V3 — github.com/Zeeshan78699/CodeTruthAgent*
*AI imagines. CodeTruth checks. Nature tests. Humans decide.*
