# CodeTruth V3 — Module Integration Guide

**How Module 1, Module 2, and Module 3 compose into one pipeline.**

**Date:** 2026-07-10
**Canonical implementation:** `v3\run_codetruth.py` → `run_platform()`
**Every number in this document was measured. Nothing is illustrative.**

---

## 1. The Cycle

```
                         repository path
                                │
                                ▼
                      ┌───────────────────┐
                      │    PREFLIGHT      │  venv guard
                      └─────────┬─────────┘
                                │  no virtualenv inside the repo
                                ▼
                      ┌───────────────────┐
                      │     MODULE 1      │  Repository Cognition   [FROZEN]
                      │                   │
                      │  reads : manifests, framework signatures, file tree
                      │  emits : application_type, framework, architecture,
                      │          confidence, language_composition, GATE
                      └─────────┬─────────┘
                                │
                    gate == APPROVED ?  ──── no ──▶  REVIEW_REQUIRED / BLOCKED
                                │                     no findings generated
                               yes                    (--force overrides, discloses)
                                │
                                ▼
                      ┌───────────────────┐
                      │  LANGUAGE ROUTING │   ← the M1→M2 boundary
                      │                   │
                      │  1. M1.language_composition      (if populated)
                      │  2. bridge.classify_files()      (real file counts)  ← primary
                      │  3. DOMAIN_TO_LANGUAGE           (last resort, flagged)
                      │
                      │  emits : language, source, confidence, files_provided
                      └─────────┬─────────┘
                                │
                                ▼
                      ┌───────────────────┐
                      │     MODULE 2      │  Repository Graph       [FROZEN]
                      │                   │
                      │  reads : the file list for the selected language
                      │  emits : function_graph, class_graph, call_graph,
                      │          unresolved, governance_gate
                      └─────────┬─────────┘
                                │
                                ▼
                      ┌───────────────────┐
                      │     MODULE 3      │  Repository Reasoning
                      │                   │
                      │  python  → frozen module3_pipeline  (Phase 3A/3B)
                      │  java/js/c_cpp    → bridge.answer
                      │  go/csharp        → bridge.advanced_reparsed
                      │  sql              → bridge.sql_lineage
                      │  rust             → NOT_IMPLEMENTED
                      └─────────┬─────────┘
                                │
                                ▼
                      ┌───────────────────┐
                      │   GOVERNANCE      │  completeness guard
                      │                   │
                      │  COMPLETE requires primary artifacts appropriate to the
                      │  selected language's paradigm — from M2 OR from M3.
                      └─────────┬─────────┘
                                │
                        COMPLETE  |  REVIEW_REQUIRED
```

---

## 2. Data Contracts at Each Boundary

### PREFLIGHT → M1

```python
venvs = _unskippable_venvs(repo_root)   # detects any venv by pyvenv.cfg marker
```

A virtual environment inside the repository would cause Module 2 to walk
installed dependencies as source. The guard detects it by the `pyvenv.cfg`
marker — not by directory name, so `.venv`, `venv`, `myenv`, and `env` are all
caught — and halts before Module 1 runs.

### M1 → ROUTING

```python
summary, m1_core, gate = _m1(repo_root)
```

```json
{"application_type": "WEB_APPLICATION",
 "framework": "Flask",
 "architecture": "LIBRARY",
 "confidence": 1.0,
 "gate": "APPROVED"}
```

Plus, on `m1_core`, the field that matters most to routing:

```python
m1_core.language_composition   # {} on some repositories — including odoo
```

**The gate is checked here.** If it is not `APPROVED`, the pipeline returns
`REVIEW_REQUIRED` and generates no findings. `--force` proceeds under explicit
human override and the report discloses that it did.

### ROUTING → M2

```python
language, source, confidence = detect_language_meta(m1_core, repo_root)
files = _files_for_language(repo_root, language)
adapter = get_adapter(language)
```

```json
"language_selection": {
  "language": "python",
  "source": "bridge_classify_files",
  "confidence": "high",
  "files_provided": 4609
}
```

Provenance travels with the result. A consumer can always see *how* the language
was chosen.

**`get_adapter` raises on an unknown language.** It never substitutes another
language's adapter. That `else: return PythonAdapter()` existed until 2026-07-09
and silently handed `.java` files to the Python parser.

### M2 → M3

```python
with _deep_recursion(20000):
    scan = adapter.scan(repo_root=repo_root, file_paths=files)
summary = _m2_summary(scan, language, files_provided=len(files))
```

Adapter output shapes **differ by language** — a fact the summary layer
normalizes:

| Adapter | Emits |
|---|---|
| Python | `function_graph`, `class_graph`, `call_graph`, `unresolved`, `files_scanned` |
| Java, C/C++, JavaScript | `function_graph`, `class_graph`, `call_graph`, `unresolved` — **no `files_scanned`** |
| Go, C# | `call_graph` **without enclosing callers** |
| SQL | `tables`, `views`, `procedures`, `edge_counts` — no functions at all |

`_deep_recursion(20000)` wraps the scan because javalang recurses per AST node
and exceeds Python's default 1,000-frame cap on elasticsearch-scale Java. The
limit is **always restored**, including on exception — otherwise one failing
repository would leave it raised for every subsequent repository in a corpus run.

### M3 → GOVERNANCE

```python
if language == "python":
    m3 = run_module3(repo_root, m2_scan=scan, m1_result=m1_summary)   # frozen
else:
    m3 = _module3_for_language(repo_root, language)                   # bridge dispatch
```

Python's Module 3 consumes M2's scan directly. **Go and C# do not** — their
adapters dropped the caller, so Module 3 re-parses the source itself.

---

## 3. The Governance Guard

`COMPLETE` requires **primary artifacts appropriate to the selected language's
paradigm**, from either Module 2 *or* Module 3.

```python
m2_ok = _has_primary_artifacts(language, m2_summary, m2_scan)
m3_ok = (m3["status"] == "COMPLETE" and
         (m3.get("graph", {}).get("functions_in_index", 0) > 0
          or any(v > 0 for v in m3.get("lineage", {}).values())))

if not (m2_ok or m3_ok):
    status = "REVIEW_REQUIRED"      # no findings claimed
```

| Language class | Requires |
|---|---|
| Graph languages | `functions > 0` **or** `call_graph_edges > 0` **or** an M3 reasoning index |
| SQL | `objects` / `reads` / `writes` / `data_flows` > 0 |

**Why "M2 *or* M3":** Go's Module 2 adapter yields **0 functions**. Its Module 3
re-parse yields **33,428**. Requiring M2 artifacts alone would hold every Go
repository at `REVIEW_REQUIRED` despite a working call graph.

**What the guard does not catch:** a *wrong-language* analysis that produces
*real* artifacts. See §5.

---

## 4. Four Traced Runs

Real output. Nothing simplified.

### 4.1 flask — the straightforward path

```
PREFLIGHT   no venv
M1          WEB_APPLICATION · Flask · LIBRARY · confidence 1.0 · APPROVED
ROUTING     python · bridge_classify_files · high · 83 files
M2          PythonAdapter → 83 files · 1,460 functions · 160 classes · 686 edges
M3          frozen module3_pipeline
            attribute calls resolved: 18 · guesses: 0
            edge_provenance: 686 + 11 = 697 ✓
GOVERNANCE  m2_artifacts: True → COMPLETE
```

Note **`architecture: LIBRARY`** while **`application_type: WEB_APPLICATION`**.
Flask is a library. Module 1's architecture axis is right and its role axis is
wrong — at confidence 1.0. This is a known Module 1 defect, not a routing one.

---

### 4.2 go — where Module 3 rescues Module 2

```
M1          COMPILER_TOOLCHAIN · Go · APPROVED
ROUTING     go · bridge_classify_files · high · 11,437 files
M2          GoAdapter → 11,437 files scanned
                        0 functions
                        0 call-graph edges        ← adapter records callees
                                                     without enclosing callers
M3          bridge.advanced_reparsed
            go_call_graph.py re-parses the source, recovering callers by
            brace-depth scope tracking
                        33,428 functions in index
            hotspots:  src.cmd.compile.internal.ssa.Value.reset → 4,878 callers
GOVERNANCE  m2_artifacts: False
            m3_artifacts: True
            may_report_complete: True → COMPLETE
```

**This is the guard and the dispatch working together.** The guard demands
evidence; the dispatch supplies it from whichever layer can actually produce it.

Before Module 3's per-language dispatch existed, this repository reported
`REVIEW_REQUIRED` — correctly, and uselessly.

---

### 4.3 odoo — how the M1→routing boundary failed

**Before 2026-07-09:**

```
M1          ERP_SYSTEM · Odoo · MVC · confidence 1.0 · APPROVED   ← correct!
            language_composition: {}                              ← empty
ROUTING     lang_comp is empty → skip file-count ranking
            fall through to DOMAIN_TO_LANGUAGE["ERP_SYSTEM"] = "sql"
            → language: sql
M2          SQLAdapter → 77 SQL files · 0 functions
M3          skipped (SQL is not a call graph)
GOVERNANCE  (guard did not exist)
STATUS      COMPLETE / APPROVED
```

The repository contains **8,485 Python files** and **5,857 JavaScript files**.
None were read. The report said `COMPLETE`.

**Root cause, confirmed by reading the implementation:**

```python
DOMAIN_TO_LANGUAGE = {"ERP_SYSTEM": "sql", ...}

def detect_language(m1_core):
    lang_comp = getattr(m1_core, "language_composition", {})
    if lang_comp:                                    # ← False. Skipped entirely.
        ...rank by file_count...
    return DOMAIN_TO_LANGUAGE.get(m1_core.application_type, "python")
```

Module 1 was **correct**. `ERP_SYSTEM` is the right label for odoo. The failure
was a hardcoded assumption — *ERP systems are SQL-centric* — sitting in the
router of a tool whose premise is refusing to assume.

**After:**

```
ROUTING     bridge.classify_files() → {python: 8485, javascript: 5857, sql: 77}
            dominant: python · source: bridge_classify_files · high
M2          PythonAdapter → 48,005 functions
STATUS      COMPLETE
```

---

### 4.4 rust — honest refusal

```
M1          COMPILER_TOOLCHAIN · Rust · confidence 0.875 · APPROVED
ROUTING     rust · bridge_classify_files · high · 36,176 files
M2          RustAdapter.scan() → empty_report()      ← declared stub
M3          NOT_IMPLEMENTED · capabilities: []
GOVERNANCE  m2_artifacts: False · m3_artifacts: False
            may_report_complete: False
STATUS      REVIEW_REQUIRED
REASON      "This repository is predominantly rust (36,176 rust files),
             identified from actual file composition. CodeTruth does not
             implement rust analysis: its adapter is a declared stub. No
             analysis was performed and no findings are claimed. This is a
             known capability boundary, not a failure to parse."
```

**Before 2026-07-10**, `rust` was excluded from the routable set — on the
reasoning that a stub should not be routed to. The router therefore filtered out
36,176 Rust files and selected **javascript (190 files)**. The pipeline reported
`COMPLETE`.

> A stub must be **selected** so that it can **refuse**.
> Excluding it does not prevent a wrong answer. It produces one.

---

## 5. The Two Failure Modes, and What Catches Each

| Failure | Example | Caught by |
|---|---|---|
| **Empty result** — routed to a language that finds nothing | rust → stub → 0 artifacts | **Completeness guard** |
| **Wrong-language result with real artifacts** | odoo → 17 SQL tables · rust → 190 JS functions | **Language-review flag** |

The completeness guard checks **whether substance exists**.
It does not check **whether the substance is about the right thing**.

Both odoo and rust produced *real* artifacts in the wrong language. Both passed
the guard. Both were caught by the neutral **language-review flag**, which
records that Module 1's framework and Module 2's language name different
languages — and delivers no verdict.

That flag is a *fact*, not a judgment. A mismatch may be entirely expected in a
mixed-language repository. It says only: **these two modules disagree; look.**

Across the 74-repository corpus, after both fixes: **0 flags.**

---

## 6. What Each Stage Cannot Establish

A stage whose limits are undeclared will eventually be trusted past its evidence.

| Stage | Cannot establish |
|---|---|
| **M1** | domain (not computed) · reliable confidence — a 94-repo held-out evaluation measured accuracy *inversely* correlated with confidence (32% correct at conf 1.0, 77% at 0.5) · `language_composition` is empty on some repositories |
| **ROUTING** | the correct language near parity — PyTorch is 4,733 C/C++ vs 4,609 Python, a **1.3% margin** · which language a *user wants*; it selects by file count |
| **M2** | directed call edges for Go and C# · callers invoked by decorators, middleware, or framework registration · some in-repo cross-module calls under `src/` layouts (tagged `<external>`) |
| **M3** | complete caller sets — every result is a verified in-repo **floor** · runtime behaviour · deep resolution outside Python |

---

## 7. Two Boundaries Worth Understanding

### 7.1 `<external>` does not mean "third-party"

The frozen resolver tags a call `<external>` when it **could not resolve the
target to a verified in-repo node**. That set contains both genuine third-party
calls *and* in-repo calls the resolver could not confirm — `src/` layouts
contribute here.

Splitting it into "internal cross-module" versus "third-party" would fabricate a
distinction the graph does not support. The report says so:

> *Targets marked `<external>` are outside the verified in-repo graph — either
> third-party libraries or in-repo calls the resolver could not confirm.
> CodeTruth does not guess which.*

### 7.2 Every caller count is a floor

`flask.ctx.AppContext.push` shows **one** verified caller: `__enter__`.

It is in reality invoked by every `with app.app_context():` in every application
using Flask — through the context-manager protocol, from outside the analyzed
repository.

**One caller is a proven lower bound, not the complete set.**

For a security patch this is safety-critical. Authentication methods are
decorator- and middleware-invoked. A low verified-caller count on
`validate_token` means *"CodeTruth cannot see the callers"* — never *"few
dependencies."*

---

## 8. Invariants That Hold Across the Whole Cycle

Verified across 74 repositories: **0 failures.**

### Always

```
✅ Status is one of the known honest states
✅ No fabricated evidence
✅ Truth Boundary present
✅ No silent success — a non-COMPLETE run claims no findings
✅ Gate and status are consistent
```

### Per outcome

| Outcome | Invariant |
|---|---|
| `COMPLETE` + Python M3 | `guesses == 0` · `total_edges == module2_edges + local_receiver_added` |
| `COMPLETE` + non-Python | primary artifacts exist (graph or lineage) |
| `REVIEW_REQUIRED` | gate matches status · reason reported · no findings |
| `M2_ERROR` / `M3_ERROR` | honest loud failure with a reason · no findings claimed |
| any envelope | `ENGINE_ERROR` or `NOT_IMPLEMENTED` ⇒ `capabilities == []` |

**`guesses` is checked only when Module 3 *measured* it.** The per-language
envelope carries a `truth_boundary` with `{scope, limitations}` and deliberately
**no** `guesses` key — because `bridge.answer` never computes one. Emitting
`guesses: 0` for Java would assert a guarantee that engine never produced.

---

## 9. The Single-Router Rule

There is exactly **one** implementation of language routing:
`v3\run_codetruth.py :: detect_language_meta()`.

`service.py` imports it. The web application inherits every routing fix for free:

```python
# v3/main_pipeline_to_run/service.py:307
# M1 doesn't emit language directly; derive it the same way the pipeline
from v3.run_codetruth import detect_language
```

A second copy once existed in `main_pipeline_to_run\pipeline.py`. It carried its
own `DOMAIN_TO_LANGUAGE`, its own four-language `adapter_langs`, and the odoo
bug — weeks after the bug had been fixed in the canonical file. **Nothing
imported it, so nothing caught it.**

> Any file that inspects the pipeline may **read** its decisions.
> It may never **make** them.

---

## 10. Running the Cycle

**Production entry point:**

```powershell
python v3\run_codetruth.py <repo> [--json] [--force]
```

**Stage-by-stage review** — shows each module's contribution and boundary:

```powershell
python v3\main_pipeline_to_run\pipeline.py <repo>
python v3\main_pipeline_to_run\pipeline.py --registry     # no repo needed
```

**Contract validation across a corpus:**

```powershell
python run_corpus_eval.py --root "C:\repos\v3" --runner "v3\run_codetruth.py"
```

**Web application** (same router, same modules):

```powershell
cd v3\main_pipeline_to_run
python -m uvicorn app:app --reload --port 8000
```

---

## 11. What the Cycle Produces — and What It Does Not

**Produces:** a deterministic, verified, in-repository dependency map — who
calls what, change impact, dead-code candidates, call chains, rule-based
regression risk — together with an **explicit map of what could not be seen.**

**Does not produce:** a diagnosis. Module 3 reads structure; it does not execute
code. It **scopes** an issue and does not explain it.

Root-cause analysis, runtime behaviour, data-flow tracing, and cross-language
resolution are different module classes. They do not exist.

> *"Analyzed the dependencies"* must never drift into *"analyzed the bug."*

---

*CodeTruth Agent V3 — github.com/Zeeshan78699/CodeTruthAgent*
*AI imagines. CodeTruth checks. Nature tests. Humans decide.*
