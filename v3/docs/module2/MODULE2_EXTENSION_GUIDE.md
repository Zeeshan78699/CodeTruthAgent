# Module 2 — Extension Guide

**CodeTruth Agent V3 — Module 2 — Repository Graph Engine**

Module 2 has two extension points. Both follow the same philosophy as
Module 1's `framework_signatures.py`: extend by ADDING a file/entry, not by
modifying the frozen core.

---

## Extension Point 1: New Resolution Rules (Python core)

`call_graph.py`'s resolution order is: same-class -> resolved inheritance
chain (D-004) -> stdlib whitelist (D-003) -> qualified/dotted paths (Gap 1)
-> local-scope type tracking (Gap 2) -> nested functions (D-006) ->
unresolved.

To add a new resolution rule:
1. Identify the `unresolved` pattern it should reduce (e.g.
   `name_call_unresolved`, `attribute_call`).
2. Add a new resolution function (mirroring `_find_method_in_hierarchy` or
   `_resolve_dotted_path`'s structure: take the global symbol tables built
   in Stage A, return a `(module, target)` tuple or `None`).
3. Insert it into the resolution order in `_resolve_call`/`_resolve_self_call`
   BEFORE the final `unresolved.append(...)` fallback.
4. Add a new `resolution` category name (document it in
   `MODULE2_DOCUMENTATION.md` Section 6).
5. Add unit tests to `test_module2_repository_graph.py`; re-run the 69-repo
   scan to measure impact on `MODULE2_FULL_SUMMARY`.

This is exactly how D-002 through D-007 were each added - no prior decision
was ever removed, only new rules inserted before the fallback.

---

## Extension Point 2: New Languages (languages/)

To add support for a new language (e.g. Go, Rust - currently stubs):

1. **Open the existing stub** (e.g. `languages/go_adapter.py`) - it already
   declares `file_extensions` and is registered in `registry.py`.
2. **Choose a parser**: prefer a real AST parser (pure-Python if possible -
   `javalang` for Java, `tree-sitter-*` via `tree_sitter_languages` for
   JS/TS/Go/Rust/C/C++). Avoid regex unless no parser is feasible (the
   C/C++ adapter is regex as a documented lower-confidence first pass).
3. **Implement `scan(repo_root, file_paths)`** to return the SAME shape as
   Python's `build_repository_graph()` output:
   `function_graph`, `class_graph`, `module_graph`, `import_graph`,
   `dependency_graph`, `call_graph`, `unresolved`, `cyclic_clusters`.
4. **Set `is_implemented()` to `True`**.
5. **Start with same-file resolution** (like Java/C++'s current state),
   then add cross-file resolution as a second pass (like JavaScript's
   relative-import resolution) once extraction is validated.

**Zero changes required** to `call_graph.py`, `function_graph.py`,
`class_graph.py`, `module_graph.py`, `import_graph.py`,
`dependency_graph.py`, `topology.py`, or `graph_engine.py`'s Stage A/B
logic - `graph_engine.py` only calls `languages.classify_files()` for the
additive `language_composition` field, wrapped in try/except.

**Validation checklist** (same as Java/JS/C++ this cycle):
- Synthetic test with known expected output (`test_java_js_adapters.py` pattern)
- Real-repo test, 0 crashes (`test_lang_adapters_real_repo.py`)
- 69-repo summary (`scan_all_repos_languages.py`)
- Document known limitations honestly in the adapter's docstring (see
  `javascript_adapter.py` for the pattern - explicit "SCOPE" and "KNOWN
  LIMITATION" sections)

---

*CodeTruth Agent V3 — Module 2 — Repository Graph Engine*
*github.com/Zeeshan78699/CodeTruthAgent*
