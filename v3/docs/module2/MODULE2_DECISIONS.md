# Module 2 — Design Decisions Log

## D-001: Project-wide symbol table required BEFORE call resolution

**Date**: 2026-06-13
**Status**: Confirmed (via proof-of-concept)

**Context**:
Initial proof-of-concept attempted per-file call resolution — for each file,
build local symbol table (Pass 1), then resolve calls within that same file (Pass 2).

**Problem found**:
Cross-module calls cannot be resolved this way. Example:
```python
# main.py
from pkg.utils import helper

def main():
    helper()   # <- logged as "unresolved external call"
```
`helper` is a valid project function (`pkg.utils.helper`), but per-file Pass 1
only knows about symbols defined IN `main.py`, not symbols imported INTO it
from elsewhere in the project.

**Decision**:
Module 2's real build will use a two-stage approach across the WHOLE repo,
not per-file:

1. **Stage A — Global Symbol Table Pass**: scan ALL files first, build one
   project-wide table of {module: [functions, classes]} (this is essentially
   today's function_graph + class_graph, combined).
2. **Stage B — Global Call Resolution Pass**: scan ALL files again for calls,
   resolving each call against the GLOBAL symbol table (not just local).
   This correctly resolves imported-function calls, e.g. `helper()` after
   `from pkg.utils import helper` → `pkg.utils.helper`.

**Reason**:
Per-file resolution is structurally insufficient for any project with more
than one file that calls across modules — which is effectively all real
repos. The "two-pass" in the original plan should be understood as
"two passes over the WHOLE repo," not "two passes per file."

**Impact**:
- import_graph/dependency_graph (file-local import statements) can still be
  built per-file — no change needed there.
- function_graph/class_graph (Stage A) — no change, already global-friendly.
- call_graph (Stage B) — engine must run AFTER Stage A completes for ALL
  files, not interleaved per-file.

**Status of unresolved items**:
Remaining unresolved patterns (attribute calls on instances, e.g. `g.greet()`,
and builtin calls like `print()`) are NOT fixed by this decision — those are
separate, smaller resolution-rule additions for `resolution_rules.py`.

## D-002: Builtins list expansion + same-module/external class constructor resolution

**Date**: 2026-06-13
**Status**: Confirmed (via real-repo test on repository_cognition/, 5 files, 39 functions)

**Context**:
First real-repo run of graph_engine.py produced 402 unresolved items.
~85% were expected noise (.append(), .join(), .lower() etc - method calls on
local variables/strings, not yet type-tracked - by design, not a bug).

**Problems found** (~15% of unresolved, real gaps):

1. Missing builtins: `round`, `any`, `next`, `iter` flagged as unresolved -
   these ARE Python builtins, just missing from call_graph.BUILTINS set.

2. Same-module class constructor not resolved: `RepositoryCognitionReport(...)`
   called from within cognition_report.py (same file it's defined in) was
   flagged unresolved. CallResolver only checked (a) same-class self-calls
   and (b) cross-module imports - missed "another class in THIS module."

3. External class constructors not categorized: `Path(...)` (from
   `from pathlib import Path`) and `defaultdict(...)` (from
   `from collections import defaultdict`) flagged as unresolved name calls.
   pathlib/collections are stdlib (external), so global_class_methods has
   no entry for them - falls through to unresolved instead of being
   recognized as "external constructor call."

**Decision**:
- Expand BUILTINS set to cover full commonly-used builtin function list.
- Add same-module class lookup: if a Name call matches a class defined in
  the SAME module, resolve to its __init__ (or "<module>.<ClassName>.<class>"
  if no __init__).
- Add new resolution category "external_constructor_call": if a Name call
  matches an import_alias_map entry whose target's module root is NOT a
  project module, classify as external_constructor_call instead of
  unresolved (still informational, not a graph edge to an unknown node).

**Impact**: Expected to reduce unresolved count from 402 to roughly <50 on
this same repo, with remainder being legitimate "method call on untyped
local variable" cases (future: variable type tracking, out of Module 2 scope).

## D-003: Builtin exceptions + stdlib-inherited-method whitelist

**Date**: 2026-06-13
**Status**: Confirmed (via multi-repo run: repository_cognition, repository_graph, core, ai)

**Context**:
Multi-repo validation surfaced two recurring unresolved patterns:
1. `self.generic_visit(...)` - 19 occurrences across repository_graph/ -
   ast.NodeVisitor's inherited method, not found in any local class.
2. `Exception(...)` - 1 occurrence (ai/ai_interface.py) - builtin exception
   type missing from BUILTINS.

**Decision**:
- Added builtin exception types (Exception, ValueError, TypeError, KeyError,
  etc.) to BUILTINS.
- Added STDLIB_INHERITED_METHODS whitelist (generic_visit, visit, dunder
  methods like __repr__/__iter__/etc.) - if self.X() isn't found locally,
  X is in this whitelist, AND the current class has at least one base class,
  resolve as "external_inherited_call" (informational - names the base
  class(es) as written, not a graph edge to an unknown node) instead of
  unresolved.

**Result on repository_graph/**: self_method_not_found 19 -> 0.

**Remaining `ai/` findings** (20 of 24 name_call_unresolved - dataclass-style
constructor names like PipelineResult, FileNode, RiskDecision):
NOT investigated further - `ai/` is frozen V1/V2 code, out of scope for
Module 2 changes. Documented as an open observation for future modules if
relevant, not chased here.

**Remaining unresolved is now exclusively `attribute_call`** (method calls
on untyped local variables - see D-002's "Known Limitation" note;
variable type tracking remains out of scope for Module 2's first freeze).

## D-004: Cross-module class inheritance resolution

**Date**: 2026-06-13
**Status**: Implemented

**Context**: 69-repo validation showed `self_method_not_found` = 495,783
(larger than `name_call_unresolved`'s 181,303). D-003's whitelist only
covered known stdlib base classes (e.g. ast.NodeVisitor); it did NOT resolve
`self.method()` when `method` is defined in a CUSTOM parent class, often in
a DIFFERENT file (e.g. `class MyModel(BaseModel)` where `BaseModel.save()`
lives in another module).

**Decision**: Added `build_resolved_bases()` - resolves each class's declared
`bases` (from class_graph) to (module, class_name) pairs via same-module
lookup or import_alias_map. Added `_find_method_in_hierarchy()` - recursive,
cycle-safe walk of resolved bases (cross-module) to find inherited methods.
`self.method()` resolution order is now: own class -> resolved inheritance
chain (D-004) -> D-003 stdlib whitelist (using only bases D-004 could NOT
resolve) -> unresolved.

## Gap 1: Qualified module call resolution

**Status**: Implemented

**Context**: Calls like `pkg.utils.helper()` (after `import pkg.utils`) or
`utils.helper()` (after `from pkg import utils`) were previously logged as
`attribute_call` - Stage B only resolved single-name imports, not dotted
attribute chains.

**Decision**: Added `_flatten_attribute()` (flattens an Attribute chain to
root+parts) and `_resolve_dotted_path()` (tries module/symbol split points
against global function/class indices, including one-level Class.method).
New resolution category: `qualified_module_call`.

## Gap 2: Non-predictive local-scope type tracking

**Status**: Implemented

**Context**: The dominant `attribute_call` source is local variables of
known literal type, e.g. `items = []` then `items.append(x)`.

**Decision**: Added per-function-scope type tracking via `visit_Assign`.
Tracks: list/dict/set literals and comprehensions -> `("builtin", type)`;
single-Name constructor calls to known local/imported classes ->
`("class", module, classname)`. On attribute-call with a single-level
target (`x.method()`), checks this scope map. New resolution categories:
`local_builtin_method_call` (e.g. `<builtin>.list.append`),
`local_typed_method_call` (resolves to actual method, using D-004 hierarchy
if needed). Explicitly non-predictive: reassignment overwrites binding,
no control-flow/branch modeling, no cross-function inference.

## D-005: Expand STDLIB_INHERITED_METHODS for unittest.TestCase

**Status**: Implemented

**Context**: After D-004, testing against Module 2's OWN test suite
(test_module2_repository_graph.py, a NEW file added this session) showed
45 `self_method_not_found` - all `self.assertEqual/assertIn/...` from
`unittest.TestCase`, which D-003's whitelist (built for ast.NodeVisitor)
didn't cover.

**Decision**: Added unittest.TestCase's assert*/setUp/tearDown/fail/skipTest
methods to STDLIB_INHERITED_METHODS. Result: self_method_not_found 45 -> 0
on repository_graph/.

## D-006: Nested/recursive function call resolution

**Status**: Implemented

**Context**: `local_func_index` only includes top-level (scope=None)
functions. Recursive calls to NESTED functions (e.g. Tarjan's `strongconnect`
helper inside `find_cycles`, calling itself) were logged as
`name_call_unresolved`.

**Decision**: Added `nested_func_index: {module: {(scope, name): full_id}}`
covering ALL functions (incl. nested). `_resolve_nested_func_call()` walks
the current scope chain outward looking for a matching nested function.
New resolution category: `nested_function_call`.

## Gap 3: Topology cycle detection (Tarjan SCC)

**Status**: Implemented as separate module `topology.py`

**Context**: Hidden import cycles (A imports B, B imports A) could trap
naive downstream graph traversals in infinite loops.

**Decision**: New module `topology.py` - `find_cycles()` runs Tarjan's SCC
over import_graph's internal edges; `annotate_module_graph()` adds
`in_cyclic_loop`/`cyclic_cluster_id` fields to module_graph entries.
Does NOT modify any of the 6 core graphs' edges - informational annotation
only. New report field: `cyclic_clusters`.

## Gap 4: Divergence audit (Module 1 <-> Module 2 file-count check)

**Status**: Implemented as `tests/verify_pipeline_integrity.py`

**Context**: Ensure no Python files are silently dropped between Module 1's
discovery and Module 2's scan.

**Decision**: Standalone script comparing Module 1's FULL_DOMAIN_SUMMARY
total_python_files per repo against Module 2's MODULE2_FULL_SUMMARY
files_scanned. Reports matches/mismatches/repos-only-in-one-summary.
Schema-tolerant (handles list or dict JSON, multiple possible field names) -
gracefully skips if Module 1 summary absent or schema unrecognized.

## Net Effect on repository_graph/ (14 files, incl. new files added this
session: topology.py, verify_pipeline_integrity.py, test_module2_repository_graph.py)

| Metric | Before (D-003 baseline) | After D-004/005/006 + Gap1/2 |
|---|---|---|
| self_method_not_found | 0 (no custom inheritance in old fileset) | 0 |
| name_call_unresolved | 0 | 0 |
| attribute_call | 203 | 254 (file count grew 12->14) |
| resolved_pct | 21.0% | 44.0% |
| new categories | - | qualified_module_call, local_builtin_method_call, local_typed_method_call, inherited_method_call, nested_function_call |

31/31 unit tests pass (test_module2_repository_graph.py).

## D-007: Relative import resolution

**Date**: 2026-06-13
**Status**: Implemented

**Context**: 69-repo results after D-004/005/006 showed `self_method_not_found`
roughly halved (495,783 -> 230,412) but `name_call_unresolved` barely moved
(181,303 -> 176,353), with both still concentrated in large frameworks using
heavy relative imports: ccxt (105,494 self_method_not_found), odoo (39,543),
transformers (31,097 / 16,339), qiskit (29,623 name_call_unresolved),
pennylane (24,846), django (19,620 / 13,138).

Root cause: `build_import_alias_map` ignored `relative_level` -
`from .models import PipelineResult` or `from ..base import BaseModel`
produced alias targets like "models.PipelineResult" (missing the actual
package prefix), which never matched the global symbol tables (keyed by
full absolute module paths).

**Decision**: 
- `import_graph.py`: ImportCollector now additionally records `module_part`
  (text after dots) and `symbol_part` (imported name) per from-import entry.
- `call_graph.build_import_alias_map(module_name, raw_imports, is_package)`:
  for entries with `relative_level > 0`, computes the importing module's own
  package path (using `is_package` from module_graph - packages use their
  own dotted path, regular modules use their parent), walks up
  `(level - 1)` additional package levels, and concatenates with
  `module_part` + `symbol_part` to produce an ABSOLUTE target path.
- `graph_engine.py`: passes `is_package` (from module_graph) when building
  each module's import_alias_map.

D-004's inheritance resolution and Gap1's qualified-call resolution both
consume `import_alias_map`, so they benefit automatically - no changes
needed there.

**Verified** on a synthetic 4-file package mirroring the real-world pattern
(`from ..base import BaseModel` for inheritance + `from .models import
PipelineResult` for constructor calls): 0 unresolved, both patterns resolve
correctly (`inherited_method_call`, `imported_call`).

31/31 unit tests still pass.

**Expected impact on 69-repo numbers**: significant further reduction in
both `self_method_not_found` and `name_call_unresolved`, concentrated in
django/transformers/qiskit/pennylane/odoo/ccxt - re-run
scan_all_repos_module2.py to measure.
