# Module 2 — Capability Proof

**CodeTruth Agent V3 — Module 2 — Repository Graph Engine**

This document shows concrete, real evidence for each capability claimed in
`MODULE2_DOCUMENTATION.md` — actual input/output, not descriptions.

---

## 1. Function & Class Extraction (V3-004, V3-005)

Input (`helper.py`):
```python
class BaseService:
    def save(self):
        return "saved"

class MyService(BaseService):
    def run(self):
        return self.save()
```

Output (`function_graph`, `class_graph`):
```json
"function_graph": {
  "helper": [
    {"id": "helper.BaseService.save", "name": "save", "lineno": 2, "scope": "BaseService", "is_async": false},
    {"id": "helper.MyService.run", "name": "run", "lineno": 6, "scope": "MyService", "is_async": false}
  ]
},
"class_graph": {
  "helper": [
    {"id": "helper.BaseService", "name": "BaseService", "lineno": 1, "bases": [], "scope": null},
    {"id": "helper.MyService", "name": "MyService", "lineno": 5, "bases": ["BaseService"], "scope": null}
  ]
}
```

---

## 2. Cross-Module Call Resolution (D-001, V3-009)

Input (`main.py`): `from helper import MyService` then `MyService().run()`.

Output (`call_graph`):
```json
{"caller": "main.<module>", "callee": "helper.MyService.run", "lineno": 3, "resolution": "imported_call"}
```
Without D-001 (two-stage global build), this would be logged as
"unresolved external call" — Stage A builds the global symbol table first,
Stage B resolves against it.

---

## 3. Cross-Module Inheritance Resolution (D-004)

`MyService.run()` calls `self.save()` — `save` is defined in `BaseService`,
a DIFFERENT class, found via D-004's `_find_method_in_hierarchy()`:
```json
{"caller": "helper.MyService.run", "callee": "helper.BaseService.save", "lineno": 7, "resolution": "inherited_method_call"}
```

---

## 4. Relative Import Resolution (D-007)

Input (`pkg/sub/models.py`): `from ..base import BaseModel` then
`class MyModel(BaseModel): ...`.

D-007 resolves `..base` (relative, level=2) to the absolute module
`pkg.base` using the importing module's own package path — verified on a
4-file synthetic package with 0 unresolved items.

---

## 5. Honest "Truth Boundary" (unresolved log)

Input: `data.process()` where `data`'s type can't be statically determined.

Output (`unresolved`):
```json
{"module": "main", "lineno": 12, "pattern": "attribute_call",
 "note": "Method call on local variable 'data' - type not tracked"}
```
No graph edge is created to a guessed target — the call is logged with
file/line/reason instead.

---

## 6. Cycle Detection (Gap 3 — topology.py)

Two modules importing each other (`a.py` imports `b`, `b.py` imports `a`)
produce:
```json
"cyclic_clusters": [["a", "b"]]
```
and both modules' `module_graph` entries get `"in_cyclic_loop": true,
"cyclic_cluster_id": 0`.

---

## 7. Scale & Stability (69-Repo Validation)

| Metric | Value |
|---|---|
| Repos scanned | 69 |
| Crashes | 0 |
| Files scanned | 49,379 |
| Functions found | 515,610 |
| Classes found | 84,468 |
| Resolved calls | 1,005,321 |
| Governance APPROVED | 65/69 (4 non-Python repos correctly BLOCKED) |

Full per-repo breakdown: `MODULE2_VALIDATION_SUMMARY.md`.

---

## 8. Multi-Language Extension (languages/)

Same `build_repository_graph()`-shaped output produced for non-Python code,
via registered adapters — zero changes to the Python core (31/31 tests pass
throughout):

| Language | Real-repo evidence |
|---|---|
| C/C++ | Redis (20.3% resolved, 682 functions), u-boot (19.4%, 215 functions) |
| Java | Synthetic sample: classes, methods, inheritance, same-class calls all correctly extracted via `javalang` |
| JavaScript/TS | vscode (50-file real test): 0 parse errors (was 28/30 with prior `esprima`-based adapter), 620 functions, 55 classes extracted |

**Cross-file resolution (`imported_call`/`imported_constructor_call`)** was
verified correct on a synthetic 2-file package (relative-import + class
constructor + default export, 0 unresolved). On the 69-repo aggregate,
total resolved calls increased +77% (5,899 -> 10,449) after this change -
though on the specific 50-file vscode sample, the resolvable import targets
happened to fall outside the sampled files (0 `imported_call` hits there,
186 correctly logged as "target file not in scanned set"). The mechanism is
verified working; its yield on any given sample depends on the file cap.

---

*CodeTruth Agent V3 — Module 2 — Repository Graph Engine*
*github.com/Zeeshan78699/CodeTruthAgent*
