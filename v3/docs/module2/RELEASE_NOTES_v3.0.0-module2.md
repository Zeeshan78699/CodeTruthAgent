# Release Notes — v3.0.0-module2

**CodeTruth Agent V3 — Module 2 — Repository Graph Engine**
**Status**: FROZEN (Python core, V3-004 through V3-009)
**Date**: 2026-06-14

---

## Summary

Module 2 maps how a Python codebase is wired together: every function,
class, module, import, dependency, and resolved function call, as 6
structured graphs. Validated on 69 real open-source repositories (49,379
files), 0 crashes, 1,005,321 resolved call edges, governance gate
APPROVED/BLOCKED consistent with Module 1.

This release also includes an early multi-language extension scaffold with
working first implementations for Java, JavaScript/TypeScript, and C/C++.

---

## What's New (Python Core)

- **D-001**: Two-stage global build (Stage A: per-file symbol collection;
  Stage B: global call resolution) - the architectural foundation for
  cross-module resolution.
- **D-002/D-003**: Expanded builtins, same-module class constructors,
  external constructors, stdlib-inherited-method whitelist
  (`ast.NodeVisitor`, `unittest.TestCase`).
- **D-004**: Cross-module class inheritance resolution -
  `self_method_not_found` cut 53% (495,783 -> 224,737).
- **Gap 1**: Qualified/dotted module call resolution (`pkg.utils.helper()`).
- **Gap 2**: Local variable type tracking for literals and constructors.
- **D-006**: Nested/recursive function call resolution.
- **Gap 3**: Import cycle detection (Tarjan SCC) via new `topology.py`.
- **Gap 4**: Module1<->Module2 file-count divergence audit.
- **D-007**: Relative import resolution (`from .models import X`).

Net effect: resolved calls increased from ~403,000 to 1,005,321 (2.5x)
across the 69-repo set.

---

## Known Limitations (Documented, By Design)

- `attribute_call` (1,785,190 instances): method calls on local variables
  whose type isn't statically tracked - requires full type inference, out
  of scope for Module 2's core.
- **D-008** (documented, not pursued): package-root/module-path mismatches
  in some large frameworks (e.g. `ccxt`) - requires per-repo package-root
  detection, a separate future investigation.

---

## New: Multi-Language Extension Scaffold (`v3/repository_graph/languages/`)

Extension-point architecture (mirrors Module 1's `framework_signatures.py`)
- adding a language = one adapter file + one registry entry, zero changes
to the frozen Python core.

| Language | Parser | Status |
|---|---|---|
| Python | `ast` | Mature (this release) |
| Java | `javalang` | Implemented, same-file resolution |
| JavaScript/TypeScript | `tree-sitter` | Implemented, incl. relative-import cross-file resolution |
| C/C++ | regex heuristic | Implemented, same-file resolution |
| Go, Rust | - | Registered stubs |

Validated on real repos with 0 crashes: Redis, u-boot, vscode,
ui5-webcomponents, react, elasticsearch, spring-boot.

This scaffold is NOT part of Module 2's original V3-004-009 specification -
it's an early head start for a future Multi-Language module.

---

## Test Results

- 31/31 unit tests pass (`test_module2_repository_graph.py`)
- 0 crashes across 69 repos / 49,379 files (Python core)
- 0 crashes across 69 repos for Java/JS/C++ adapters

---

## Files in This Release

`v3/repository_graph/` (8 core files + `languages/` package, 10 files),
`v3/repository_graph/tests/` (8 test files), `v3/docs/module2/` (9
documentation files, this set).

---

*CodeTruth Agent V3 — Module 2 — Repository Graph Engine*
*github.com/Zeeshan78699/CodeTruthAgent*
