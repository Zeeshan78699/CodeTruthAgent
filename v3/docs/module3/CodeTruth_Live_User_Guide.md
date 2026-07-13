# CodeTruth Live — User Guide

**Deterministic repository intelligence with zero guesses and reproducible engineering evidence.**

**Version:** V3 · multi-language pipeline
**Updated:** 2026-07-13

---

## What CodeTruth Live Is

A web interface to the CodeTruth analysis pipeline. Point it at a repository and
it answers structural engineering questions from **verified evidence only**:

- What is this repository, and how is it built?
- If I change this method, what provably breaks?
- What code has no verified caller?
- Where does the analysis stop being able to see?

**It never guesses.** Where it cannot prove something, it says so and names the
reason.

## What It Is Not

It reads **structure**. It does not execute code.

It **scopes** an issue — producing a verified dependency map plus an explicit
map of what it could not see. It does not **diagnose** one. Root-cause analysis
requires runtime behaviour, and that is not what this tool does.

> *"Analyzed the dependencies"* is not *"analyzed the bug."*

---

## Starting the Server

```powershell
cd C:\AI_Project\CodeTruthAgent\v3\main_pipeline_to_run
python -m uvicorn app:app --reload --port 8000
```

Open **http://localhost:8000**

You may see `SyntaxWarning: invalid escape sequence` lines from repositories
being parsed. Those come from the analyzed source, not from CodeTruth. Ignore them.

---

## The Six Analysis Modes

| Mode | Question it answers |
|---|---|
| **Repository Assessment** | What is this repository? Full 11-section engineering report with rule-based health/risk labels (the rule is always shown inline). |
| **Method Change Impact** | What is verifiably affected if I change this method? |
| **Class Change Impact** | Aggregate impact across every method of a class. |
| **Dead Code Candidates** | What has no verified caller? **Candidates, not a verdict.** |
| **Truth Boundary Demo** ⭐ | Watch it refuse to guess. |
| **Project Intelligence Report** | Full evidence-tiered project document for humans & AI. Every field tagged OBSERVED / DERIVED / INFERRED / not-determined. Includes the Documentation Auditor (docs-vs-code drift). |

**Two report families, two philosophies — both honest.** The *Repository
Assessment* gives rule-based labels (SOUND, risk HIGH/MEDIUM/LOW) with the
deriving rule always printed beside the label, so a label is a citation to a
deterministic function of measured facts, never a subjective judgment. The
*Project Intelligence Report* drops labels entirely and reports raw evidence
tiers, for auditors and AI that want the underlying numbers. Same engine, two
surfaces.

---

## Choosing a Repository

Three sources:

### Curated repo (instant)
A dropdown of pre-cloned repositories. Returns in seconds. Use this first.

### GitHub URL (clones, slower)
Paste a repository URL. It is cloned live, size-capped, analyzed, then deleted.
The report shows the **source URL**, not the temporary clone path.

### Local path (this machine only)
A folder on the server machine. Use **Browse…** to open a native folder picker.

---

## Selecting a Method

For **Method Change Impact** and **Class Change Impact**, use **Browse methods**
rather than typing. It lists the methods that are actually in the verified call
index, so a typo or a wrong-repository name is impossible.

If you do type one and it isn't found, you get a **guided diagnosis** rather
than a dead end:

> Target `memory_db.MemoryDB.search_semantic` is not in the verified call index.
> The target's top-level module `memory_db` does not appear in the verified call
> index for this repository. Verify that you selected the correct repository or
> target method. This repo's top-level modules include: docs, examples, flask,
> tests. Tip: use Browse methods to pick a verified method from the current
> repository.

Note what it says and does not say. It reports that the module **is not in the
index** — a verified fact. It does **not** assert *"this method belongs to a
different repository"*, because that was never checked.

---

## Reading the Status Line

The status colour reflects what actually happened. It is not decoration.

| Status | Meaning |
|---|---|
| 🟢 **Analysis complete — deterministic, 0 guesses** | The pipeline completed, governance approved, Module 3 ran. |
| 🟢 **Analysis complete under manual override** | You pressed *Analyze anyway*. The classification was uncertain; a human chose to proceed. Findings remain zero-guess. |
| 🟡 **Held: REVIEW_REQUIRED** | Module 1's governance gate flagged an uncertain classification. **No findings were generated.** |
| 🔴 **BLOCKED by governance gate** | No analysis was performed. |

**A green "0 guesses" appears only when Module 3 actually ran.** It is never
shown on a run that produced nothing.

---

## "Analyze anyway"

When a repository is **held at REVIEW_REQUIRED**, a button appears:

> **Analyze anyway (proceed past governance review) →**

This is the review-then-approve workflow the gate's name implies. The gate still
fires. Nothing is silently bypassed. **You** decide to proceed, and the resulting
report opens with a banner recording that you did:

> **Analyzed under manual override.** Module 1's governance gate returned
> REVIEW_REQUIRED (uncertain classification: UNKNOWN, confidence 0.5). A human
> chose to proceed. Findings below are computed normally and remain zero-guess;
> the gate's caution about the repository's *classification* still applies.

**BLOCKED repositories do not get this button.** Forcing an analysis of an empty
or unrecognizable repository is pointless. Only *analyzable but uncertain*
repositories offer the override.

### Why libraries are often held

Module 1 classifies application *type* with low confidence on many real
libraries — `requests`, `records`, CPython. The gate holds them. This is honest
abstention, not a failure. Press *Analyze anyway* and the engine analyzes them
perfectly.

---

## Languages

The pipeline routes to the **dominant language by actual file count**.

| Language | What you get |
|---|---|
| **Python** | Full reasoning: attribute resolution, MRO, `super()` chains, edge provenance, guess counting |
| **Java, JavaScript, C/C++** | Call graph · who-calls · impact · dead-code |
| **Go, C#** | Call graph, recovered by re-parsing source (their parsers drop callers) |
| **SQL** | Data lineage — reads, writes, table flows. Not a call graph. |
| **Rust** | **Honest refusal.** The adapter is a declared stub. |

### What a Rust repository looks like

```
Status : REVIEW_REQUIRED
Reason : This repository is predominantly rust (36,176 rust files), identified
         from actual file composition. CodeTruth does not implement rust
         analysis: its adapter is a declared stub. No analysis was performed
         and no findings are claimed. This is a known capability boundary,
         not a failure to parse.
```

It identifies the language correctly, then refuses. It does not analyze the
repository's 190 JavaScript files and call that a result.

### Depth is not equal

Python has been validated across a 76-repository corpus with full resolution.
The other languages have been demonstrated on **one real repository each**. They
produce a call graph and answer queries. They do **not** perform Python's deep
resolution.

### Near-parity repositories

Routing selects by file count. When two languages are close, the choice is
unreliable.

**PyTorch is 4,733 C/C++ files and 4,609 Python files** — a 1.3% margin. A
124-file difference decides whether you get a 143,436-function Python analysis
or a 17,625-function C/C++ one. For such repositories, check the reported
language before trusting the report.

Every report shows how the language was chosen:

```json
"language_selection": {"language": "python", "source": "bridge_classify_files",
                       "confidence": "high", "files_provided": 4609}
```

---

## Reading a Repository Assessment

### Four independent axes

They are not the same thing and must not be conflated.

| Axis | Answers |
|---|---|
| **Repository role** | What the codebase *is* |
| **Domain** | What it is *about* — **not yet classified**, shown blank rather than guessed |
| **Architecture** | How it is *structured* |
| **Detected technologies** | What it *uses* — a dependency, not the repository's identity |

A web framework has role `LIBRARY` and detected-technologies pointing at itself.
An application that imports it has role `WEB_APPLICATION`, detected `Flask`.

**Application type is classified; domain is not.** Module 1 assigns a
*repository role* (e.g. WEB_APPLICATION, CLI_TOOL, SPACE_SYSTEM, MEDICAL_SYSTEM)
alongside an independent *architecture* axis (e.g. LIBRARY). When the two axes
conflict — a web framework is structurally a LIBRARY but role-classified as
WEB_APPLICATION — the Project Intelligence Report reports the conflict as
`EVIDENCE_CONFLICTING` rather than collapsing it into one wrong label. The
separate *domain* axis (what the code is *about*) is still not computed and is
shown blank rather than guessed. An unclassified field is more useful than a
wrongly-classified one.

### Health means analysis integrity, not coverage

```
Rating rule: SOUND if guesses == 0 AND uncategorized_declines == 0
```

A dynamic framework with 2% attribute-call resolution and zero guesses is
**SOUND**. The analysis is trustworthy. It is not penalized for the code being
dynamic — most unresolved calls are dynamic dispatch, correctly declined.

Low coverage is a fact about the *code*. Zero guesses is a fact about the *tool*.

---

## Reading a Change Impact Report

### Verified callers are a **floor**

`flask.ctx.AppContext.push` shows **one** verified caller: `__enter__`.

In reality it is invoked by every `with app.app_context():` in every application
using Flask — through the context-manager protocol, from outside the analyzed
repository.

**One caller is a proven lower bound, not the complete set.** The report says so:

> These are the verified in-repository impacts. External libraries, plugins,
> runtime dispatch, and dynamic callers are not included and are explicitly
> treated as unknown rather than guessed.

### This matters most for security patches

Authentication methods are invoked by decorators and middleware — precisely the
callers CodeTruth cannot see.

A low verified-caller count on `validate_token` means **"CodeTruth cannot see the
callers."** It never means **"few dependencies."** Read the Truth Boundary before
you read the risk rating.

### `<external>` does not mean "third-party"

It means the resolver **could not confirm the target is in this repository**.
That set contains genuine third-party calls *and* in-repo calls it could not
resolve. CodeTruth does not guess which, and says so.

### Risk is rule-based, not scored

```
HIGH   if all three of [public API, depth ≥ 3, affected ≥ 3]
MEDIUM if exactly two
LOW    otherwise
```

Every input is measured from the verified graph. There is no subjective scoring.
The rating describes the **verified graph**, not the runtime system.

---

## Reading Dead Code Candidates

**The label is CANDIDATES. It is not a deletion verdict.**

A candidate is a function with **no inbound internal call edge** in the verified
call graph. That is evidence of absence in static analysis — not proof the
function is unused.

Two evidence-backed buckets:

| Bucket | Evidence |
|---|---|
| **Module entry script** | The node is a `.<module>` execution entry |
| **Investigation candidate** | No verified inbound internal caller |

### Why Flask reports 125 candidates

Most of them are **live public API**. `Flask.__call__` is the WSGI entry point —
every request goes through it. `send_static_file`, `send_file`, route decorators,
pytest fixtures: all invoked from outside the analyzed graph.

CodeTruth lists them because it cannot verify their callers. It **refuses to call
them dead**. Richer labels — *route handler*, *CLI entry point* — are not
inferred, because the call graph carries no decorator metadata and labelling a
route would be a guess.

**Read every candidate as "investigate." Never as "delete."**

---

## Reading the Documentation Auditor

Part of the **Project Intelligence Report**. It tests what the docs **claim**
against what the code **contains**. Code is the arbiter; documentation is the
claim under test. Every finding states a disagreement and both sides — it never
declares the docs simply "wrong," and it never invents API the code lacks.

### Three outcomes, and they reconcile

| Outcome | Meaning |
|---|---|
| **MATCH** | A documented API symbol exists in the code. |
| **DRIFT** | Docs claim a symbol (via an explicit `:func:`/`:class:` role) that the code lacks — or the code exposes public API the docs never name. |
| **NO_EVIDENCE** | The claim can't be confirmed *or* refuted from static structure — a property, attribute, inherited member, or re-export the symbol model cannot represent. Reported, never guessed. |

The counts always reconcile: `api_claims_checked = MATCH + DRIFT + NO_EVIDENCE`,
and the report prints the arithmetic.

### What is filtered out before drift analysis

A documented token is only treated as a project-API claim if it looks like one.
Python keywords, standard-library names, third-party dependencies (derived from
the repo's own manifest, not a hardcoded list), config keys, filenames, HTTP
terms, and example/tutorial variables are all excluded and counted separately.
This is why a real run reports a handful of genuine findings, not hundreds of
false positives.

### Three documentation styles are understood

- **Prose + roles** (`:func:\`create_app\``) — e.g. Flask
- **Explicit autodoc** (`.. autofunction:: X`)
- **Whole-module autodoc** (`.. automodule:: pkg.mod`) — e.g. scientific
  libraries that document a package's members at once

A public symbol whose module is covered by an `automodule` directive is treated
as documented; symbols in modules with no such directive are honestly reported
as undocumented, broken down by source (production vs example vs tooling).

### Undocumented ≠ noise

When a scientific library reports hundreds of "public symbols not named in docs,"
that is usually a *true* finding — internal subpackages exposing public helpers
with no API-doc coverage. The auditor's job is to surface that fact, not to
soften it. Read it as "these exist and aren't documented," then decide whether
to document them or mark them private.

---

## The Truth Boundary Demo

Same tool, same repository, two methods.

| Method | Verified callers | Verdict |
|---|---|---|
| `flask.app.Flask.dispatch_request` | 1 — `full_dispatch_request` | 🟢 VERIFIED IMPACT |
| `flask.app.Flask.send_static_file` | 0 | 🟡 **KNOWN-UNKNOWN** — not "safe to delete" |

`send_static_file` is public Flask API. A naive dead-code tool would see zero
callers and report it removable. It is not.

```
Verified findings : 1
Known-unknowns    : 1
Guesses           : 0
```

**Zero callers is reported as unknown, never as unused.**

---

## Common Situations

### "Repository contains a virtual environment"

> CodeTruth analyzes your source, not installed dependencies — move the
> environment outside the project folder and try again.

A `.venv` inside the repository would cause the analyzer to walk thousands of
installed packages as if they were your code. Move it out. Any name is
detected — `.venv`, `venv`, `myenv`, `env` — by its `pyvenv.cfg` marker.

### The Stop button

> Stopped watching this run. Note: the server may still finish the analysis in
> the background — this cancels the browser wait, not the server job.

It is honest about what it does. It stops the browser waiting. It does not kill
the server-side analysis.

### Large repositories

PyTorch (4,620 files, 143,436 functions) and transformers (4,469 files, 55,521
functions) analyze successfully and are slow and memory-hungry. Free RAM first.
Elasticsearch parses 22,101 Java files.

---

## Exports

| Button | Produces |
|---|---|
| **Export Markdown** | The report, verbatim |
| **Export JSON** | Structured output including `language_selection` provenance |
| **Export PDF (print)** | Browser print dialog |

Reports are safe to hand to a maintainer. They state their own boundaries.

---

## What Every Report Guarantees

```
✅ Zero guesses            No target is invented. Ever.
✅ Deterministic           Same inputs, same output, every time.
✅ Reproducible            Every finding traces to a module and an evidence source.
✅ Truth Boundary          What cannot be proven is reported as unknown.
```

And what it does not guarantee:

```
❌ Complete caller sets    Every result is a verified in-repo floor.
❌ Runtime behaviour       It reads structure; it does not execute.
❌ A diagnosis             It scopes an issue. It does not explain one.
```

---

## Known Limitations

| Limitation | Detail |
|---|---|
| **Near-parity language routing** | PyTorch: a 1.3% file-count margin decides the analysis language. Check the reported language on mixed repositories. |
| **No decorator detection** | Route handlers, auth methods, and pytest fixtures appear as dead-code candidates. Their callers are invisible. |
| **Depth varies by language** | Python has full resolution. Others have a call graph. |
| **C/C++ under-extraction** | nginx: 401 files yield 15 functions. |
| **Module 1 application-type accuracy** | The application-type classifier is the pipeline's weakest layer — e.g. Flask is role-classified WEB_APPLICATION though structurally a LIBRARY. This is contained, not hidden: the independent architecture axis reports LIBRARY, and the Project Intelligence Report surfaces the disagreement as `EVIDENCE_CONFLICTING` rather than committing to one label. Dual-axis refinement is scheduled work. |

Each of these is a *known* limit, stated here so that no report is trusted past
its evidence.

---

*CodeTruth — proves what it can, flags what it can't, never guesses.*
*github.com/Zeeshan78699/CodeTruthAgent*
