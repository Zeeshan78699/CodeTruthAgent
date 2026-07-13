# Release Notes — CodeTruth Agent V3 · Module 3

**Module:** Repository Reasoning
**Date:** 2026-07-10
**Corpus:** 74 repositories · 71 COMPLETE · 3 REVIEW_REQUIRED · **0 invariant failures**

---

## Headline

Module 3 now dispatches reasoning **per language**. Python retains its full
Phase 3A/3B pipeline, unchanged and frozen. Seven other languages route to
validated engines. One refuses honestly.

```
run_codetruth.py
        ├── python  → frozen module3_pipeline        (full resolution)
        ├── java    → bridge.answer                  (call graph + queries)
        ├── js      → bridge.answer
        ├── c_cpp   → bridge.answer
        ├── go      → bridge.advanced_reparsed       (caller-aware re-parse)
        ├── csharp  → bridge.advanced_reparsed
        ├── sql     → bridge.sql_lineage             (data lineage)
        └── rust    → NOT_IMPLEMENTED                (declared stub, zero capabilities)
```

---

## What Is New

### Per-language reasoning dispatch

Non-Python repositories previously received Module 2 structure and a note that
reasoning was Python-only. They now receive real call graphs and query surfaces.

| Language | Repository | Reasoning index |
|---|---|---|
| go | Go compiler | **33,428 functions** |
| java | elasticsearch | **30,291 functions** |
| csharp | ccxt/cs | **8,493 functions** |
| java | spring-boot | 700 functions |
| sql | camel | 2 reads · 2 writes · 1 data_flow |

### The common envelope

Each language declares what it computed and what it cannot see. **No language
borrows Python's `guesses` or `edge_provenance`** — those are Phase 3A/3B
measurements, and claiming them elsewhere would fabricate a guarantee.

### Evidence-based language routing

Selection is by **actual file count** via `bridge.classify_files()`, with
provenance recorded on every run:

```json
"language_selection": {"language": "python", "source": "bridge_classify_files",
                       "confidence": "high", "files_provided": 4609}
```

`DOMAIN_TO_LANGUAGE` survives only as a flagged, low-confidence last resort that
forces `REVIEW_REQUIRED`.

### The completeness guard

`COMPLETE` requires primary artifacts appropriate to the selected language's
paradigm. A pipeline that analyzed nothing can no longer report success.

---

## Bugs Fixed

| Bug | Before | After |
|---|---|---|
| **odoo false completeness** | `COMPLETE` · 77 SQL files · **0 functions** · 8,485 Python ignored | `COMPLETE` · python · **48,005 functions** |
| **rust wrong-language** | `COMPLETE` · 190 JavaScript files of 36,176 Rust | `REVIEW_REQUIRED` · `NOT_IMPLEMENTED` · zero capabilities |
| **Adapter substitution** | `get_adapter("java")` → `PythonAdapter` · 0 files parsed | all 8 mapped · unknown language **raises** |
| **Empty file list** | `adapter.scan(file_paths=[])` | real per-language list |
| **spring-boot** | 0 functions · `REVIEW_REQUIRED` | 468 files · **2,019 functions** · 1,231 edges |
| **nginx** | 0 files scanned | 401 files · `COMPLETE` |
| **elasticsearch** | `M2_ERROR: RecursionError` | 22,101 files · **134,037 functions** |
| **Gate contradiction** | `status: REVIEW_REQUIRED` + `gate: APPROVED` | consistent |
| **Shape mismatch** | java/c_cpp reported `functions: 0` while holding 301 | shape-aware summary |

### The root cause of odoo

```python
DOMAIN_TO_LANGUAGE = {"ERP_SYSTEM": "sql", ...}
```

Module 1 correctly classified odoo as `ERP_SYSTEM`. `language_composition`
returned `{}`. The router fell through to a hardcoded map and analyzed 77 SQL
files while ignoring 8,485 Python files — reporting `COMPLETE / APPROVED`.

**A guess was hardcoded inside the guess-refusing tool.** It sat unexamined for
weeks.

---

## Corpus Result

```
Repositories tested   : 74
COMPLETE (APPROVED)   : 71
REVIEW_REQUIRED       :  3    ← python, striplog (M1 abstention); rust (declared stub)
BLOCKED               :  0
Pipeline errors       :  0
Invariant failures    :  0
Language-review flags :  0
```

Before this cycle: **72 COMPLETE, 2 REVIEW_REQUIRED, 6 invariant failures.**

The `COMPLETE` count *fell* by one. That is the pipeline getting more honest, not
less capable — rust left `COMPLETE`, where it never belonged.

---

## Zero-Guess Contract at Scale

| Repository | Functions | Edges | Guesses | Provenance |
|---|---|---|---|---|
| PyTorch | 143,436 | 319,506 | **0** | 312,650 + 6,856 = 319,506 ✓ |
| transformers | 55,521 | 105,280 | **0** | 100,225 + 5,055 = 105,280 ✓ |

Edge provenance reconciles to the unit at over 100,000 edges. Both repositories
are dominated by dynamic dispatch; resolution coverage is correspondingly low.

**Low coverage with zero guesses is SOUND.** The engine declined what it could
not prove and recorded why.

---

## Known Limitations

| Limitation | Detail |
|---|---|
| **Near-parity routing** | PyTorch: 4,733 C/C++ vs 4,609 Python — a **1.3% margin** decides which analysis runs. All 74 corpus repositories have decisive margins. Use an explicit override for such repositories. |
| **C/C++ under-extraction** | nginx: 401 files → 15 functions. |
| **javalang recursion** | Mitigated by a scoped pipeline guard, not fixed at source. |
| **Go/C# re-parse** | Their Module 2 adapters drop callers. Files are parsed twice. |
| **No multi-repo UAT** | Each non-Python language is proven on one real repository. |
| **No deep resolution outside Python** | No attribute resolution, MRO, `super()` chains, edge provenance, or guess counting. |

---

## Honest Claim

> **Module 3 provides language-aware reasoning across the supported languages,
> with Python fully validated and the remaining language routes validated
> according to their current implementation depth.**

**Not claimed:** depth equivalence between Python and any other language ·
multi-repo UAT for any non-Python route · complete caller sets for any language ·
any knowledge of runtime behaviour.

---

## What Module 3 Does Not Do

It **scopes** an issue. It does not **diagnose** one.

Every report is a verified in-repository **floor** plus an explicit map of what
could not be seen. Root-cause analysis, runtime behaviour, and data-flow tracing
are different module classes and do not exist.

---

## Freeze Prerequisite — Outstanding

Approximately 30 debugging scripts were moved from `repository_reasoning\` into
`_scratch\`. **The corpus has not been re-run since.**

"They were only debug scripts" is a hypothesis until the corpus reproduces
**71 / 3 / 0**.

```powershell
python run_corpus_eval.py --root "C:\repos\v3" --runner "v3\run_codetruth.py"
```

**This gates the freeze.** A tag should point at a tree that is clean *and*
verified in its clean state.

---

## Documentation Corrections Required

Two published documents assert accuracy that measurement contradicts, and must
carry a dated correction notice before either is cited as evidence:

- **`MODULE1_CAPABILITY_PROOF.md`** — reports 69/69 correct application types and
  `10/10` on application-type detection. A subsequent 94-repository held-out
  evaluation measured ~51% accuracy, with confidence **inversely** correlated
  with correctness. Flask is classified `WEB_APPLICATION` though it is a library;
  VSCode is assigned framework "React" though it is TypeScript.

- **`MODULE2_VALIDATION_REPORT.md`** — states "non-Python repos correctly
  BLOCKED" (today: 0 BLOCKED) and marks the Go and C# adapters `✅ Validated`
  (in the live pipeline both produce **0 functions**; the graphs come from Module
  3's re-parse).

**`MODULE2_CAPABILITY_MATRIX.md` requires no correction.** It separates
*implemented* from *proven* and refuses to claim the difference. It is the model
these Module 3 documents follow.

---

*CodeTruth Agent V3 — github.com/Zeeshan78699/CodeTruthAgent*
*AI imagines. CodeTruth checks. Nature tests. Humans decide.*
