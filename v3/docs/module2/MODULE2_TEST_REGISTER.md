# Module 2 — Test Register

**CodeTruth Agent V3 — Module 2 — Repository Graph Engine**

---

## 1. Unit Tests — `test_module2_repository_graph.py`

**31/31 PASS**

Covers all 6 graphs (V3-004 through V3-009) plus edge cases:

| Area | Tests cover |
|---|---|
| function_graph | top-level functions, methods, nested functions, async functions |
| class_graph | classes, declared bases, nested classes |
| module_graph | package detection, parent/child relationships |
| import_graph / dependency_graph | internal vs external split, relative imports (D-007), declared dependencies |
| call_graph | direct calls, self-method calls, inherited methods (D-004), qualified/dotted calls (Gap 1), local-typed method calls (Gap 2), nested function calls (D-006), external constructors (D-002), stdlib-inherited methods (D-003), unittest.TestCase methods (D-005) |
| topology | cycle detection (Gap 3) |
| edge cases | syntax-error files (parse_error), empty repos, single-file repos |

---

## 2. Integration Test — `verify_pipeline_integrity.py` (Gap 4)

Compares Module 1's `total_python_files` per repo against Module 2's
`files_scanned`. Schema-tolerant, gracefully skips if Module 1 summary
absent. Used to confirm no files are silently dropped between modules.

---

## 3. 69-Repository Validation — `scan_all_repos_module2.py`

Same 69-repo set as Module 1's validation, for direct comparability.

| Metric | Result |
|---|---|
| Repos scanned | 69 |
| Crashes | 0 |
| Governance APPROVED | 65/69 |
| Governance BLOCKED | 4/69 (nginx, react, spring-boot, ui5-webcomponents - all correctly non-Python) |
| Files scanned | 49,379 |
| Functions found | 515,610 |
| Classes found | 84,468 |
| Resolved calls | 1,005,321 |
| `self_method_not_found` | 224,737 (down from 495,783 pre-D-004, -53%) |
| `name_call_unresolved` | 178,389 |
| `attribute_call` | 1,785,190 (documented limitation - variable type tracking) |
| Parse errors | 84 (genuine Python syntax errors in source repos, e.g. Python 2 files) |

Full per-repo breakdown: `MODULE2_FULL_SUMMARY.{json,csv,md}`.

---

## 4. Multi-Language Extension Tests (new this cycle)

| Test | Coverage |
|---|---|
| `test_language_composition.py` | Registry classification across 6 languages + "other extensions" bucket |
| `test_java_js_adapters.py` | Synthetic Java/JS samples with known expected output |
| `test_lang_adapters_real_repo.py` | Single-repo real-world test, any of the 3 implemented adapters |
| `scan_all_repos_languages.py` | 69-repo summary for Java/JS/C++ |

### 69-Repo Multi-Language Results

| Language | Repos with files | Files found | Functions | Classes | Resolved | Resolved % | Parse errors | Crashes |
|---|---|---|---|---|---|---|---|---|
| C/C++ | 30/69 | 53,774 | 17,248 | 2,956 | 19,381 | 9.5% | 0 | 0 |
| Java | 5/69 | 23,340 | 19,664 | 684 | 2,900 | 2.5% | 156 | 0 |
| JavaScript/TS | 33/69 | 30,822 | 7,421 | 736 | 10,449 | 5.4% | 0 | 0 |

JavaScript's 0 parse errors (down from 1,674, a 58% failure rate with the
prior `esprima`-based adapter) and resolved-call count (+77% after adding
relative-import cross-file resolution) are the headline results of this
cycle's adapter work.

---

*CodeTruth Agent V3 — Module 2 — Repository Graph Engine*
*github.com/Zeeshan78699/CodeTruthAgent*
