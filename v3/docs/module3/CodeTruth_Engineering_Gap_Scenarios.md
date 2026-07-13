# CodeTruth — Engineering Gap Scenarios

**Real situations in which CodeTruth's limits appear, what an engineer sees,
and what they must do about it.**

**Updated:** 2026-07-10
**Every scenario below was observed. None is hypothetical.**

---

## How to Read This Document

Each scenario states:

- **What you see** — the actual output
- **What is really true** — the ground truth
- **The gap** — which limitation produced the discrepancy
- **What you must do** — the engineer's obligation
- **Where the fix lives** — module, and whether it is a bug or a boundary
- **Status** — fixed, open, or *not a gap at all*

Three scenarios (§12–§14) are included **precisely because they are not gaps.**
Distinguishing an honest abstention from a defect is the discipline this whole
project rests on. A tool that never says *"I don't know"* is not more capable.
It is less honest.

---

# PART I — Gaps That Produce a Confidently Wrong Answer

These are the dangerous ones. The report says `COMPLETE` and looks like success.

---

## §1 — The ERP Repository Analyzed as SQL

**Repository:** odoo — 8,485 Python files, 5,857 JavaScript files, 77 SQL files

**What you saw:**
```
Application Type : ERP_SYSTEM
Language         : sql
Files scanned    : 77
Functions        : 0
Status           : COMPLETE / APPROVED
```

**What is really true:** the repository's 8,485 Python files were never opened.

**The gap:** Module 1 emitted an empty `language_composition`. The router fell
through to a hardcoded map:

```python
DOMAIN_TO_LANGUAGE = {"ERP_SYSTEM": "sql", ...}
```

**Module 1 was correct.** `ERP_SYSTEM` is the right label for odoo. The failure
was a hardcoded assumption — *ERP systems are SQL-centric* — built on top of a
right answer.

> A guess was hardcoded inside the guess-refusing tool. It sat unexamined for
> weeks.

**What you must do:** nothing now. **Status: FIXED.** Routing is by real file
count via `bridge.classify_files()`. odoo now reports `python`, 48,005 functions.

**Where the fix lived:** the router, not Module 1. `DOMAIN_TO_LANGUAGE` survives
as a flagged, low-confidence last resort that forces `REVIEW_REQUIRED`.

**Why it went undetected:** the completeness guard did not exist, and Module 1's
documentation reported `10/10` on application-type detection — which made
trusting its output to select a language look safe.

---

## §2 — The Rust Compiler Analyzed as JavaScript

**Repository:** rust — 36,176 `.rs` files, 190 `.js` files

**What you saw:**
```
Language : javascript
Files    : 190
Status   : COMPLETE
```

**The gap:** `rust` was excluded from the routable language set, on the reasoning
that a stub should not be routed to. The router therefore filtered 36,176 files
out of the count, and JavaScript's 190 became the maximum.

> Excluding a stub does not prevent a wrong answer. **It produces one.**
> A stub must be **selected** so that it can **refuse**.

**What you must do:** nothing now. **Status: FIXED.**

```
Status : REVIEW_REQUIRED
Reason : This repository is predominantly rust (36,176 rust files), identified
         from actual file composition. CodeTruth does not implement rust
         analysis: its adapter is a declared stub. No analysis was performed
         and no findings are claimed.
```

---

## §3 — The Two Failure Modes, and Why Only One Is Guarded

Both §1 and §2 passed the completeness guard.

odoo's SQL analysis found **17 tables**. rust's JavaScript analysis found **real
functions**. Both produced genuine artifacts — in the wrong language.

| Failure | Caught by |
|---|---|
| Routed to a language that finds **nothing** | ✅ Completeness guard |
| Routed to the wrong language that finds **something** | ❌ Guard is blind. Caught by the **language-review flag**. |

> The completeness guard checks **whether substance exists**.
> It does not check **whether the substance is about the right thing.**

The language-review flag records a **fact** — Module 1's framework and Module 2's
language name different languages — and delivers **no verdict**. A mismatch may
be entirely expected in a mixed-language repository.

**It has now caught both instances of the most dangerous bug class in the system.**

**Open design question:** should a genuine disagreement **force**
`REVIEW_REQUIRED` rather than annotate a CSV column? Two instances suggest yes.
**Measure first** — how many repositories would flip, and are any legitimate?

**Status: OPEN.** Corpus flags currently: 0.

---

## §4 — PyTorch Routed by a 1.3% Margin

**Repository:** PyTorch

```
c_cpp  : 4,733 files
python : 4,609 files
         ─────────────
         124 files — a 1.3% margin
```

**What you see:** `language: c_cpp` · 17,625 functions

**What you would see if 125 Python files were added:** `language: python` ·
143,436 functions · `guesses: 0` · exact edge provenance.

**The gap:** *dominant language by file count* is evidence-based and correct at
110:1 (odoo) and 190:1 (rust). At 1.03:1 it decides nothing.

And routing away from Python **silently drops the strongest guarantee CodeTruth
makes.** `bridge.answer` for C/C++ emits no `guesses` field — correctly, because
it never computed one. Nothing in the report signals that a weaker guarantee now
applies.

**What you must do:** **check the reported language before trusting the report**
on any mixed repository. Look at `language_selection`:

```json
{"language": "c_cpp", "source": "bridge_classify_files",
 "confidence": "high", "files_provided": 4733}
```

`confidence: high` here means *the file-count source is reliable* — **not** that
the margin was decisive.

**Where the fix lives:** the router. **Status: OPEN — measure first.**

**What not to do:** hardcode a Python preference, or weight by lines of code.
Each replaces one rule with another chosen *after seeing the answer we wanted*.
Measure the top-two margin across all 74 repositories. If every repository
exceeds 10× except PyTorch, the rule is sound and PyTorch needs a manual
override — not a new threshold.

**All 74 corpus repositories have decisive margins.** PyTorch does not.

---

# PART II — Gaps That Produce an Honest but Incomplete Answer

These do not lie. They under-report, and they say so. The danger is a reader who
does not read the boundary.

---

## §5 — One Verified Caller, Thousands in Reality

**Target:** `flask.ctx.AppContext.push`

**What you see:**
```
Verified direct caller(s) : flask.ctx.AppContext.__enter__
Verified impact depth     : 2 call levels
Regression risk           : LOW
Guesses made              : 0
```

**What is really true:** `push` is invoked by **every `with app.app_context():`
in every application using Flask** — through the context-manager protocol, from
outside the analyzed repository.

**The gap:** none. This is the Truth Boundary working exactly as designed. The
report states it:

> These are the verified in-repository impacts. External libraries, plugins,
> runtime dispatch, and dynamic callers are not included and are explicitly
> treated as unknown rather than guessed.

**What you must do:** read *one verified caller* as a **proven lower bound**,
never as *"one dependency."*

**Status: BOUNDARY, not a gap.** It will never be closed by static analysis.

---

## §6 — The Security Patch That Looks Safe

**Scenario:** a CVE in `Authentication.validate_token`. Which callers need
regression testing before you patch?

**What you see:**
```
Verified affected callers : 2
Regression risk           : LOW
```

**What is really true:** `validate_token` is invoked on **every authenticated
request** — through `@requires_auth` decorators, middleware, and the framework's
request pipeline. None of those callers is in the graph.

**The gap:** the call graph carries **no decorator metadata**. Authentication
methods are overwhelmingly decorator- and middleware-invoked, which means the
verified caller set is not merely incomplete — it is *almost entirely missing*
for exactly this class of method.

**What you must do — and this is safety-critical:**

> A low verified-caller count on an auth method means **"CodeTruth cannot see the
> callers."** It never means **"few dependencies."**

Treat the verified callers as the **must-test** set. Treat the Truth Boundary's
external surface as a **must-manually-review** set: grep for decorator usage,
middleware registration, and cross-service callers.

**Do not infer low risk from a low verified-caller count on authentication code.**

**Where the fix lives:** Module 4 — decorator / framework-hook detection.
**Status: BLOCKS `TC_M3_003`.** That test case is written and cannot be run.

---

## §7 — Flask Reports 125 Dead-Code Candidates, Most Are Live

**What you see:** 139 candidates from 421 callable nodes. 99 under `flask`.

**A sample:**
```
flask.app.Flask.__call__                         ← the WSGI entry point
flask.app.Flask.send_static_file                 ← public API
flask.helpers.send_file                          ← public API
flask.sansio.scaffold.Scaffold.route.decorator   ← decorator internals
tests.conftest.app                               ← pytest fixture
tests.conftest.leak_detector                     ← pytest fixture
```

**What is really true:** `Flask.__call__` handles *every HTTP request*. Nothing
in that list is dead.

**The gap:** these functions have no *verified in-repo* caller because they are
invoked by WSGI servers, test runners, and decorator machinery — all outside the
analyzed graph.

**What CodeTruth does right:** it labels them **CANDIDATES**, never **DEAD**.
And it refuses to add a *"framework entry point"* bucket, because the graph
carries no decorator metadata and labelling a route would be a guess:

> Richer labels — Framework entry point (e.g. `@app.route` routes) and CLI entry
> point — are not inferred here: the verified call graph carries no decorator
> metadata, so labelling a route would be a guess. Such candidates remain
> "investigate" until decorator detection is added.

**What you must do:** read every candidate as *"investigate."* Never as
*"delete."*

**Where the fix lives:** Module 4. Decorator detection would move most of these
out of *investigation candidate* and into *carries a framework-shaped decorator;
invocation not verified.*

Note the wording. It would prove the **decorator**, never the **caller**.

**Status: OPEN. Highest-ROI Module 4 item.**

---

## §8 — `<external>` Does Not Mean "Third-Party"

**What you see:**
```
Outgoing dependencies:
    <external>.src.requests.models.Response
```

`requests` calling into its own `models` module — tagged external.

**The gap:** the frozen resolver assigns `<external>` when it **could not resolve
the target to a verified in-repo node.** That set contains genuine third-party
calls *and* in-repo calls it could not confirm. `src/` layouts contribute
heavily.

**What CodeTruth does right:** it refuses to split the category:

> Targets marked `<external>` are outside the verified in-repo graph — either
> third-party libraries or in-repo calls the resolver could not confirm.
> CodeTruth does not guess which.

Splitting it into *"internal cross-module"* versus *"third-party"* would
fabricate a distinction the graph does not support.

**Where the fix lives:** Module 2 — `src/`-layout-aware resolution.
**Status: OPEN, deferred (frozen module).**

---

# PART III — Gaps in the Analysis Engines

---

## §9 — nginx: 401 C Files, 15 Functions

**What you see:**
```
language      : c_cpp
files_scanned : 401
functions     : 15
Status        : COMPLETE
```

**What is really true:** nginx has thousands of functions.

**The gap:** the C/C++ adapter under-extracts. Invoked directly through the
bridge, it finds more (`ngx_iocp_wait_events`, `ngx_iocp_wait_connect`, others).

**Why this is worse than it looks:** 15 functions is *non-zero*, so the
completeness guard passes it and the pipeline reports `COMPLETE`. A near-empty
graph is presented as a successful analysis.

**What you must do:** treat C/C++ function counts as a floor with an unknown
recovery rate. Do not conclude that a C repository is small.

**Where the fix lives:** Module 2 — `c_cpp_adapter`. Cause not yet investigated.
**Status: OPEN. High priority — it silently produces near-empty graphs.**

---

## §10 — Go and C# Produce Zero Functions

**What you see, from Module 2:**
```
go     : 11,437 files scanned →  0 functions,  0 edges
csharp :                      →  0 functions
```

**What Module 3 then produces:**
```
go     : 33,428 functions  (caller-aware re-parse)
csharp :  8,493 functions
```

**The gap:** both adapters record a call's **target without its enclosing
function**. No directed `{caller → callee}` edge is constructible from their
output.

This is why `go_call_graph.py` and `csharp_call_graph.py` exist — Module 3
re-parses the source to recover callers.

**The documentation problem:** `MODULE2_VALIDATION_REPORT.md` marks both adapters
`✅ Validated`, with 30.43% and 86.49% resolution. Those figures come from
isolated fixtures. **In the live pipeline both produce zero.**

> A passing test sat beside a component producing no usable output, for weeks.
> The fixture measured something the pipeline does not invoke.

**What you must do:** nothing. The capability works. Read the ✅ in Module 2's
docs with suspicion until it is corrected.

**Where the fix lives:** Module 2 adapters, at source. Module 3's re-parse is a
**workaround**, and duplicates parsing work — Go's 11,437 files are read twice.

**Status: worked around. Root fix requires a Module 2 freeze break.**

---

## §11 — Elasticsearch Aborts on 22,101 Java Files

**What you saw:**
```
status : M2_ERROR
reason : RecursionError: maximum recursion depth exceeded
```

**The gap:** `javalang` recurses per AST node and exceeds Python's default
1,000-frame cap on large Java sources. The **entire scan** aborted.

**What CodeTruth did right:** it failed **loudly**, named the real cause, and
claimed nothing. `M2_ERROR` with a reason and no findings is
**contract-compliant** — the tool failing honestly, not a Truth Boundary
violation.

**Status: MITIGATED.** A scoped `_deep_recursion(20000)` guard wraps the scan and
the Module 3 bridge engines. The limit is **always restored**, including on
exception — otherwise one failing repository would leave it raised for every
subsequent repository in a corpus run, making results silently irreproducible.

Elasticsearch now analyzes: 22,101 files → 134,037 functions.

**Not fixed at source.** Raising the ceiling means a pathological file can now
exhaust the C stack rather than raise a catchable error. **20,000 is a chosen
number, not a measured one.**

**Where the real fix lives:** Module 2 — the Java adapter's per-file exception
containment.

---

# PART IV — Things That Look Like Gaps and Are Not

---

## §12 — CPython Holds at REVIEW_REQUIRED

**What you see:**
```
repo   : python
gate   : REVIEW_REQUIRED
status : REVIEW_REQUIRED
```

**Why:** Module 1 could not classify CPython's own source tree confidently. The
governance gate held it. No findings were generated.

**This is not a defect.** It is **honest abstention** — the *good* failure mode.

Compare with Flask, which Module 1 classifies as `WEB_APPLICATION` at
**confidence 1.0**, when Flask is a library. That is **wrong-confident** — the
dangerous mode.

Your own 94-repository held-out evaluation measured application-type accuracy at
~51%, with **confidence inversely correlated with correctness**: 32% accurate at
confidence 1.0, 77% at confidence 0.5.

> "Fixing" CPython's abstention would mean teaching Module 1 to be confident
> where it has no signal. That is a **regression**, not an improvement.

**What you must do:** press **Analyze anyway**. The engine analyzes it perfectly.
The gate was uncertain about the *classification*, not the *code*.

**Status: CORRECT BEHAVIOUR.**

---

## §13 — Low Resolution Coverage on PyTorch

**What you see:**
```
attribute calls resolved : 7,979 of 334,960  (2.39%)
guesses                  : 0
Overall health           : SOUND
```

**Why 2.39% is fine:** PyTorch is dominated by dynamic dispatch —
`__torch_function__`, registration tables, tensor dispatch. Most of those calls
**cannot be statically resolved**, and CodeTruth declines each one with a
documented reason.

```
Rating rule: SOUND if guesses == 0 AND uncategorized_declines == 0
```

> Low coverage is a fact about the **code**.
> Zero guesses is a fact about the **tool**.

Health means **analysis integrity**, not resolution coverage. A dynamic framework
with 2% coverage and zero guesses is trustworthy. It is not penalized for the
code being dynamic.

**Status: CORRECT BEHAVIOUR.** And 312,650 + 6,856 = 319,506 — edge provenance
reconciles exactly across 319,506 edges.

---

## §14 — The `torch.compile` Investigation That Cannot Diagnose

**Scenario:** an open PyTorch issue — Dynamo bakes `ProcessGroup` group names
into the FX graph as constants, so ranks in different EP groups produce different
cache keys and cache reuse collapses at 8,192 GPUs.

**What CodeTruth can give you:** a verified Python-side dependency map around
`torch.distributed._functional_collectives.all_to_all_single` and
`torch._dynamo.variables.distributed.ProcessGroupVariable` — who calls them, what
they call, call chains, affected modules.

**What it cannot give you:** *why* the constant gets baked in. That is tracing
behaviour at runtime.

**Three compounding limits:**
1. `_c10d_functional` ops are **natively registered** — those callers are C++
2. Dynamo's dispatch is **heavily dynamic** — expect a sparse verified caller set
3. Much of PyTorch's engine is **C++/CUDA** — outside the analyzed graph entirely

**The sparseness is the finding, not a defect.** A near-empty verified caller
list for `all_to_all_single` is *evidence* that its invocation path is dynamic —
which is precisely *why* the group name leaks into the traced graph.

**How to frame it for a maintainer:**

> Verified Python-side dependency floor around these functions. Dynamo's dispatch
> is heavily dynamic and `_c10d_functional` ops are natively registered — those
> callers are outside the verified graph and flagged as known-unknowns, not
> counted.

**Status: BOUNDARY.** CodeTruth **scopes** the issue. It does not **diagnose** it.

> *"Analyzed the dependencies"* must never drift into *"analyzed the bug."*

---

# PART V — Gaps in the Project, Not the Product

Three artifacts in the repository claim something they cannot support. Each reads
correctly to anyone glancing at it. Each is the same failure shape as a report
that says `COMPLETE` and is wrong.

| Artifact | Looks like | Is |
|---|---|---|
| `main_pipeline_to_run\pipeline.py` | the pipeline | imported by nothing; carries the odoo bug, still runnable |
| `repository_reasoning\tests\` | a test suite | 16 files named `test_*.py`; pytest collects **zero tests** |
| `MODULE2_VALIDATION_REPORT.md` — Go/C# rows | `✅ Validated` | those adapters produce **0 functions** in the live pipeline |
| `MODULE1_CAPABILITY_PROOF.md` | `69/69 correct`, `10/10` | not a held-out evaluation; measured accuracy is ~51% |

**`pipeline.py` still runs.** Point it at odoo today and it prints:

```
Application Type : ERP_SYSTEM
Language         : sql
Files scanned    : 77
Status           : PIPELINE COMPLETE
```

Two green `[OK]` marks over 8,485 unread Python files.

**Where the fix lives:** documentation corrections and file hygiene.
**Status: OPEN.**

---

# Summary Table

| # | Scenario | Class | Status |
|---|---|---|---|
| 1 | odoo → SQL, 0 functions, COMPLETE | wrong-language | ✅ FIXED |
| 2 | rust → JavaScript, COMPLETE | wrong-language | ✅ FIXED |
| 3 | Guard blind to wrong-language-with-artifacts | detection | ⚠️ OPEN — flag exists, is not a gate |
| 4 | PyTorch: 1.3% routing margin | routing | ⚠️ OPEN — measure first |
| 5 | `push`: 1 caller, thousands real | **boundary** | ✅ correct, unfixable |
| 6 | Security patch reads "LOW risk" | decorator detection | 🚫 blocks TC_M3_003 |
| 7 | Flask: 125 candidates, most live | decorator detection | ⚠️ OPEN |
| 8 | `<external>` conflates two things | src-layout | ⚠️ OPEN (Module 2) |
| 9 | nginx: 401 files → 15 functions | c_cpp adapter | ⚠️ OPEN — high priority |
| 10 | Go/C#: 0 functions from Module 2 | adapter design | 🔧 worked around |
| 11 | elasticsearch: RecursionError | robustness | 🩹 mitigated, not fixed |
| 12 | CPython holds at REVIEW_REQUIRED | **honest abstention** | ✅ correct |
| 13 | PyTorch: 2.39% coverage | **dynamic code** | ✅ correct |
| 14 | `torch.compile` cannot be diagnosed | **boundary** | ✅ correct |
| 15 | `pipeline.py`, `tests\`, stale ✅ marks | project hygiene | ⚠️ OPEN |

---

## The Pattern

Three bugs this cycle. **All three reported success.**

```
odoo    : COMPLETE / APPROVED, 0 functions
rust    : COMPLETE, 190 JavaScript files out of 36,176 Rust
pytorch : COMPLETE, in the wrong language, by 124 files
```

None was caught by asking *"did it finish?"*
All were caught by asking **"is this substance about the right thing?"**

And three artifacts in the repository make the same shape of claim: a file that
looks like the pipeline, a directory that looks like tests, a checkmark that
looks like validation. Each reads correctly. **None is.**

> The gap between *a component that works* and *a component that is called* is
> where every one of these lived.

---

*CodeTruth — proves what it can, flags what it can't, never guesses.*
*github.com/Zeeshan78699/CodeTruthAgent*
