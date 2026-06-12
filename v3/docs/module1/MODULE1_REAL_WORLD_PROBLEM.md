# CodeTruth Agent V3 — Module 1
## Real-World Problem Statement

---

## 1. The Problem

Any tool that proposes to analyze, modify, or govern changes to a code
repository — whether an AI coding assistant, a static analysis tool, or
a CI/CD policy engine — must first answer a basic question:

**"What kind of repository is this?"**

Without that context, the same signal can mean very different things.
A `torch` import in a repository might indicate a machine-learning
pipeline, or it might just be a dependency used internally by a
computer-vision tool (Ultralytics), an audio tool (Whisper), or a
quantum-computing library (PennyLane). A `.bin` file might be a trained
model weight, or it might be an unrelated binary asset. A repository
with almost no Python files (Redis, Nginx, Go, Rust, U-Boot) might still
be one where Python tooling, governance, or analysis is relevant.

Tools that skip this step, or that rely on shallow heuristics (file
extension counts, single-keyword matching), produce misclassifications
that cascade into every later stage of analysis.

---

## 2. Where This Stands Today

General-purpose language-detection tools (e.g. GitHub Linguist, `cloc`)
answer "what languages are present" but not "what kind of application
is this" or "what framework is it built on". They are not designed to
distinguish, for example, between a Flask web application and a Flask
dependency used only for internal tooling inside a robotics repository
(as seen in Drake).

Framework-specific tools (e.g. a Django-specific linter) assume the
framework is already known.

---

## 3. How Module 1 Addresses This

Module 1 performs repository-wide discovery and classification as a
distinct, first step, combining:

- Dependency-file signals (what's declared)
- Import-statement signals (what's actually used, sampled across
  source files)
- Content-pattern signals (what files/structures exist, for
  repositories without a pip-installable identity)
- A type hierarchy that resolves conflicts between competing signals

The output — application type, primary framework, languages, build
systems, technology stack, discovery score — is structured data that
later modules (or other tools) can consume without re-deriving it.

---

## 4. Problem → Resolution Mapping

| Problem | How Module 1 Resolves It |
|---|---|
| Same package import can mean different things in different repos (e.g. `torch` in an ML pipeline vs. inside Ultralytics/Whisper/PennyLane) | Content-pattern signals (weight 15) establish repository identity *before* generic import signals are weighed, and a type hierarchy table suppresses competing types when a stronger, more specific signal is present |
| Non-Python repositories (Redis, Nginx, Go, Rust, U-Boot, Zephyr) still need classification | Content-pattern and file-extension signals work independently of Python package presence; "No Framework Detected" is reported honestly when no Python framework exists, rather than guessing |
| Generic utility packages (Click, Requests, Pytest) appearing anywhere can masquerade as "the framework" | These are excluded from the primary-framework candidate pool entirely — they may appear as *secondary* frameworks but never as primary |
| A package's pip name differs from its display/self identity (e.g. `solana-py` repo vs. `solana` package, `cvxpy` vs `ortools`) | Self-name resolution pass strips common affixes (`_py`, `python_`) and matches repo directory name against package names before falling back to other signals |
| Two frameworks both map to the same application type (e.g. `astropy` and `sgp4` both → SPACE_SYSTEM) | Type-match pass prefers the candidate whose own mapped type equals the repository's determined type |
| Confidence in a result needs to be communicated, not just a yes/no | Two separate scores — discovery (file/asset coverage) and classification (type + framework confidence) — are reported, with classification=75% meaning specifically and only "type correct, no framework exists" |
| Downstream tooling needs structured, reusable output | All results are returned as an immutable `RepositoryCognitionReport` dataclass plus `.txt`/`.md`/`.json` reports, consumable without re-deriving any of the above |

## 5. Validation Approach

Rather than validating against synthetic or curated examples only,
Module 1 was run against 69 real, cloned, open-source repositories
spanning 46 application types and roughly 38 engineering domains —
including repositories with no Python code at all (Redis, Nginx, Go,
Rust, U-Boot, Zephyr) and repositories ranging from 35 files to over
61,000 files.

Results: 69/69 correct application type, 69/69 100% discovery, 69/69
correct primary framework, 0 crashes. Details in
`MODULE1_CAPABILITY_PROOF.md`.

---

## 6. Scope and Next Steps

Module 1 is a discovery/classification layer. It does not modify
repositories and does not make any code-change decisions. It is the
first of several modules in CodeTruth Agent V3 — a governance pipeline
currently under development. The next module (Repository Graph Engine)
will build a structural graph of the repository using the output of
Module 1 as its starting point.
