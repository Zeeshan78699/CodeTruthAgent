# Module 2 — Proof of Concept (POC) — Full Details

**CodeTruth Agent V3 — Module 2 — Repository Graph Engine**
**File**: `v3/repository_graph/poc/graph_engine_poc.py` (kept for historical
reference — NOT used in production; `graph_engine.py` is the real engine)

This document records exactly what the POC was, how it was tested, what it
found, and how those findings became D-001 through D-003 — the foundation
the production engine (`graph_engine.py`) was built on.

---

## 1. POC Scope (as stated in the file header)

```
CodeTruth Agent V3 - Module 2 Proof of Concept
Scope: function_graph (V3-004) + import_graph (V3-007) only
Approach: two-pass AST scan, adjacency-dict storage
```

Two graphs only (not all 6) — the goal was to validate the CORE APPROACH
(AST-based extraction + call resolution) on a small scale before building
the full 6-graph engine.

---

## 2. POC Architecture

### `Pass1SymbolCollector` (per file)
An `ast.NodeVisitor` that walks ONE file and records:
- Every `FunctionDef`/`AsyncFunctionDef`, with its qualified id
  (`module.ClassName.method_name` for methods, `module.func_name` for
  top-level), line number, and `scope` (the enclosing class name, or `None`)
- Every `ClassDef`, with its qualified id and line number

### `Pass2RelationshipResolver` (per file, using Pass 1's output)
A second `ast.NodeVisitor` over the SAME file that:
- Records `Import`/`ImportFrom` statements, splitting internal
  (`project_modules`) vs external via `_is_internal()`
- Records `Call` nodes — for `ast.Name` callees (`helper()`), checks
  `self._local_func_names` — **a set built ONLY from THIS FILE's
  Pass1 output**

### Orchestration (`build_repository_graph_poc`, implied by the two classes)
For each file: run Pass1, then run Pass2 using Pass1's output for THAT
SAME FILE. Repeat per file. No data is shared ACROSS files.

---

## 3. Test Case 1 — First Real-Repo Run

**Target**: `v3/repository_cognition/` (Module 1's own source — 5 files, 39
functions at the time)

**Result**: **402 unresolved items**.

**Analysis**: ~85% were EXPECTED noise — `.append()`, `.join()`, `.lower()`
etc. (method calls on local variables/strings — Pass2 has no concept of
variable types, so `Call` nodes with `ast.Attribute` callees were entirely
unhandled in this first POC pass). This ~85% became, much later, the
documented `attribute_call` category — not a bug, a known-from-day-1 scope
boundary.

**The remaining ~15% (~60 items) were real gaps** — this is where D-002 came
from:

1. **Missing builtins**: `round`, `any`, `next`, `iter` were flagged
   unresolved — they ARE Python builtins, just missing from the POC's
   builtin set.
2. **Same-module class constructor not resolved**:
   `RepositoryCognitionReport(...)` called from within
   `cognition_report.py` (the SAME FILE it's defined in) was flagged
   unresolved — Pass2 only checked `_local_func_names` (functions), never
   checked `local_classes` for constructor calls.
3. **External class constructors uncategorized**: `Path(...)` (from
   `pathlib`) and `defaultdict(...)` (from `collections`) were flagged as
   plain unresolved name calls, with no distinction from "genuinely
   missing" calls.

---

## 4. The Critical Finding — Why "Two-Pass" Wasn't Enough (→ D-001)

The POC's docstring says "two-pass AST scan" — and it IS two passes, but
**both passes run PER FILE**. Consider:

```python
# main.py
from pkg.utils import helper

def main():
    helper()   # <- Pass2 checks _local_func_names for main.py's Pass1
               #    output. helper is defined in pkg/utils.py, NOT main.py.
               #    -> "unresolved external call"
```

`helper` is a completely valid, resolvable project function — but Pass2 for
`main.py` only has Pass1's output FOR `main.py`. It has no way to know
`pkg.utils.helper` exists.

**This is the finding that produced D-001**: the "two-pass" design needed
to be re-scoped from "two passes PER FILE" to "two passes over the WHOLE
REPO" — Stage A (ALL files' symbol tables, combined into one global
table) → Stage B (ALL files' calls, resolved against the GLOBAL table).
This is the single most consequential POC finding — it's the architectural
basis for everything `graph_engine.py` does.

---

## 5. Test Case 2 — Multi-Repo Run (→ D-003)

**Target**: `repository_cognition/`, `repository_graph/` (the POC itself),
`core/`, `ai/` — 4 directories.

**Result on `repository_graph/`**: 19 occurrences of
`self.generic_visit(...)` flagged as `self_method_not_found` —
`generic_visit` is inherited from `ast.NodeVisitor` (stdlib), not defined
in any local class.

**Result on `ai/`**: 1 occurrence of `Exception(...)` — a builtin exception
type, missing from the builtins set (same category as Test Case 1's
`round`/`any`/`next`/`iter`, but for exception types specifically).

**Also in `ai/`**: 20 of 24 `name_call_unresolved` were dataclass-style
constructor names (`PipelineResult`, `FileNode`, `RiskDecision`) — NOT
investigated further at the time, since `ai/` was frozen V1/V2 code, out of
scope for Module 2. Documented as an open observation, not chased.

---

## 6. From POC Findings to Production Decisions

| POC Finding | Production Decision |
|---|---|
| Per-file Pass2 can't resolve cross-module calls | **D-001**: two-stage GLOBAL build (Stage A across all files, then Stage B) |
| Missing builtins (`round`, `any`, `next`, `iter`, `Exception`) | **D-002/D-003**: expanded `BUILTINS` set |
| Same-module class constructor unresolved | **D-002**: same-module class lookup added |
| `Path(...)`/`defaultdict(...)` uncategorized | **D-002**: new `external_constructor_call` category |
| `self.generic_visit(...)` unresolved (ast.NodeVisitor) | **D-003**: `STDLIB_INHERITED_METHODS` whitelist → `external_inherited_call` |
| ~85% noise = attribute calls on local vars | Documented as out-of-scope from the start; later partially addressed by Gap 2 (local-scope type tracking for literals/constructors only) |

The POC was NOT thrown away as "wrong" — its `Pass1SymbolCollector` logic
(qualified names, scope tracking) is structurally the ancestor of
`function_graph.py`/`class_graph.py`'s Stage A logic. What changed was the
ORCHESTRATION: Pass1+Pass2 per file → Stage A (all files) + Stage B (all
files), per D-001.

---

## 7. Status

`graph_engine_poc.py` is retained in `v3/repository_graph/poc/` for
historical reference — it documents the reasoning trail from "first AST
experiment" to "the validated 7-decision production engine." It is not
imported by, or part of, the production pipeline (`graph_engine.py` and its
6 graph modules), and is not covered by the 31-test suite.

---

*CodeTruth Agent V3 — Module 2 — Repository Graph Engine*
*github.com/Zeeshan78699/CodeTruthAgent*
