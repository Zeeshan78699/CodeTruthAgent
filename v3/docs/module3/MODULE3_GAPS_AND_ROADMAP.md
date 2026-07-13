# Module 3 — Gaps and Roadmap

**Date:** 2026-07-10
**Standard:** Every gap below is measured, not suspected. Nothing is listed as a
gap because it "seems likely."

---

## 1. Gaps Inside Module 3

### 1.1 No multi-repo UAT for non-Python languages

| Language | Validated on |
|---|---|
| Python | 76-repo corpus, full Phase 3A/3B |
| Java | elasticsearch, spring-boot |
| Go | Go compiler |
| C# | ccxt/cs |
| C/C++ | nginx |
| JavaScript | react |
| SQL | camel test fixtures |

One real repository each. That is genuine evidence and a genuine limit. Raising
these to Python's confidence tier requires per-language multi-repo evaluation
with the same harness.

**Priority:** medium. The engines work; the confidence claim is what's thin.

---

### 1.2 C/C++ under-extraction

```
nginx : 401 C files scanned → 15 functions
```

The bridge engine finds more when invoked directly. Cause not investigated.
Fifteen functions from 401 files of nginx is implausible.

**Priority:** high — it silently produces a near-empty graph that still passes
the completeness guard.

---

### 1.3 No deep resolution outside Python

Python's Module 3 performs Phase 3A attribute-call resolution, C3 MRO
linearization, `super()` chain resolution, local and imported receiver typing,
edge provenance accounting, and guess counting.

The bridge engines perform **none of these**. They build a call graph and expose
a query surface. The envelope declares this; closing it is substantial work.

**Priority:** low. The envelope is honest about it, and the call graph is what
most queries need.

---

### 1.4 Go and C# require duplicate parsing

The frozen Go adapter reads 11,437 files and produces nothing usable. Module 3
then reads them again to recover callers.

**Root cause is in Module 2** (see §2.1). Module 3's re-parse is a workaround, not
a design.

**Priority:** deferred — fixing it means breaking Module 2's freeze.

---

### 1.5 Near-parity language routing is unreliable

```
PyTorch : 4,733 C/C++ files
          4,609 Python files
          ──────────────────
          124 files — a 1.3% margin
```

That margin decides between a **143,436-function Python analysis** carrying
`guesses: 0` and exact edge provenance, and a **17,625-function C/C++ analysis**
carrying neither. Routing away from Python silently drops the strongest guarantee
CodeTruth makes, and nothing in the report signals that the decision was close.

**All 74 corpus repositories have decisive margins.** PyTorch does not.

**What not to do:** hardcode a Python preference, or weight by lines of code, or
add a "primary language" heuristic. Each replaces one rule with another chosen
*after seeing the answer we wanted*.

**What the evidence supports:** the router should know when it is uncertain, as
Module 1's gate does. A near-parity margin is not a confident selection.

**Before changing the rule:** measure the top-two margin across all repositories.
If every corpus repo exceeds 10× except PyTorch, the rule is sound and PyTorch
needs a manual override — not a new threshold.

**Priority:** high, but **measure first**.

---

### 1.6 `adapter_langs` and `list_languages()` can drift

`detect_language_meta` hardcodes the set of routable languages. The bridge
independently knows its own. Nothing enforces agreement.

Omitting `rust` from that set caused a 36,176-file Rust repository to be analyzed
as 190 JavaScript files and reported `COMPLETE`. The two sets agree today. They
will not agree the next time a language is added.

**Fix:** derive `adapter_langs` from `list_languages()`. Small. Touches routing,
so it needs its own verification run.

**Priority:** high — closes the bug *class*, not just the instance.

---

### 1.7 `repository_reasoning\tests\` runs nothing

Sixteen files named `test_*.py`, in a directory named `tests\`, collecting **zero
pytest tests**. They are manual scripts with `if __name__ == "__main__"` blocks.

Three additionally fail to import: `test_bench_against_networkx.py`,
`test_bench_crosscodeeval.py`, `test_java_type_inference.py` — wrong module paths.

A folder called `tests\` that runs nothing is a claim the codebase makes about
itself and cannot support. It reads, to any observer, as *"Module 3 is tested."*

**Fix:** convert to real pytest tests, or rename the directory.

**Priority:** high. This is the same failure shape as `pipeline.py` (looks like
the pipeline, unimported) and the Go adapter's ✅ Validated mark (looks proven,
produces nothing).

---

### 1.8 Rust adapter is a stub

Registers `.rs` files so they are counted. `scan()` returns `empty_report()`.
`is_implemented()` returns `False`. The pipeline selects it and it refuses
honestly.

Implementing it requires a **non-Python parsing toolchain** — `syn` via a Rust
helper binary, or tree-sitter-rust. Every other adapter is self-contained Python.
The stub's own docstring contains the implementation specification.

**Priority:** low, and it is a **new capability**, not a bug fix. Build it when
corpus data shows Rust repositories matter enough to justify a new toolchain.

---

## 2. Gaps That Live in Module 2

Module 3 works around these. The root fixes require a Module 2 freeze break —
measure → fix → UAT → re-freeze.

### 2.1 Go and C# adapters drop callers

Both record a call's target without its enclosing function. No directed
`{caller → callee}` edge is constructible from their output.

```
go     : 11,437 files → 0 functions, 0 edges
csharp :               → 0 functions
```

This is why `go_call_graph.py` and `csharp_call_graph.py` exist.

**Note:** `MODULE2_VALIDATION_REPORT.md` marks both adapters `✅ Validated` with
30.43% and 86.49% resolution respectively. Those figures come from isolated
fixtures. In the live pipeline both produce zero. The fixture tested something
the pipeline does not invoke.

---

### 2.2 javalang exceeds Python's recursion limit

elasticsearch's 22,101 Java files abort the entire scan with `RecursionError`.

**Mitigated** by a scoped pipeline-level guard — `_deep_recursion(20000)`, always
restored, including on exception. **Not fixed at source.** Raising the ceiling
means a pathological file can now exhaust the C stack rather than raise a
catchable error.

---

### 2.3 Adapter output shapes differ

Python's adapter emits `functions` and `files_scanned` counts. Java, C/C++, and
JavaScript emit only `function_graph` and `call_graph` dictionaries.

`_m2_summary` normalizes this at the pipeline layer. Until 2026-07-09 it did not,
and java/c_cpp reported `functions: 0` while holding 301.

---

### 2.4 src-layout resolution

In-repo cross-module calls are tagged `<external>` under `src/` layouts. The
resolver cannot confirm they are in-repo, so it declines — correctly. The tag
means *"not resolved to a verified in-repo node,"* not *"third-party."*

---

### 2.5 No decorator or framework-hook detection

The call graph carries no decorator metadata. Consequences:

- Auth methods invoked by `@requires_auth` show few or zero verified callers
- Route handlers appear as dead-code candidates
- Flask's dead-code report lists 125 "investigation candidates," most of which
  are live public API, WSGI entry points, and pytest fixtures

**This blocks the security-patch use case** (`TC_M3_003`) and inflates every
dead-code report.

---

## 3. Roadmap

Ordered by evidence, not by ambition.

### Immediate — verification, no new code

| # | Item |
|---|---|
| 1 | Re-run the corpus after the `_scratch\` cleanup. Expect **71 / 3 / 0**. **This gates the freeze.** |
| 2 | Freeze Module 3 against the verified, cleaned tree |

### Next — small, evidence-backed

| # | Item | Why |
|---|---|---|
| 3 | Derive `adapter_langs` from `list_languages()` | Closes the drift class that produced the rust bug |
| 4 | Convert or rename `repository_reasoning\tests\` | A tests directory that runs nothing is a false claim |
| 5 | Fix three broken test imports | Pre-existing |
| 6 | Investigate C/C++ under-extraction (nginx: 401 → 15) | Silently produces near-empty graphs |
| 7 | Measure top-two language margins across the corpus | Decide the near-parity rule **with numbers visible** |

### Then — Module 1 accuracy

Blind-label `module1_evaluation.csv` → build the failure matrix → rank by
frequency × engineering impact → fix the top item only → re-run the identical
corpus → compare, **including calibration** → freeze.

The matrix must distinguish **wrong-confident** (dangerous) from **honest
abstention** (often correct) from **correct**. A fix that raises accuracy while
worsening calibration is a regression.

Approach: an **additive extension layer**. Module 1 stays frozen.

### Then — Module 4 candidates, in dependency order

| # | Module | Reads | Proves |
|---|---|---|---|
| 1 | **Decorator / base-class detection** | decorators, base class names | **that those decorators and bases exist** — still static |
| 2 | Behavioral evidence (runtime tracing) | actual execution | observed edges, **workload-scoped** |
| 3 | Sound symbolic analysis | abstract semantics | sound properties for bounded classes, or `unknown` |
| 4 | Data-flow / taint analysis | value propagation | — |
| 5 | Cross-language resolution (Python ↔ C++) | binding boundary | — |
| 6 | Root-cause / failure diagnosis | — | — |

---

## 4. Boundaries That Are Not Gaps

These are limits of what any tool can do. They will not be closed.

**"Absolute behavioral analysis" of arbitrary programs is undecidable.** Rice's
theorem. No module, no architecture, no amount of engineering reaches it.

What is achievable, and what each layer honestly gives:

| Layer | Claim | Label |
|---|---|---|
| Static call graph (today) | this edge exists in the code | `verified_static` |
| Decorator / base-class | this decorator is written here | `structural_evidence` |
| Runtime tracing | this edge executed under workload X | `observed_runtime(workload=X)` |
| Sound symbolic | this property holds on every execution | `proven_sound` \| `unknown` |

**These labels must never merge into a single confidence number.** They answer
different questions with different warrants. A dead-code report showing all four,
unmerged, is more useful *and* more honest than any weighted score.

**Decorator detection is not behavioral.** `@app.route` is a token in the AST.
That the framework *calls* the decorated function is an inference, not a proof.
The correct label is *"carries a route-shaped decorator; invocation not
verified"* — never *"framework entry point."*

**Runtime tracing is not absolute.** It observes one workload. Absence of
observation is not proof of absence. Untested code is not dead code.

---

## 5. What the Corpus Taught

Three bugs found this cycle. All three reported success.

```
odoo    : COMPLETE / APPROVED, 0 functions
          (analyzed 77 SQL files; ignored 8,485 Python)

rust    : COMPLETE, 190 JavaScript files out of 36,176 Rust

pytorch : COMPLETE, in the wrong language, by 124 files
```

None was caught by asking *"did it finish?"* All were caught by asking
**"is this substance about the right thing?"**

And the odoo root cause was a **hardcoded guess inside the guess-refusing tool**:

```python
DOMAIN_TO_LANGUAGE = {"ERP_SYSTEM": "sql", ...}
```

It looked harmless. It sat unexamined for weeks — arguably because Module 1's
documentation reported `10/10` on application-type detection, which made trusting
its output to select a language look safe.

**A validation layer that only catches other people's bugs is decoration.**
During this cycle the invariant suite caught two bugs introduced minutes earlier
by its own author.

---

*CodeTruth Agent V3 — github.com/Zeeshan78699/CodeTruthAgent*
*AI imagines. CodeTruth checks. Nature tests. Humans decide.*
