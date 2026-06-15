# CodeTruth Agent V3 — Module 2: Repository Graph Engine

Independent AI research project. GPLv3.

## What it does

Module 1 answers "what kind of repository is this?" Module 2 answers the
next question: **"how is the code inside it wired together?"**

Given a path to a repository, it produces six structural graphs:

- **`function_graph`** (V3-004) — every function/method definition
- **`class_graph`** (V3-005) — every class definition, with declared bases
- **`module_graph`** (V3-006) — package/directory structure, incl. import-cycle annotations
- **`import_graph`** (V3-007) — internal (project-to-project) imports
- **`dependency_graph`** (V3-008) — external (stdlib/3rd-party) dependencies
- **`call_graph`** (V3-009) — resolved function/method call edges, globally cross-referenced

Plus an honest **`unresolved`** log — anything the engine cannot prove is
recorded with file/line/reason, never guessed. A **governance gate**
(APPROVED/BLOCKED) consistent with Module 1's repo classification.

It performs no network access and makes no modifications to the scanned
repository.

## Example

```bash
python -c "
from v3.repository_graph.graph_engine import build_repository_graph
report = build_repository_graph('/path/to/repo')
print(report['governance_gate'])
print(report['files_scanned'], 'files')
print(sum(len(v) for v in report['call_graph'].values()), 'call edges')
print(len(report['unresolved']), 'unresolved (honestly logged)')
"
```

Output (abridged, on a real repo):

```
APPROVED
1769 files
40719 call edges
299395 unresolved (honestly logged)
```

## Validation

Run against the same 69 real, cloned, open-source repositories used for
Module 1's validation:

```
69/69 repos scanned, 0 crashes
65/69 governance gate APPROVED
 4/69 correctly BLOCKED (non-Python repos: nginx, react, spring-boot, ui5-webcomponents)
49,379 total Python files scanned
515,610 functions found
84,468 classes found
1,005,321 resolved call edges
31/31 unit tests pass
```

Full results: [`v3/docs/module2/MODULE2_VALIDATION_SUMMARY.md`](v3/docs/module2/MODULE2_VALIDATION_SUMMARY.md)

## How it works (brief)

Two-stage build (decision D-001):

1. **Stage A** (per file) — parse each `.py` file once, extract
   `function_graph`, `class_graph`, `module_graph`, and raw imports.
2. **Stage B** (global) — using the project-wide symbol table built in
   Stage A, resolve `call_graph` edges across modules, packages, relative
   imports, and class inheritance chains.

A function defined in `pkg/utils.py` and called from `main.py` via
`from pkg.utils import helper; helper()` cannot be resolved by looking at
`main.py` alone — Stage A must first catalog the whole project.

Seven decisions (D-001 through D-007) progressively closed resolution gaps:
cross-module inheritance, qualified/dotted calls, local variable type
tracking, nested function calls, import-cycle detection, and relative
import resolution. Full log:
[`v3/docs/module2/MODULE2_DECISIONS.md`](v3/docs/module2/MODULE2_DECISIONS.md)

## Multi-Language Extension (optional, validated baseline — not frozen)

`v3/repository_graph/languages/` is an extension-point scaffold (same
philosophy as Module 1's `framework_signatures.py`) with working first
implementations for **Java** (`javalang`), **JavaScript/TypeScript**
(`tree-sitter`, incl. relative-import cross-file resolution), and **C/C++**
(regex heuristic) — all validated on real repos (Redis, u-boot, vscode,
ui5-webcomponents, react, elasticsearch, spring-boot) with 0 crashes. Go and
Rust are registered stubs. See `requirements-languages.txt` to enable.

## Documentation

- [`MODULE2_REAL_WORLD_PROBLEM.md`](v3/docs/module2/MODULE2_REAL_WORLD_PROBLEM.md) — the problem this solves, and how
- [`MODULE2_DOCUMENTATION.md`](v3/docs/module2/MODULE2_DOCUMENTATION.md) — architecture, schema, resolution categories
- [`MODULE2_DECISIONS.md`](v3/docs/module2/MODULE2_DECISIONS.md) — D-001 through D-007 decision log
- [`MODULE2_CAPABILITY_PROOF.md`](v3/docs/module2/MODULE2_CAPABILITY_PROOF.md) — concrete input/output evidence
- [`MODULE2_VALIDATION_SUMMARY.md`](v3/docs/module2/MODULE2_VALIDATION_SUMMARY.md) — full 69-repo results
- [`MODULE2_TEST_REGISTER.md`](v3/docs/module2/MODULE2_TEST_REGISTER.md) — test suite results
- [`MODULE2_COMPONENTS_AND_CAPABILITIES.md`](v3/docs/module2/MODULE2_COMPONENTS_AND_CAPABILITIES.md) — file-by-file map
- [`MODULE2_EXTENSION_GUIDE.md`](v3/docs/module2/MODULE2_EXTENSION_GUIDE.md) — how to add resolution rules or languages
- [`MODULE2_QUESTION_AND_ANSWER.md`](v3/docs/module2/MODULE2_QUESTION_AND_ANSWER.md) — FAQ
- [`QUICKSTART_MODULE2.md`](v3/docs/module2/QUICKSTART_MODULE2.md) — usage guide

## Project Structure

```
v3/
├── repository_graph/        # Module 2 source
│   ├── graph_engine.py
│   ├── function_graph.py
│   ├── class_graph.py
│   ├── module_graph.py
│   ├── import_graph.py
│   ├── dependency_graph.py
│   ├── call_graph.py
│   ├── topology.py
│   ├── languages/            # optional multi-language extension
│   └── tests/
│       ├── test_module2_repository_graph.py   # 31 unit tests
│       ├── scan_all_repos_module2.py            # 69-repo validation
│       └── scan_all_repos_languages.py          # 69-repo language adapter summary
├── outputs/module2_graphs/    # per-repo reports + summary
└── docs/module2/              # documentation (this README links here)
```

## Status

Module 2's Python core (V3-004 through V3-009) is complete and frozen as of
`v3.0.0-module2`. The multi-language extension scaffold is a validated
baseline, not frozen, and may be extended without affecting the core.
Module 3 is next.

## License

GPLv3 — see `LICENSE`.

## Author

Zeeshan Saud — Independent AI Researcher, UAE
github.com/Zeeshan78699/CodeTruthAgent
