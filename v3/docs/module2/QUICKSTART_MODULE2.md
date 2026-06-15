# Module 2 — Quickstart

**CodeTruth Agent V3 — Module 2 — Repository Graph Engine**

---

## Installation

Module 2's Python core has no extra dependencies beyond the standard
library (`ast`, `os`).

For the multi-language extension (optional):
```bash
pip install javalang "tree-sitter==0.21.3" tree-sitter-languages --break-system-packages
```

---

## Basic Usage

```python
from v3.repository_graph.graph_engine import build_repository_graph

report = build_repository_graph("/path/to/your/repo")

print(report["governance_gate"])     # "APPROVED" or "BLOCKED"
print(report["files_scanned"])       # int
print(report["function_graph"].keys())  # module names
```

---

## Reading the Output

```python
# All functions in a module
for func in report["function_graph"]["mypackage.utils"]:
    print(func["id"], "at line", func["lineno"])

# All resolved calls FROM a module
for call in report["call_graph"]["mypackage.main"]:
    print(call["caller"], "->", call["callee"], f"({call['resolution']})")

# Everything the engine couldn't resolve - check before trusting silence
for item in report["unresolved"]:
    print(item["module"], item["lineno"], item["pattern"], "-", item["note"])

# Import cycles, if any
print(report["cyclic_clusters"])  # e.g. [["pkg.a", "pkg.b"]]
```

---

## Worked Example (real, runnable)

Create this small package — a realistic mini-project with a base class,
inheritance, a cross-module constructor call, and a relative import:

```
pkg/
├── __init__.py          (empty)
├── base.py
└── sub/
    ├── __init__.py       (empty)
    ├── models.py
    └── handler.py
```

**`pkg/base.py`**
```python
class BaseModel:
    def save(self):
        return "saved"
```

**`pkg/sub/models.py`**
```python
from ..base import BaseModel

class MyModel(BaseModel):
    def export(self):
        return self.save()

class PipelineResult:
    def __init__(self, value):
        self.value = value
```

**`pkg/sub/handler.py`**
```python
from .models import PipelineResult, MyModel

def build():
    r = PipelineResult(1)
    m = MyModel()
    m.export()
    return r
```

Now run:
```python
from v3.repository_graph.graph_engine import build_repository_graph
report = build_repository_graph("/path/to/pkg/..")  # parent of pkg/

print(report["files_scanned"])       # 5
print(report["governance_gate"])     # "APPROVED"

for mod, edges in report["call_graph"].items():
    for e in edges:
        print(f"{e['caller']} -> {e['callee']}  [{e['resolution']}]")

print(report["unresolved"])          # []
```

**Actual output** (captured from a real run of this exact example):
```
5
APPROVED
pkg.sub.models.MyModel.export -> pkg.base.BaseModel.save  [inherited_method_call]
pkg.sub.handler.build -> pkg.sub.models.PipelineResult.__init__  [imported_call]
pkg.sub.handler.build -> pkg.sub.models.MyModel.<class>  [imported_call]
pkg.sub.handler.build -> pkg.sub.models.MyModel.export  [local_typed_method_call]
[]
```

What just happened, in plain terms:
- `MyModel.export()` calls `self.save()` — `save` is defined in `BaseModel`,
  a DIFFERENT file. Resolved via cross-module inheritance (D-004).
- `handler.py` does `from .models import PipelineResult, MyModel` — a
  RELATIVE import (`.models`). Both `PipelineResult(1)` and `MyModel()`
  resolve to `pkg.sub.models`, the correct target file, via D-007's
  relative-import resolution.
- `m.export()` — `m` was assigned `MyModel()` two lines above; Module 2
  tracked that local variable's type (Gap 2) and resolved the method call.
- `unresolved` is empty — every call in this example was provably resolved,
  with 0 guesses.

---

## Running on Your Own Repository

```python
from v3.repository_graph.graph_engine import build_repository_graph

report = build_repository_graph("/path/to/your/repo")
```

That's it — one call, the entire repo. A few things to expect on real,
larger codebases:

**Check the governance gate first**:
```python
print(report["governance_gate"])  # "APPROVED" or "BLOCKED"
```
`BLOCKED` with `files_scanned == 0` means the repo has no `.py` files
(e.g. it's a Java/JS/C/C++ project) — this is a correct result, not an
error. See the multi-language section below if you want to scan those
files too.

**Don't expect a high "resolved %"** — and don't worry if you don't get
one. Across 69 real repos, resolved calls ranged roughly 15-45% of all
calls. The DOMINANT remaining category, `attribute_call` (method calls on
local variables whose type isn't tracked, e.g. `data.process()`), is a
documented, by-design limitation — not a sign something's wrong with your
code or with Module 2. Focus on the ABSOLUTE resolved count and the
`unresolved` log's reasons, not the percentage.

**A quick health-check snippet**:
```python
from collections import Counter

resolved = sum(len(v) for v in report["call_graph"].values())
unresolved = Counter(u["pattern"] for u in report["unresolved"])

print(f"Files scanned: {report['files_scanned']}")
print(f"Functions: {sum(len(v) for v in report['function_graph'].values())}")
print(f"Classes: {sum(len(v) for v in report['class_graph'].values())}")
print(f"Resolved calls: {resolved}")
print(f"Unresolved breakdown: {dict(unresolved)}")
print(f"Import cycles: {report['cyclic_clusters']}")
```

**If your repo has relative imports** (`from .models import X`,
`from ..utils import Y` — common in larger packages), these are resolved
via D-007 automatically — no configuration needed.

**If your repo has a non-standard package layout** (the importable package
lives in a subdirectory of the repo root, e.g. `myrepo/src/mypackage/`),
be aware of the documented D-008 limitation: module names are computed
relative to the path you pass to `build_repository_graph()`, so absolute
imports matching the INSTALLED package name (`mypackage.foo`) may not match
computed module names (`src.mypackage.foo`) if you point at the repo root.
**Workaround**: point `build_repository_graph()` directly at the directory
that IS the package root (e.g. `myrepo/src/` instead of `myrepo/`) if you
hit unexpectedly high `self_method_not_found`/`name_call_unresolved` counts.

**Performance**: the engine scans every `.py` file via `ast.parse()` — for
reference, a 1,700-file repo (FreeCAD-sized) completed in well under a
minute on standard hardware during the 69-repo validation. No caching or
incremental mode exists yet (see `MODULE2_GAPS_AND_ROADMAP.md` for future
work like `incremental_graph_manager.py`).

---

## Running the Test Suite

```bash
python -m unittest v3.repository_graph.tests.test_module2_repository_graph
```
Expected: `Ran 31 tests ... OK`

---

## Running the 69-Repo Validation

```bash
python v3/repository_graph/tests/scan_all_repos_module2.py
```
Outputs `MODULE2_FULL_SUMMARY.{json,csv,md}` to
`v3/outputs/module2_graphs/`. Set `CLONED_REPOS_DIR` in the script to your
local repo-clone directory.

---

## Multi-Language Extension (optional)

```python
from v3.repository_graph.languages import classify_files, ADAPTERS

# See what languages are registered and which are implemented
for adapter in ADAPTERS:
    print(adapter.language_name, adapter.is_implemented())

# Classify a repo's files by language
composition = classify_files("/path/to/repo")
print(composition["javascript"]["adapter"].scan("/path/to/repo",
      composition["javascript"]["files"]))
```

`build_repository_graph()`'s output also includes `language_composition`
(file counts per language) automatically - no extra calls needed for that
field.

---

*CodeTruth Agent V3 — Module 2 — Repository Graph Engine*
*github.com/Zeeshan78699/CodeTruthAgent*
