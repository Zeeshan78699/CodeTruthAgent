# Module 3 — Design Decisions

**Date:** 2026-07-10

Each decision records what was chosen, what was rejected, and **why the rejected
option was tempting**. A decision log that omits the tempting wrong answer teaches
nothing.

---

## D3-001 — Additive dispatch, not a Module 2 edit

**Decision:** Module 3 imports the frozen Module 2 adapters and normalizes them
from outside. It edits none of them.

**Rejected:** patching the Go and C# adapters to record callers.

**Why the rejection was hard:** the adapters are where the bug actually is. Go's
adapter reads 11,437 files and produces nothing usable, and Module 3 then reads
them again. The workaround duplicates work.

**Why additive won:** Module 2 is frozen. Breaking a freeze requires
measure → fix → UAT → re-freeze. The re-parse delivers the capability now, at the
cost of duplicate parsing, without invalidating Module 2's corpus evidence.

**Consequence:** `go_call_graph.py` and `csharp_call_graph.py` exist. They are a
workaround, and the roadmap says so.

---

## D3-002 — A common envelope; no borrowed vocabulary

**Decision:** every non-Python language emits
`{language, engine, status, capabilities, truth_boundary{scope, limitations}}`.

**Rejected:** forcing all languages into Python's Module 3 JSON shape.

**Why the rejection matters most:** Python's block contains
`truth_boundary.guesses: 0` and `edge_provenance`. Those are Phase 3A/3B
*measurements*. Emitting `guesses: 0` for Java would assert a guarantee the Java
engine never computed — a fabrication, in the schema, in a tool built to refuse
fabrication.

**The envelope makes it impossible by construction.** Java's block has no
`guesses` key because Java's engine never produced one.

**Enforced by:** `INV_C_007` — a block reporting `ENGINE_ERROR` or
`NOT_IMPLEMENTED` must claim `capabilities == []`.

---

## D3-003 — The completeness guard is paradigm-aware

**Decision:** `COMPLETE` requires primary artifacts **appropriate to the selected
language's paradigm**.

```
graph languages : functions > 0  OR  call_graph_edges > 0  OR  an M3 reasoning index
sql             : objects / reads / writes / data_flows > 0
```

**Rejected:** `COMPLETE requires functions > 0`.

**Why:** SQL has no functions. It has tables, reads, writes, and lineage. A
`functions > 0` rule would falsely fail a genuine SQL repository.

**Second rejection:** requiring Module 2 artifacts only.

**Why:** Go's Module 2 adapter yields **0 functions** while Module 3's re-parse
yields 33,428. The guard accepts either source of evidence. Without that, every
Go and C# repository would hold at `REVIEW_REQUIRED` despite having a working
call graph.

**What the guard does not catch:** a wrong-language analysis producing *real*
artifacts. odoo's SQL analysis found 17 tables. rust's JavaScript analysis found
real functions. Both had substance.

> The guard checks whether substance exists. It does not check whether the
> substance is about the right thing.

That gap is covered by D3-005.

---

## D3-004 — Language routing by evidence, with the guess demoted

**Decision:** language is selected in this order.

```
1. Module 1's language_composition        — if populated
2. bridge.classify_files()                — counts real files on disk  ← primary
3. DOMAIN_TO_LANGUAGE                     — last resort, low-confidence, forces REVIEW_REQUIRED
```

Every result carries `language_selection: {language, source, confidence}`.

**Rejected:** deleting `DOMAIN_TO_LANGUAGE`.

**Why:** file-composition detection **can** fail. odoo's `language_composition`
returned `{}`. Deleting the fallback leaves nothing for that case.

**The bug was never that it existed.** The bug was that it ran **first**,
**silently**, with `"ERP_SYSTEM": "sql"` hardcoded — routing odoo's 8,485 Python
files to its 77 SQL files and reporting `COMPLETE`.

> A guess was hardcoded inside the guess-refusing tool.

Now it runs last, is labelled low-confidence, and cannot silently complete.

---

## D3-005 — The language-review flag is a fact, not a verdict

**Decision:** when Module 1's framework and Module 2's language name *different
languages*, record `language_review_required = Yes`. Deliver no judgment.

**Rejected:** deciding which module is right, or maintaining a list of
"unsupported" languages.

**Why:** a mismatch may be entirely expected — a mixed-language repository, or
Python tooling inside a non-Python project. Asserting a verdict from a
disagreement would be inference presented as measurement.

**What the flag has caught:** both wrong-language-`COMPLETE` bugs.

| Repository | Reported | Actually analyzed |
|---|---|---|
| odoo | `COMPLETE` | 77 SQL files; 8,485 Python ignored |
| rust | `COMPLETE` | 190 JavaScript files; 36,176 Rust ignored |

Neither was caught by the completeness guard. Both analyses produced real
artifacts.

**Open design question, deliberately unresolved:** should a genuine M1/M2
disagreement **force** `REVIEW_REQUIRED` rather than annotate a CSV column?
Two instances suggest yes. **Measure first** — how many repositories would flip,
and are any legitimate mixed-language cases?

---

## D3-006 — A stub must be selected so that it can refuse

**Decision:** every language with a registered adapter — **including stubs** —
participates in routing.

**Rejected:** excluding rust from `adapter_langs` because it is unimplemented.

**Why the rejection was tempting and wrong:** "don't route to a stub" sounds
prudent. It is not. Excluding rust filtered its 36,176 files out of the count,
leaving JavaScript's 190 as the maximum. The pipeline reported `COMPLETE` on a
Rust repository whose language it never touched.

> Excluding a stub does not prevent a wrong answer. It produces one.

**Correct behaviour:** rust wins on file count → routes to the stub → the engine
reports `NOT_IMPLEMENTED` with zero capabilities → the pipeline holds at
`REVIEW_REQUIRED` and explains:

> *This repository is predominantly rust (36,176 rust files), identified from
> actual file composition. CodeTruth does not implement rust analysis: its
> adapter is a declared stub. No analysis was performed and no findings are
> claimed. This is a known capability boundary, not a failure to parse.*

---

## D3-007 — `get_adapter` raises rather than substitutes

**Decision:** an unknown language raises `ValueError`. It never falls back to
another language's adapter.

**Rejected:** `else: return PythonAdapter()`.

**Why:** that `else` existed. `get_adapter("java")` returned `PythonAdapter`,
which parsed zero `.java` files. spring-boot, nginx, react, and ui5-webcomponents
were being routed correctly and then handed the wrong parser.

**Cost of the decision:** a language the bridge can classify but `get_adapter`
does not know now hard-errors as `M2_ERROR`. That is the correct trade — an
honest loud failure over a silent wrong analysis.

**Residual risk:** `adapter_langs` and `list_languages()` are two hardcoded sets
that must agree, with nothing enforcing it. This produced the rust bug. **Fix by
derivation.**

---

## D3-008 — An honestly-reported error is contract-compliant

**Decision:** `M2_ERROR` and `M3_ERROR`, carrying a real reason and claiming no
findings, **pass** the invariant contract.

**Rejected:** treating any non-`COMPLETE` status as a contract failure.

**Why:** elasticsearch's `RecursionError` was the tool failing loudly and
fabricating nothing. That is the Truth Boundary working. It is a **robustness
issue to log** — not a violation.

Recording it as a failure would create pressure to suppress errors rather than
report them.

---

## D3-009 — Recursion limit raised, always restored

**Decision:** `_deep_recursion(20000)` wraps the Module 2 scan and the Module 3
bridge engines. The original limit is restored in a `finally` block — including
when the scan raises.

**Why the restore matters more than the raise:** without it, one repository that
errors would leave the interpreter's recursion limit elevated for every
subsequent repository in a corpus run. Results would become non-reproducible in a
way that is very difficult to notice.

**Honest limit:** this raises the ceiling on *catchable* recursion. A genuinely
pathological file can now exhaust the C stack rather than raise a clean
`RecursionError`. **20,000 is a chosen number, not a measured one.** If a
repository exceeds it, measure the actual depth rather than doubling again.

---

## D3-010 — Guided diagnosis states only what was verified

**Decision:** when a target is not in the call index, report the *evidence* —
which modules the index actually contains — and the next action.

**Rejected wording:** *"This usually means the method belongs to a different
repository."*

**Why:** CodeTruth verified that the module is **not in the index**. It did not
verify *why*. The module could belong to another repository, or be a typo, or
have failed to parse. Asserting the cause claims more than was checked.

**Shipped wording:** *"The target's top-level module `memory_db` does not appear
in the verified call index for this repository. Verify that you selected the
correct repository or target method."*

The Truth Boundary applies to error messages, not only to findings.

---

## D3-011 — Dead-code candidates are candidates

**Decision:** the dead-code report is labelled `CANDIDATES`. Two evidence-backed
buckets:

| Bucket | Evidence |
|---|---|
| Module entry script | node is a `.<module>` execution entry |
| Investigation candidate | no verified inbound internal caller |

**Rejected:** a "Framework entry point" bucket for route handlers.

**Why:** the verified call graph carries **no decorator metadata**. Labelling a
function a route would be a guess. The report says so:

> Richer labels — Framework entry point (e.g. `@app.route` routes) and CLI entry
> point — are not inferred here: the verified call graph carries no decorator
> metadata, so labelling a route would be a guess.

**Consequence:** Flask reports 125 investigation candidates, most of which are
live public API, WSGI entry points, and pytest fixtures. That is noisy **and
honest**. Decorator detection would fix it — as `structural_evidence`, never as
`proven_caller`.

---

## D3-012 — Every result is a floor

**Decision:** all reports state that verified callers are a lower bound.

**Why this is not a caveat but the product:** `AppContext.push` shows **one**
verified caller. It is invoked by every `with app.app_context():` in every Flask
application — through the context-manager protocol, from outside the repository.

A tool reporting *"1 caller, LOW risk"* without that boundary would be
confidently wrong on exactly the code where confidence hurts most.

**For security patches this is safety-critical.** Authentication methods are
decorator- and middleware-invoked. A low verified-caller count on `validate_token`
means *"CodeTruth cannot see the callers,"* never *"few dependencies."*

---

## Rejected Across the Board

| Proposal | Why rejected |
|---|---|
| Split `<external>` into "internal cross-module" vs "third-party" | The tag is assigned by the frozen resolver and means *"not resolved to a verified in-repo node."* Splitting it would fabricate a distinction the graph does not support. |
| Override Module 1's classifier in the report layer | Would print labels Module 1 never produced. |
| Guess the Domain axis | Shown as *"not yet classified"* instead. An unclassified field is more valuable than a wrongly-classified one. |
| Hardcode a Python preference for near-parity routing | Would be choosing a rule *after seeing the answer we wanted*. |
| Skip `REVIEW_REQUIRED` repositories in the invariant suite | `REVIEW_REQUIRED` is a valid scenario with correct behaviour. It must **pass**, not be skipped. |
| Claim "8 languages supported" | Seven reason. One refuses. Depth is unequal. |
| Call the future runtime module "absolute behavioral analysis" | Undecidable for arbitrary programs. It observes one workload. |

---

*CodeTruth Agent V3 — github.com/Zeeshan78699/CodeTruthAgent*
*AI imagines. CodeTruth checks. Nature tests. Humans decide.*
