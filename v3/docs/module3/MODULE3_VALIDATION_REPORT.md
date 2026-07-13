# CodeTruth Agent V3 — Module 3 Validation Report

**Module:** Module 3 — Repository Reasoning
**Status:** Implementation complete · Corpus-validated
**Date:** 2026-07-10
**Corpus:** 74 repositories · **0 invariant failures**

---

## Objective

> Provide deterministic, language-aware reasoning over the verified repository
> graph — answering who-calls, change-impact, dead-code, and dependency
> questions — while never asserting a caller, an edge, or a guarantee that was
> not computed.

---

## 1. Corpus Result

```
Repositories tested         : 74
COMPLETE (APPROVED)         : 71
REVIEW_REQUIRED             :  3
BLOCKED                     :  0
Pipeline errors             :  0
Invariant failures          :  0
Language-review flags       :  0
```

### The three REVIEW_REQUIRED repositories

Each **passes** its contract by refusing honestly. None is a defect.

| Repository | Cause | Behaviour |
|---|---|---|
| `python` (CPython) | Module 1 could not classify confidently | Governance gate held. Honest abstention. |
| `striplog` | Module 1 could not classify confidently | Governance gate held. Honest abstention. |
| `rust` | Dominant language identified (36,176 `.rs` files); adapter is a declared stub | `NOT_IMPLEMENTED` · zero capabilities · no findings claimed |

The rust row is the first real-data exercise of the envelope invariant
(`NOT_IMPLEMENTED` ⇒ `capabilities == []`). Prior to 2026-07-10 that check had
only ever passed against synthetic input.

---

## 2. Per-Engine Pipeline Validation

Every engine kind was exercised in the live pipeline on a real repository.

| Engine | Language | Repository | Result |
|---|---|---|---|
| frozen M3 (3A/3B) | python | flask | `guesses: 0` · edge provenance exact |
| `bridge.answer` | java | elasticsearch | 22,101 files → 134,037 functions · 30,291-function index |
| `bridge.answer` | java | spring-boot | 468 files → 2,019 functions · 1,231 edges · 700-function index |
| `bridge.answer` | javascript | react | COMPLETE |
| `bridge.answer` | c_cpp | nginx | 401 files · COMPLETE |
| `bridge.advanced_reparsed` | go | Go compiler | 11,437 files · **33,428-function index** |
| `bridge.advanced_reparsed` | csharp | ccxt/cs | **8,493-function index** |
| `bridge.sql_lineage` | sql | camel | 2 reads · 2 writes · 1 data_flow |
| — | rust | rust | `NOT_IMPLEMENTED` · zero capabilities |

### What the Go and C# rows demonstrate

Module 2's Go adapter scanned **11,437 files and produced 0 functions**. Its C#
adapter produced **0 functions**. Both record callees without enclosing callers,
so no directed call graph can be built from their output.

The completeness guard correctly refused to report COMPLETE. Module 3's
caller-aware re-parse then produced 33,428 and 8,493 functions respectively.

**The graphs come from Module 3, not from the adapters.**

---

## 3. Zero-Guess Contract at Scale

Verified on repositories outside the corpus.

| Repository | Files | Functions | Edges | Guesses | Provenance |
|---|---|---|---|---|---|
| PyTorch | 4,620 | 143,436 | 319,506 | **0** | exact |
| transformers | 4,469 | 55,521 | 105,280 | **0** | 100,225 + 5,055 = 105,280 ✓ |
| flask | 83 | 1,460 | 697 | **0** | 686 + 11 = 697 ✓ |

Edge provenance reconciles to the unit: every edge traces to Module 2's parse or
a labelled Module 3 resolution. Nothing is fabricated.

Both PyTorch and transformers are dominated by dynamic dispatch. Resolution
coverage is correspondingly low (PyTorch: 2.39% of attribute calls). **Low
coverage with zero guesses is SOUND** — the engine declined what it could not
prove and recorded why.

---

## 4. Invariant Contract

Enforced across all 74 repositories, branched by outcome. **Nothing is skipped.**
Every repository passes by behaving correctly *for its gate*.

### Universal — always asserted

```
✅ Status is one of the known honest states
✅ No fabricated evidence
✅ Truth Boundary present
✅ No silent success — a non-COMPLETE run claims no findings
✅ Gate and status are consistent
```

### Conditional — asserted per outcome

| Outcome | Invariant |
|---|---|
| `COMPLETE` + Python M3 ran | `guesses == 0` · `total_edges == module2_edges + local_receiver_added` |
| `COMPLETE` + non-Python engine | Primary artifacts exist (graph or lineage) |
| `REVIEW_REQUIRED` | Gate matches status · reason reported · no findings |
| `BLOCKED` | No findings claimed · reason reported |
| `M2_ERROR` / `M3_ERROR` | Honest loud failure with a reason · no findings claimed |
| Any envelope | `ENGINE_ERROR` or `NOT_IMPLEMENTED` ⇒ `capabilities == []` |

### Two design points

**`guesses` is gated on the measurement, not the block.** The per-language
envelope carries a `truth_boundary` with `{scope, limitations}` — deliberately
without `guesses`. The invariant therefore checks for the *presence of the
`guesses` key*, not the presence of a `truth_boundary`. Checking the latter
would demand a Python-only metric from engines that never compute it.

**An honestly-reported pipeline error is contract-compliant.** `M2_ERROR` with a
real reason and no findings claimed means the tool failed loudly rather than
fabricating. That is a robustness issue to log — **not** a Truth Boundary
violation.

---

## 5. Bugs Found and Fixed During Validation

The corpus found defects that a green `COMPLETE` concealed. Each was
root-caused by reading the implementation, not by inference.

| Bug | Symptom | Root cause | Status |
|---|---|---|---|
| **odoo false completeness** | `COMPLETE / APPROVED` with **0 functions** | `language_composition` returned `{}` → fell through to `DOMAIN_TO_LANGUAGE["ERP_SYSTEM"] = "sql"` → analyzed 77 SQL files, ignored 8,485 Python + 5,857 JavaScript | Fixed — evidence-based routing |
| **rust wrong-language COMPLETE** | `COMPLETE` on 190 JavaScript files out of 36,176 Rust | `rust` omitted from `adapter_langs`; the router filtered it out and javascript won by default | Fixed — a stub must be *selected* so it can *refuse* |
| **Adapter substitution** | java/javascript/c_cpp scanned 0 files | `get_adapter()` fell through to `else: PythonAdapter()` | Fixed — all 8 mapped; unknown language now **raises** |
| **Empty file list** | Non-Python adapters received nothing | `adapter.scan(file_paths=[])` | Fixed — real per-language list |
| **Shape mismatch** | java/c_cpp reported `functions: 0` while holding 301 | `_m2_summary` read Python-only keys | Fixed — shape-aware |
| **Gate contradiction** | `status: REVIEW_REQUIRED` with `gate: APPROVED` | Guard set status, left stale gate | Fixed |
| **javalang recursion** | elasticsearch aborted the entire scan | 22,101 Java files exceed Python's recursion cap | Mitigated — scoped guard, always restored |

### What caught them

**Not the completeness guard.** odoo's SQL analysis produced 17 tables; rust's
JavaScript analysis produced real functions. Both had *substance*. The guard
checks whether substance exists — not whether it is about the right thing.

**Both were caught by the neutral language-review flag**, which records the fact
that Module 1's framework and Module 2's language name different languages, and
delivers no verdict.

**Two of the fixes broke things that the invariant suite caught within minutes** —
`get_adapter` silently substituting `PythonAdapter`, and the `guesses` check
misfiring on the new envelope schema. A validation layer that only catches other
people's bugs is decoration.

---

## 6. Test Evidence

### What runs

| Suite | Location | Result |
|---|---|---|
| Tier-1 unit tests | `main_pipeline_to_run\test_codetruth_fixes.py` | **20/20 pass** |
| Invariant contract | `run_corpus_eval.py` over 74 repositories | **0 failures** |
| Per-engine validation | live pipeline, one real repository per engine | all pass |

### What does not run

`v3\repository_reasoning\tests\` contains **16 files named `test_*.py` that
collect zero pytest tests.** They are manual verification scripts with
`if __name__ == "__main__"` blocks, not test functions.

Three of them additionally fail to import:
`test_bench_against_networkx.py`, `test_bench_crosscodeeval.py`,
`test_java_type_inference.py` — wrong module paths, pre-existing.

**This directory is not evidence for Module 3 and must not be cited as such.**
A folder named `tests\` that runs nothing is a claim the codebase makes about
itself and cannot support.

---

## 7. Architecture

Module 3's per-language reasoning is **additive**. It imports the frozen Module 2
adapters and the frozen Python Module 3 pipeline. It edits neither.

```
run_codetruth.py
        │
        ├── python  → frozen module3_pipeline.run_module3()
        ├── java    → bridge.answer()
        ├── js      → bridge.answer()
        ├── c_cpp   → bridge.answer()
        ├── go      → bridge.advanced_reparsed()   (caller-aware re-parse)
        ├── csharp  → bridge.advanced_reparsed()   (caller-aware re-parse)
        ├── sql     → bridge.sql_lineage()         (data lineage, not a call graph)
        └── rust    → NOT_IMPLEMENTED              (declared stub, zero capabilities)
```

`language_adapter_bridge.py` normalizes the frozen adapters from outside:
tolerates `language_name` vs `language`, imports each adapter independently so
one missing dependency cannot break the rest, and provides evidence-based
`classify_files()` file counting.

---

## 8. Language Routing

Routing selects the dominant language by **actual file count**, in order:

1. Module 1's `language_composition` — if populated
2. **`bridge.classify_files()`** — counts real files on disk (primary source)
3. `DOMAIN_TO_LANGUAGE` — **last resort only**, flagged low-confidence, forces `REVIEW_REQUIRED`

Every result carries provenance:

```json
"language_selection": {
  "language": "python",
  "source": "bridge_classify_files",
  "confidence": "high",
  "files_provided": 4609
}
```

### Corroboration

Across 20 non-Python routings, Module 1's independently-detected framework
agrees with Module 2's file-count language in **18 cases**. Two exceptions
(`ccxt` → javascript; `vscode` framework detected as "React" though it is
TypeScript) are Module 1 accuracy data points, not routing failures.

### The near-parity limitation

PyTorch: **4,733 C/C++ files vs 4,609 Python — a 1.3% margin.** A 124-file
difference decides between a 143,436-function Python analysis carrying
`guesses: 0` and exact provenance, and a 17,625-function C/C++ analysis carrying
neither.

**All 74 corpus repositories have decisive margins.** PyTorch does not. Routing
near parity should be treated as unreliable, and an explicit language override
is recommended for such repositories.

---

## 9. What Module 3 Does NOT Cover

| Capability | Where |
|---|---|
| Decorator / framework-hook detection | Future — static structural evidence |
| Runtime behaviour · observed execution | Future — behavioral evidence module (workload-scoped) |
| Sound symbolic analysis | Future — bounded property classes only |
| Data-flow / taint analysis | Future |
| Cross-language resolution (Python ↔ C++) | Future |
| Root-cause / failure diagnosis | Future |

**Module 3 scopes an issue. It does not diagnose one.** It produces a verified
in-repo dependency map plus an explicit map of what it cannot see. Root-cause
analysis is a different module class and does not exist.

---

## 10. Honest Claim

> **Module 3 provides language-aware reasoning across the supported languages,
> with Python fully validated and the remaining language routes validated
> according to their current implementation depth.**

Backed by 74 real repositories · three engine kinds each exercised in the live
pipeline · zero contract violations · zero language disagreements.

**Not claimed:** depth equivalence between Python and any other language;
multi-repo UAT for any non-Python route; complete caller sets for any language;
any knowledge of runtime behaviour.

---

## 11. Freeze Prerequisites

| # | Item | Status |
|---|---|---|
| 1 | 74-repo corpus, new routing + M3 dispatch | ✅ 0 invariant failures |
| 2 | elasticsearch after recursion fix | ✅ 22,101 files → 134,037 functions |
| 3 | C# + SQL through the live pipeline | ✅ both COMPLETE |
| 4 | Invariant CSV, no new failures | ✅ 0 |
| 5 | Corpus re-run after `_scratch\` cleanup | ⏳ **outstanding** |

**Item 5 gates the freeze.** Approximately 30 files were moved out of
`repository_reasoning\` into `_scratch\`. Nothing has verified that none were
load-bearing. "They were only debug scripts" is a hypothesis until the corpus
reproduces **71 / 3 / 0**.

---

*CodeTruth Agent V3 — github.com/Zeeshan78699/CodeTruthAgent*
*AI imagines. CodeTruth checks. Nature tests. Humans decide.*
