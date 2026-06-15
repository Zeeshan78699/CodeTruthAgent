# Module 2 — Repository Graph Engine — Documentation

**CodeTruth Agent V3 — Module 2**
**Status**: FROZEN (core, V3-004 through V3-009)
**Package**: `v3/repository_graph/`

---

## 1. Purpose

Module 1 (Repository Cognition Engine) determines *what* a repository is —
its type, framework, languages, and file layout.

Module 2 (Repository Graph Engine) maps *how the code inside it is wired
together* — every function, class, module, import, dependency, and function
call, as a set of structural graphs. This is the "blueprint" that later V3
modules (impact analysis, reasoning, failure prediction) read from.

Module 2 consumes Module 1's `detected_languages` to know it's looking at a
Python codebase, then independently scans all `.py` files.

---

## 2. Architecture — Two-Stage Build

Module 2 builds 6 graphs in two stages, per decision **D-001**
(`MODULE2_DECISIONS.md`):

```
STAGE A (per file)              POST-STAGE-A          STAGE B (global)
─────────────────────           ────────────          ─────────────────
Parse each .py file once   →    Split raw imports  →  Resolve call_graph
  ├─ function_graph              into internal/        using the GLOBAL
  ├─ class_graph                 external using        symbol table built
  ├─ module_graph                project module         in Stage A
  └─ raw imports                 roots
                                  ├─ import_graph
                                  └─ dependency_graph
```

**Why two stages?** A function defined in `pkg/utils.py` and called from
`main.py` via `from pkg.utils import helper; helper()` cannot be resolved
by looking at `main.py` alone — the engine must first know about ALL
functions in the project (Stage A), then resolve calls against that full
table (Stage B).

---

## 3. Entry Point

```python
from v3.repository_graph.graph_engine import build_repository_graph

report = build_repository_graph(repo_root, cognition_report=None)
```

- `repo_root` (str): path to the repository root
- `cognition_report` (optional): Module 1's `RepositoryCognitionReport` —
  currently informational only; the engine is Python-only and self-discovers
  `.py` files regardless

Returns a single `dict` (see Section 5 for full schema).

---

## 4. The 6 Graphs

| Graph | Spec ID | Built In | Description |
|---|---|---|---|
| `function_graph` | V3-004 | Stage A | Every function/method definition, with module-qualified IDs and class scope |
| `class_graph` | V3-005 | Stage A | Every class definition, with declared base classes (as written, not resolved) |
| `module_graph` | V3-006 | Stage A | Package/directory structure — parent/child relationships, package flags |
| `import_graph` | V3-007 | Post-A | Internal (project-to-project) import statements only |
| `dependency_graph` | V3-008 | Post-A | External (stdlib/3rd-party) packages, aggregated with usage counts |
| `call_graph` | V3-009 | Stage B | Resolved function/method call edges, globally cross-referenced |

---

## 5. Output Schema

```python
{
  "repo_root": str,
  "files_scanned": int,
  "modules_parsed": int,
  "governance_gate": "APPROVED" | "BLOCKED",

  "function_graph": {
    "<module.name>": [
      {"id": str, "name": str, "lineno": int, "scope": str|None, "is_async": bool},
      ...
    ]
  },

  "class_graph": {
    "<module.name>": [
      {"id": str, "name": str, "lineno": int, "bases": [str, ...], "scope": str|None},
      ...
    ]
  },

  "module_graph": {
    "<module.name>": {"path": str, "parent": str|None, "is_package": bool}
  },

  "import_graph": {
    "<module.name>": [
      {"from_module": str, "imports": str, "type": "import"|"from_import",
       "relative_level": int, "lineno": int},
      ...
    ]
  },

  "dependency_graph": {
    "<package_root>": {"used_by": [str, ...], "import_count": int}
  },

  "declared_dependencies": {"<package_name>": "<version_spec_or_None>"},

  "call_graph": {
    "<module.name>": [
      {"caller": str, "callee": str, "lineno": int, "resolution": str},
      ...
    ]
  },

  "unresolved": [
    {"module": str, "lineno": int, "pattern": str, "note": str},
    ...
  ],

  "language_composition": {
    "<language>": {"file_count": int, "implemented": bool},
    ...
    "_other_extensions": {"<ext>": int, ...}
  }
}
```

---

## 6. call_graph Resolution Categories

| `resolution` value | Meaning | Added |
|---|---|---|
| `direct_name_call` | Function call within the same module (`helper()`) | initial |
| `same_class_name_call` | `self.method()` resolved to a method in the current class | initial |
| `same_module_class_call` | Call to a class defined in the same module (incl. constructor calls) | D-002 |
| `imported_call` | Cross-module call, resolved via the global symbol table (D-001) | initial |
| `external_constructor_call` | Call to a stdlib/3rd-party class constructor (e.g. `Path(...)`) | D-002 |
| `external_inherited_call` | `self.method()` resolved to a known stdlib base-class method (e.g. `generic_visit`) | D-003 |
| `inherited_method_call` | `self.method()` resolved via cross-module class inheritance (D-004) | D-004 |
| `qualified_module_call` | Dotted-path call (`pkg.utils.helper()`) resolved via global index | Gap 1 |
| `local_builtin_method_call` | Method call on a local var of known builtin type (`items.append()`) | Gap 2 |
| `local_typed_method_call` | Method call on a local var of a known local/imported class | Gap 2 |
| `nested_function_call` | Call to a sibling nested function (recursive helpers) | D-006 |

D-007 (relative import resolution) does not add a new category - it makes
`imported_call` and `inherited_method_call` resolve correctly for modules
that use relative imports (`from .models import X`), which previously fell
through to unresolved.

---

## 7. `unresolved` — Honest Gap Log

Per the extension-point pattern (same philosophy as Module 1's
`framework_signatures.py`), anything the engine cannot resolve is logged,
not hidden or guessed. Current `pattern` values:

| `pattern` | Meaning | Status |
|---|---|---|
| `parse_error` | File has a Python syntax error; skipped, engine continues | Expected — files are sometimes invalid |
| `attribute_call` | Method call on a local variable whose type isn't tracked (e.g. `lines.append(x)`) | **Known limitation** — requires variable type tracking (out of scope, see Section 8) |
| `name_call_unresolved` | Call to a name not found in local/imported/builtin symbols | Rare after D-002/D-003; usually a callable passed as a parameter |
| `self_method_not_found` | `self.method()` not found in class or known stdlib bases | Rare after D-003; may indicate multi-level custom inheritance not yet cross-referenced |

---

## 8. Known Limitations (By Design)

### 8.1 Variable Type Tracking (not implemented)

The largest source of `unresolved` items is `attribute_call` — calls like
`name.lower()` or `items.append(x)` where `name`/`items` are local
variables. Resolving these requires inferring variable types from
assignments (`items = []` → `list`), which is a substantially larger
feature than Module 2's scope. **Candidate for a future module** (Module 2.5
or the Reasoning Engine's type-inference layer).

### 8.2 Multi-level / Cross-file Inheritance (resolved - D-004)

`class_graph` records declared base classes as written (e.g. `"Base"` or
`"ast.NodeVisitor"`). D-004 added `build_resolved_bases()` and
`_find_method_in_hierarchy()`, which resolve these bases to actual
(module, class) pairs - including across files and through relative
imports (D-007) - and walk the inheritance chain (cycle-safe) for
`self.method()` resolution. Resolution order: own class -> resolved
inheritance chain (D-004) -> stdlib whitelist (D-003, for any base D-004
couldn't resolve) -> unresolved. On the 69-repo set, this cut
`self_method_not_found` by ~53% (495,783 -> 224,737).

### 8.3 Package-Root Mismatch (D-008, documented, not pursued)

Some large frameworks (e.g. `ccxt`) have their importable package root in a
SUBDIRECTORY of the cloned repo (e.g. `ccxt/python/ccxt/`), while
`module_name_from_path` computes module names relative to the repo root -
producing names that never match the absolute import paths used in the
code. This requires per-repo package-root detection, a larger investigation
than D-007. Open item for a future module.

### 8.3 Dynamic Dispatch

Calls via `getattr(obj, name)()`, decorators that wrap call targets, or
calls through variables holding function references are not resolved —
correctly logged as `attribute_call` or left as the variable's value.

---

## 9. Deferred Sub-modules

Per the frozen project structure, these `repository_graph/` files are
**not** part of Module 2's core build:

- `async_flow_analyzer.py` — event loop / async dependency tracking
- `graph_cache_registry.py` — serialized graph snapshot caching
- `incremental_graph_manager.py` — incremental rebuild of changed AST branches

These remain candidates for a future sub-module once the core 6 graphs are
in active use by downstream modules.

---

## 10. Validation

69 real repositories, 49,379 Python files, 0 crashes, governance APPROVED
on all 65 Python repos (4 non-Python repos correctly BLOCKED). 1,005,321
resolved calls (up from ~403,000 before D-004-007, a 2.5x improvement).
31/31 unit tests pass (`test_module2_repository_graph.py`). Full numbers
and per-repo breakdown: see `MODULE2_VALIDATION_SUMMARY.md`.

---

## 11. Multi-Language Extension Scaffold (v3/repository_graph/languages/)

A new package, `languages/`, provides an extension-point architecture for
non-Python languages - mirroring Module 1's `framework_signatures.py`
philosophy: adding a language = one new adapter file + one registry entry,
with **zero changes** to this module's frozen Python core.

| Language | Parser | Status |
|---|---|---|
| Python | `ast` (stdlib) | Mature - this document |
| Java | `javalang` | Implemented (same-file resolution) |
| JavaScript/TypeScript | `tree-sitter` | Implemented (incl. relative-import cross-file resolution) |
| C/C++ | regex heuristic | Implemented (same-file resolution) |
| Go, Rust | - | Registered stubs (file-counted, not parsed) |

`build_repository_graph()` gained one additive field, `language_composition`
(per-language file counts, wrapped in try/except - cannot affect the core
6-graph output). Each implemented adapter returns the same 6-graph shape as
Python, validated on real repos (Redis, u-boot, vscode, ui5-webcomponents,
react, elasticsearch, spring-boot - 0 crashes across all). This scaffold is
considered a head start for a future "Multi-Language" module, not part of
Module 2's original V3-004-009 spec.

---

*CodeTruth Agent V3 — Module 2 — Repository Graph Engine*
*github.com/Zeeshan78699/CodeTruthAgent*
