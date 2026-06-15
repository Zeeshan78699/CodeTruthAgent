# Module 2 — Gaps & Roadmap

**CodeTruth Agent V3 — Module 2 — Repository Graph Engine**

This document consolidates every known gap discovered during Module 2's
development and validation, with an honest assessment of what it would
take to close each one. Nothing here blocks the current freeze - these are
documented future-work items, in the same spirit as Module 1's "No
Framework Detected" honesty.

---

## Gap 1: `attribute_call` — Variable Type Tracking (Python core)

**Size**: 1,785,190 instances across 69 repos — the single largest
unresolved category.

**What it is**: method calls on local variables whose type isn't
statically known beyond Gap 2's literal/constructor cases (e.g.
`result = some_function(); result.process()` — `process`'s target depends
on what `some_function` returns).

**Why it's hard**: requires control-flow analysis and cross-function type
propagation — effectively a small type-inference engine.

**How to cover it**: a future module (the document elsewhere calls this a
"Reasoning Engine type-inference layer") that:
1. Builds a return-type table for every function (from `return` statement
   analysis, recursively where needed)
2. Propagates types through assignments across function boundaries
3. Feeds resolved types back into `call_graph`'s local-scope tracking (Gap 2)

**Priority**: highest by volume, but explicitly out of Module 2's core
scope — a substantial standalone effort.

---

## Gap 2: D-008 — Package-Root Mismatch (Python core)

**Size**: concentrated in large frameworks — `ccxt` (105,488
`self_method_not_found`), `odoo` (40,372).

**What it is**: some repos' importable package root is a SUBDIRECTORY of
the cloned repo (e.g. `ccxt/python/ccxt/`), but `module_name_from_path`
computes names relative to the repo root — producing names like
`python.ccxt.base.exchange` that never match the absolute import paths
(`ccxt.base.exchange`) used in the code.

**Why D-007 didn't fix it**: D-007 fixes RELATIVE import resolution; this
is an ABSOLUTE path / root-detection problem — structurally different.

**How to cover it**: per-repo package-root detection — e.g. scan for the
directory whose name matches the most common top-level import root across
the repo's own absolute imports, and use that as the module-name base
instead of the repo root.

**Priority**: medium — affects a small number of repos but severely
(>100K unresolved in `ccxt` alone).

---

## Gap 3: Java Adapter — Real-Repo Validation

**What it is**: the Java adapter (`javalang`) is validated on a synthetic
sample only — 0 of the 69 repos are primarily Java, though Java code
EXISTS within some (`elasticsearch`: 22,101 files, `ccxt`: 763 files,
`spring-boot`: 468 files) and was scanned with 0 crashes, 156 parse errors,
2.5% resolved.

**How to cover it**: same-file resolution already works (proven on
`elasticsearch`/`spring-boot`/`ccxt`). Next steps mirror Python's own
journey:
1. Cross-file resolution (D-001 equivalent) — Java imports are always
   absolute, so this is simpler than Python's relative-import case
2. Method resolution via `extends`/`implements` (D-004 equivalent)
3. Investigate the 156 parse errors (likely newer Java syntax - records,
   sealed classes, pattern matching)

**Priority**: medium — extraction works, cross-file resolution is the
next lever (same shape as the work just done for JS).

---

## Gap 4: JavaScript Adapter — Remaining Resolution Gaps

**What it is**: after the tree-sitter rewrite + relative-import cross-file
resolution (this cycle), 3 specific patterns remain unresolved:
1. **Namespace imports** (`import * as ns from './x'`) — `ns.something()`
   not resolved (same category as Python's `qualified_module_call`, Gap 1)
2. **Local-variable method calls** (`const t = new Tool(); t.use()`) — the
   JS equivalent of Python's Gap 2 (local-scope type tracking) is not
   implemented
3. **Named default-export renames** (`export default function Bar(){}`
   then `import Foo from './bar'` — `Foo` is `Bar` renamed) — the `is_default`
   flag handles same-name default exports but not renames

**How to cover it**: each is a contained addition to the existing
`alias_map`/`local_classes` machinery — items 1 and 3 are small (extend
the alias resolution lookup), item 2 is the JS equivalent of Gap 2 (track
`new X()` assignments' types in a per-function scope map).

**Priority**: medium-high — JS extraction is now solid (0 parse errors),
so these are the highest-leverage remaining JS items.

---

## Gap 5: C/C++ Adapter — Parser Quality & Cross-File Resolution

**What it is**: the C/C++ adapter is a REGEX heuristic, not a real AST
parser (unlike Python/Java/JS). Known issues:
1. Methods aren't linked to their owning class/struct — `obj->method()`
   resolves only by name coincidence with a top-level function
2. No cross-file resolution — `#include "x.h"` is split internal/external
   but not resolved to the actual header/source pair
3. Multi-line signatures, templates, and macros are imperfectly handled
   (the kernel-style two-line signature fix improved this, but templates
   and heavy macro use remain weak spots)

**How to cover it**: replace the regex with `tree-sitter-c`/`tree-sitter-cpp`
or `libclang` — same upgrade pattern as the JS rewrite (tree-sitter
delivered 0 parse errors and +77% resolved calls for JS). A real AST would
enable:
1. Class/struct → method linking (prerequisite for method resolution)
2. `#include "x.h"` → actual file resolution → declaration/definition linking
3. Correct handling of templates/macros via the AST rather than line-by-line regex

**Priority**: highest leverage among the 3 adapters for a SINGLE change
(mirrors why the JS tree-sitter rewrite was prioritized first).

---

## Gap 6: Go and Rust Adapters — Not Started

**What it is**: registered stubs only (`is_implemented() == False`) — files
are counted via `language_composition` but not parsed.

**How to cover it**: same pattern as Java/JS/C++ — pick a parser
(`tree-sitter-go`/`tree-sitter-rust`, both available via
`tree_sitter_languages`, already proven to work in this environment),
implement `scan()` returning the standard 6-graph shape, start with
same-file resolution, validate on real repos with 0 crashes before adding
cross-file resolution.

**Priority**: lowest — no validation data exists yet to prioritize against.

---

## Summary Table

| Gap | Area | Size/Impact | Suggested Priority |
|---|---|---|---|
| 1 | Python - attribute_call (type tracking) | 1.79M instances | High value, large effort |
| 2 | Python - D-008 package-root mismatch | >100K in ccxt alone | Medium |
| 3 | Java - cross-file + method resolution | 2.5% resolved currently | Medium |
| 4 | JS - namespace/local-var/default-rename | 3 contained items | Medium-high |
| 5 | C/C++ - tree-sitter rewrite | 9.5% resolved currently | High leverage |
| 6 | Go/Rust - not started | 0% (stubs) | Lowest |

None of these block Module 2's Python-core freeze. Each is independently
addressable without touching the frozen core, following the
Extension Guide's pattern.

---

*CodeTruth Agent V3 — Module 2 — Repository Graph Engine*
*github.com/Zeeshan78699/CodeTruthAgent*
