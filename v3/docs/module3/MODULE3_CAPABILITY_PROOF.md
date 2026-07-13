# Module 3 — Capability Proof

**CodeTruth Agent V3 — Module 3 — Repository Reasoning**

Concrete evidence for each capability: actual input and actual output, from real
repositories. No synthetic fixtures. No capability appears here that has not run
in the live pipeline.

**Date:** 2026-07-10

---

## 1. Verified Call Chain (Python)

**Input:** `flask` · target `flask.ctx.AppContext.push`

**Output:**

```
Verified direct caller(s):
  flask.ctx.AppContext.__enter__

Verified call chain:
  flask.ctx.AppContext.__enter__()
      -> flask.ctx.AppContext.push()

Outgoing dependencies (target calls these): 2
  flask.ctx.AppContext._get_session   (line 439, self method call)
  flask.ctx.AppContext.match_request  (line 444, self method call)

Verified impact depth: 2 call levels
Regression risk: LOW
Guesses made: 0
```

**Truth Boundary, as emitted:**

> These are the verified in-repository impacts. External libraries, plugins,
> runtime dispatch, and dynamic callers are not included and are explicitly
> treated as unknown rather than guessed.

**Read correctly:** `push` shows **one** verified caller. It is in reality
invoked by every `with app.app_context():` in every application using Flask —
through the context-manager protocol, from outside the analyzed repository. One
caller is a **proven floor**, not the complete set. The report says so.

---

## 2. Refusal to Fabricate (Truth Boundary Demo)

**Input:** `flask` · two methods, same tool, same repository.

| Method | Verified in-repo callers | Verdict |
|---|---|---|
| `flask.app.Flask.dispatch_request` | 1 — `full_dispatch_request` | 🟢 VERIFIED IMPACT |
| `flask.app.Flask.send_static_file` | 0 | 🟡 **KNOWN-UNKNOWN** — not "safe to delete" |

`send_static_file` is public Flask API, invoked by user application code and by
Flask's routing. A naive dead-code tool would see zero callers and report it
removable. It is not.

```
Verified findings : 1
Known-unknowns    : 1
Guesses           : 0
```

Zero callers is reported as *unknown*, never as *unused*.

---

## 3. Cross-Language Reasoning — Go

**Input:** the Go compiler · `advanced_reparsed(repo, "go", "hotspots")`

**Module 2 output:**
```
files_scanned : 11,437
functions     :      0
call_graph    :      0 edges
```
The frozen Go adapter records a call's package but **not its enclosing
function**. No directed edge can be built.

**Module 3 output** — caller recovered by scope tracking:
```json
{"query": "hotspots",
 "most_depended_on": [
   {"node": "src.cmd.compile.internal.ssa.Value.reset",       "callers": 4878},
   {"node": "src.cmd.compile.internal.ssa.int32ToAuxInt",     "callers": 2165},
   {"node": "src.cmd.compile.internal.ssa.auxIntToInt32",     "callers": 2042},
   {"node": "src.cmd.compile.internal.ssa.Value.AddArg2",     "callers": 2030}
 ]}
```

**33,428 functions indexed.** `Value.reset` with 4,878 callers is the Go
compiler's SSA hot-spot — exactly the shape a compiler IR produces.

**Boundary, as declared by the engine:** cross-package calls, interface dispatch,
struct embedding, generics — not modelled. Brace-heuristic parse, no Go AST.

---

## 4. Cross-Language Reasoning — Java

**Input:** `spring-boot` · `answer(repo, "java", "dead-code")`

```json
{"query": "dead_code",
 "candidates": [
   "org.springframework.boot.maven.DockerTests.DockerTests.asDockerConfigurationWithContextConfiguration",
   "org.springframework.boot.maven.RunIntegrationTests.RunIntegrationTests.whenJvmArgumentsAreConfiguredTheyAreAvailableToTheApplication"
 ],
 "label": "CANDIDATES"}
```

Real fully-qualified Java method names, parsed from real Spring Boot source.

Note the candidates are **test methods** — no in-repo caller, because a test
runner invokes them. The same honest pattern as Python's pytest fixtures. The
label is `CANDIDATES`, never `DEAD`.

**At scale:** elasticsearch — 22,101 Java files → 134,037 functions (Module 2) →
30,291-function reasoning index (Module 3).

---

## 5. Cross-Language Reasoning — C/C++

**Input:** `nginx` · `answer(repo, "c_cpp", "dead-code")`

```json
{"query": "dead_code",
 "candidates": ["src.event.ngx_event_connectex.ngx_iocp_wait_events",
                "src.event.ngx_event_connectex.ngx_iocp_wait_connect"],
 "count": 2,
 "label": "CANDIDATES",
 "boundary": "no inbound internal call edge; entry points / framework callbacks / dynamic dispatch may appear here falsely"}
```

Genuine nginx C functions — the `ngx_` prefix and IOCP naming are nginx's own.

**Known limit:** 401 C files yielded only 15 functions in the live pipeline.
The C/C++ adapter under-extracts. Cause not yet investigated.

---

## 6. Cross-Language Reasoning — C#

**Input:** `ccxt/cs` · `advanced_reparsed(repo, "csharp", "hotspots")`

**Module 2:** 0 functions. The C# adapter, like Go's, drops the caller.

**Module 3:**
```json
{"most_depended_on": [
   {"node": "Exchange.add",      "callers": 221},
   {"node": "Exchange.isTrue",   "callers": 202},
   {"node": "binance.isTrue",    "callers": 180},
   {"node": "Exchange.getValue", "callers": 150}
 ]}
```

**8,493 functions indexed.** `Exchange`, `binance`, `gate` are ccxt's exchange
classes.

---

## 7. Data Lineage — SQL

SQL is a different paradigm. It has no call graph.

**Input:** `camel/.../bigquery/src/test/resources/sql` · `sql_lineage(repo, "summary")`

```json
{"counts": {"objects": 0, "tables": 0, "reads": 2, "writes": 2, "calls": 0, "data_flows": 1},
 "boundary": "regex + scope heuristic (no SQL grammar). READ = FROM/JOIN, WRITE = INSERT/UPDATE/DELETE, attributed to the enclosing CREATE object. Dynamic SQL (EXECUTE IMMEDIATE), CTEs, and dialect-specific constructs are not fully modelled."}
```

The completeness guard accepts `reads`/`writes`/`data_flows` as primary
artifacts for SQL. It does not demand `functions` from a language that has none.

---

## 8. Honest Refusal — Rust

**Input:** the Rust compiler · 36,176 `.rs` files

```json
{"status": "REVIEW_REQUIRED",
 "language_selection": {"language": "rust", "source": "bridge_classify_files",
                        "confidence": "high", "files_provided": 36176},
 "module3": {"language": "rust", "engine": null, "status": "NOT_IMPLEMENTED",
             "capabilities": [],
             "truth_boundary": {"scope": "No Module 3 reasoning engine is implemented for rust."}},
 "reason": "This repository is predominantly rust (36176 rust files), identified from actual file composition. CodeTruth does not implement rust analysis: its adapter is a declared stub. No analysis was performed and no findings are claimed. This is a known capability boundary, not a failure to parse."}
```

The dominant language is identified correctly from evidence. The stub is
**selected** so that it can **refuse**. Zero capabilities claimed.

Before 2026-07-10 this repository reported `COMPLETE` after analyzing its
**190 JavaScript files**.

---

## 9. Zero-Guess Contract at Scale

**Input:** PyTorch — 4,620 files

```json
{"module2": {"files_scanned": 4620, "functions": 143436, "call_graph_edges": 312650},
 "module3": {
   "truth_boundary": {"numeric_confidence_scores": 0, "guesses": 0},
   "by_label": {"RESOLVED": 7979, "INFERRED": 0, "AMBIGUOUS": 35, "UNCERTAIN": 4, "UNRESOLVABLE": 0},
   "edge_provenance": {"module2_edges": 312650, "local_receiver_added": 6856, "total_edges": 319506}}}
```

**312,650 + 6,856 = 319,506.** Exact. Every edge traces to Module 2's parse or a
labelled Module 3 resolution.

Attribute-call resolution: **2.39%**. PyTorch is dominated by dynamic dispatch
(`__torch_function__`, registration, tensor dispatch). Low coverage with zero
guesses is **SOUND** — the engine declined what it could not prove and recorded
the reason for each decline.

**transformers:** 100,225 + 5,055 = 105,280. Exact. `guesses: 0`.

---

## 10. Guided Diagnosis — Refusing Without a Dead End

**Input:** repository `flask` · target `memory_db.MemoryDB.search_semantic`

```
Target `memory_db.MemoryDB.search_semantic` is not in the verified call index.
The target's top-level module `memory_db` does not appear in the verified call
index for this repository. Verify that you selected the correct repository or
target method. This repo's top-level modules include: docs, examples, flask,
tests. Tip: use Browse methods to pick a verified method from the current
repository.
```

It states only what is verified: the module is not in the index. It does **not**
assert "this method belongs to a different repository" — that would claim more
than was checked. It lists the repository's actual modules as evidence and names
the next action.

Four evidence-based branches: empty index · target module absent · name/prefix
mismatch · not parsed.

---

## 11. The Completeness Guard

The pipeline may report `COMPLETE` only if the selected engine produced
**primary artifacts appropriate to its paradigm**.

| Language class | Requires |
|---|---|
| Graph languages | `functions > 0` **or** `call_graph_edges > 0` **or** an M3 reasoning index |
| SQL | `objects` / `reads` / `writes` / `data_flows` > 0 |

**It caught, in the live pipeline:**

```
nginx       — routed c_cpp, adapter received 0 files    → REVIEW_REQUIRED
spring-boot — routed java,  adapter received 0 files    → REVIEW_REQUIRED
rust        — declared stub, no engine                   → REVIEW_REQUIRED
```

Without it, all three would have reported `COMPLETE` while analyzing nothing.
Two of those were bugs introduced hours earlier by the author of the guard.

**What it does not catch:** a wrong-language analysis that produces *real*
artifacts. odoo's SQL analysis found 17 tables; rust's JavaScript analysis found
real functions. Both had substance. The guard checks whether substance exists,
not whether it is about the right thing.

That gap is covered by the **neutral language-review flag**, which records that
Module 1 and Module 2 name different languages, and delivers no verdict.

---

## 12. The Common Envelope

No language borrows another's vocabulary.

```json
"module3": {
  "language": "go",
  "engine": "bridge.advanced_reparsed",
  "status": "COMPLETE",
  "capabilities": ["call_graph", "hotspots", "chokepoints", "recursion", "reachable"],
  "truth_boundary": {
    "scope": "Go reasoning over a caller-aware re-parse (the Module 2 adapter records callees but not callers)",
    "limitations": ["cross-package calls", "interface dispatch", "struct embedding",
                    "generics", "brace-heuristic parse (no Go AST)"]
  },
  "graph": {"functions_in_index": 33428}
}
```

**No `guesses`. No `edge_provenance`.** Those are Phase 3A/3B measurements the
Go engine never performs. Emitting `guesses: 0` here would fabricate a guarantee.

Python's block, by contrast, contains both — because Python's engine computes
them.

---

*CodeTruth Agent V3 — Module 3 — Repository Reasoning*
*github.com/Zeeshan78699/CodeTruthAgent*
