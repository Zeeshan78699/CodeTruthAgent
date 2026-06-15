# Module 2 — Questions & Answers

**CodeTruth Agent V3 — Module 2 — Repository Graph Engine**

---

**Q: What does Module 2 actually produce?**
Six graphs describing a repository's code structure: which functions and
classes exist (`function_graph`, `class_graph`), how files/packages relate
(`module_graph`), what each file imports internally (`import_graph`) and
externally (`dependency_graph`), and which functions/methods call which
(`call_graph`). Plus an honest `unresolved` log for anything it couldn't
determine.

**Q: How is this different from just running a Python AST parser?**
A raw AST only sees one file at a time. Module 2's two-stage build (D-001)
first catalogs every function/class across the WHOLE repo (Stage A), then
resolves calls against that global table (Stage B) - so `helper()` after
`from pkg.utils import helper` correctly points to `pkg.utils.helper`, not
"unresolved."

**Q: What's the "resolved %" number, and why is it often 15-40%, not 90%+?**
It's resolved-calls / (resolved + unresolved). The majority of "unresolved"
is `attribute_call` - method calls on local variables whose type isn't
statically known (`data.process()`). This requires full variable
type-inference, a substantially larger feature deliberately out of scope
for Module 2's core (see `MODULE2_DOCUMENTATION.md` Section 8.1). The
*absolute* resolved count (1,005,321 across 69 repos) is the more
meaningful metric - it more than doubled through D-004 through D-007.

**Q: Does Module 2 ever guess?**
No. Anything it can't prove is logged in `unresolved` with the file,
line number, and a reason - never turned into a graph edge. This is the
"Truth Boundary" - same honesty principle as Module 1's "No Framework
Detected."

**Q: What happens on a non-Python repo (e.g. a pure JavaScript project)?**
Module 2's Python core finds 0 `.py` files and the governance gate returns
BLOCKED - correct, not an error (verified on `nginx`, `react`,
`spring-boot`, `ui5-webcomponents` in the 69-repo set). The
`language_composition` field (additive) still reports how many JS/Java/C++
files exist, and - if those adapters are used - can produce graphs for
those languages too (see multi-language scaffold).

**Q: Is the multi-language support "done"?**
No - it's an early scaffold with working first implementations for Java,
JavaScript/TypeScript, and C/C++ (each validated on real repos, 0 crashes),
plus stubs for Go/Rust. Each is at roughly the maturity Python was at
before D-001 (same-file resolution only, except JavaScript which also got
relative-import cross-file resolution). This is explicitly NOT part of
Module 2's original V3-004-009 spec - it's a head start for a future
"Multi-Language" module.

**Q: What's D-008 and why wasn't it fixed?**
Some large frameworks (e.g. `ccxt`) have their importable package root in a
subdirectory of the cloned repo, causing module-name/import-path mismatches
that D-007 (relative imports) didn't fix. Root-causing this requires
per-repo package-root detection - a different, larger investigation.
Documented as an open item rather than rushed.

**Q: How do I run it?**
```python
from v3.repository_graph.graph_engine import build_repository_graph
report = build_repository_graph("/path/to/repo")
```
See `QUICKSTART_MODULE2.md`.

**Q: How was this validated?**
69 real open-source repositories, 49,379 Python files, 0 crashes, 31/31
unit tests. Full numbers in `MODULE2_VALIDATION_SUMMARY.md`.

---

*CodeTruth Agent V3 — Module 2 — Repository Graph Engine*
*github.com/Zeeshan78699/CodeTruthAgent*
