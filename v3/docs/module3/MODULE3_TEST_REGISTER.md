# Module 3 — Test Register

**Date:** 2026-07-10
**Standard:** A test appears in this register only if it **executes**. A file
named `test_*.py` that no runner collects is not a test, and listing it here
would make this document a false claim.

---

## Summary

| Layer | What it answers | Status |
|---|---|---|
| **L1 — Unit** | Did this individual fix regress? | ✅ **20/20 pass** |
| **L2 — Invariant** | Does the contract hold on any repository? | ✅ **74 repos, 0 failures** |
| **L3 — Golden regression** | Did a change alter known-good behaviour? | ⏳ **not built** |
| **L4 — UAT / scenarios** | Can an engineer solve a real problem with this? | ⏳ **partial** |

```
Code Change → Unit → Invariant → Golden → UAT
```

---

## L1 — Unit Tests · 20/20 PASS

**File:** `v3\main_pipeline_to_run\test_codetruth_fixes.py`
**Run:** `python -m pytest test_codetruth_fixes.py -v`
**Scope:** report-layer and guard fixes, in isolation. No live repository, no
frozen reasoning engine, no network.

| ID | Test | Asserts |
|---|---|---|
| TC_U_001–005 | `test_detects_venv_of_any_name` | `.venv`, `venv`, `.venv_hidden`, `myenv`, `env` all detected |
| TC_U_006 | `test_clean_repo_not_flagged` | no false positive |
| TC_U_007 | `test_pycache_alone_does_not_trip` | `__pycache__` is not a venv |
| TC_U_008 | `test_does_not_descend_into_venv` | guard stops at the venv, does not walk its tree |
| TC_U_009 | `test_clone_folder_name_leak_suppressed` | `"Ctlive Caex6Oyz"` at conf 0.75 → `"not detected"` |
| TC_U_010 | `test_unknown_zero_confidence_suppressed` | UNKNOWN / conf 0 → `"not detected"` |
| TC_U_011 | `test_real_framework_preserved` | Flask in `Memory_System` → `"Flask"` |
| TC_U_012 | `test_repo_named_after_its_framework_not_suppressed` | a repo *named* `flask` whose framework **is** Flask → `"Flask"` |
| TC_U_013 | `test_real_framework_inside_clone_dir_preserved` | Flask inside `ctlive_abc` → `"Flask"` |
| TC_U_014 | `test_empty_index` | empty call index → honest reason |
| TC_U_015 | `test_target_module_absent` | `memory_db.*` in the Flask index → names the repo's real modules; **does not** assert "belongs to a different repository" |
| TC_U_016 | `test_name_or_prefix_mismatch` | leaf exists under another qualifier → suggests matches |
| TC_U_017 | `test_genuinely_absent_leaf` | not parsed / misspelled |
| TC_U_018 | `test_never_fabricates` | the diagnosis is a string, never a fake analysis structure |
| TC_U_019–020 | `test_lists_subdirs_with_parent`, `test_nonexistent_path_no_crash` | folder picker |

**Result:** `20 passed in 0.09s` — win32, Python 3.12.7.

---

## L2 — Invariant Contract · 74 repositories, 0 failures

**Harness:** `run_corpus_eval.py`
**Run:** `python run_corpus_eval.py --root "C:\repos\v3" --runner "v3\run_codetruth.py"`

Every repository **passes by behaving correctly for its own gate outcome**.
Nothing is skipped. A `REVIEW_REQUIRED` repository passes by holding honestly.

### Universal invariants — always asserted

| ID | Invariant |
|---|---|
| INV_U_001 | Status is one of the known honest states |
| INV_U_002 | No fabricated evidence |
| INV_U_003 | Truth Boundary present |
| INV_U_004 | No silent success — a non-COMPLETE run claims no findings |
| INV_U_005 | Gate and status are consistent |

### Conditional invariants — per outcome

| ID | Condition | Invariant |
|---|---|---|
| INV_C_001 | `COMPLETE` + Python M3 measured `guesses` | `guesses == 0` |
| INV_C_002 | `COMPLETE` + Python M3 | `total_edges == module2_edges + local_receiver_added` |
| INV_C_003 | `COMPLETE` + non-Python | primary artifacts exist (graph or lineage) |
| INV_C_004 | `REVIEW_REQUIRED` | gate matches status; reason reported |
| INV_C_005 | `BLOCKED` | no findings claimed; reason reported |
| INV_C_006 | `M2_ERROR` / `M3_ERROR` | honest loud failure with a reason; no findings claimed |
| INV_C_007 | any envelope | `ENGINE_ERROR` or `NOT_IMPLEMENTED` ⇒ `capabilities == []` |

### Design notes

**INV_C_001 is gated on the measurement, not the block.** The per-language
envelope carries a `truth_boundary` containing `{scope, limitations}` and
deliberately **not** `guesses`. The check therefore tests for the presence of the
`guesses` **key**. Testing for `truth_boundary` instead would demand a Python-only
metric from engines that never compute it — and did, causing false failures on
FreeCAD and LibreCAD until corrected.

**INV_C_007 first fired on real data on 2026-07-10**, exercised by `rust`. Before
that it had only ever passed against synthetic input. An invariant that has never
fired on real data is a claim, not a check.

### Result — 2026-07-10

```
74 repositories · 71 COMPLETE · 3 REVIEW_REQUIRED · 0 BLOCKED
 0 pipeline errors · 0 invariant failures · 0 language-review flags
```

### Bugs this suite caught

| Repository | Detected |
|---|---|
| odoo | `COMPLETE` with 0 functions — false completeness |
| go, nginx, pulumi, react, spring-boot, ui5-webcomponents | `status: REVIEW_REQUIRED` with `gate: APPROVED` — contradiction |
| FreeCAD, LibreCAD | the suite's *own* `guesses` check misfiring on the new envelope |

Two of those were introduced by the author minutes before the suite caught them.

---

## L3 — Golden Regression · NOT BUILT

**Purpose:** detect unintended output changes against a pinned repository at a
pinned commit SHA.

**Design requirement:** assert **structural invariants**, not brittle totals.

```
✅ AppContext.push has exactly 1 verified caller: __enter__
✅ dispatch_request has caller full_dispatch_request
❌ flask has 697 edges          ← drifts with upstream changes
```

**Prerequisite:** pin commit SHAs. `psf/flask` is not a fixed input.

---

## L4 — UAT / Real-World Scenarios · PARTIAL

| ID | Scenario | Status |
|---|---|---|
| **TC_M3_001** | Missing-target guided validation | ✅ **PASS** |
| **TC_M3_003** | Security patch impact analysis | ⏳ **To be run** |

### TC_M3_001 — Missing-target guided validation · PASS

**Input:** repository `flask`, target `memory_db.MemoryDB.search_semantic`

**Asserts:** the verified index is inspected · the absent top-level module is
named · the repository's actual modules are listed · a next action is given ·
**no analysis is fabricated** · the wording claims only what was checked
(*"does not appear in the verified call index"*, **not** *"belongs to a different
repository"*).

**Note:** the test is named for what is *verified* — target absent from index —
not for the *inferred* cause (wrong repository).

### TC_M3_003 — Security patch impact · TO BE RUN, BLOCKED

**Scenario:** a CVE in an authentication method. Which callers require regression
testing before patching?

**Why it is blocked:** authentication methods are overwhelmingly invoked by
decorators, middleware, and framework request pipelines — precisely the callers
Module 3 cannot see. Decorator detection is not implemented.

**Mandatory acceptance criteria** — the test **fails** if any of these are absent:

| # | Criterion |
|---|---|
| 1 | The Truth Boundary is the **headline**, not a footnote |
| 2 | The verified caller count is explicitly framed as a **floor** |
| 3 | A low or zero verified-caller count does **not** read as "safe to patch" |
| 4 | The report does not claim a complete authentication-impact picture |
| 5 | The deferred decorator-detection limitation is acknowledged |

**Fail conditions:** the report implies the caller list is complete · a low count
is presented as low real risk · any fabricated caller, chain, or "safe to patch"
verdict appears.

---

## Seven Validated Engineering Workflows

Exercised on flask, django, requests, records, Memory_System.

| # | Workflow | Report |
|---|---|---|
| 1 | Repository onboarding / assessment | Repository Assessment |
| 2 | Safe method refactoring | Method Change Impact |
| 3 | Class-level refactoring | Class Change Impact |
| 4 | Dead-code investigation | Dead Code Candidates |
| 5 | Dependency-chain reconstruction | verified call chains |
| 6 | Rule-based regression triage | stated LOW/MEDIUM/HIGH rule |
| 7 | Change-impact for security review | with boundary — see TC_M3_003 |

Each carries the same boundary: **a verified in-repo floor, not a ceiling.**

---

## NOT A TEST SUITE — `v3\repository_reasoning\tests\`

Sixteen files named `test_*.py`, in a directory named `tests\`. **Pytest collects
zero tests from them.** They contain `if __name__ == "__main__"` blocks, not test
functions. They execute only when a human invokes them individually.

Three additionally fail to import:

```
test_bench_against_networkx.py   → bench_against_networkx lives in benchmarks/crosscodeeval/
test_bench_crosscodeeval.py      → same
test_java_type_inference.py      → bare `import java_type_inference` with no sys.path setup
```

**This directory is not evidence and must not be cited as such.** It is listed
here only so that no future reader mistakes it for coverage.

A folder named `tests\` that runs nothing is the same failure shape as
`pipeline.py` — which looks like the pipeline and is imported by nothing — and as
the Go adapter's `✅ Validated` mark, which sits beside a component that produces
zero functions in the live pipeline.

**Remediation:** convert to real pytest tests, or rename the directory.

---

*CodeTruth Agent V3 — github.com/Zeeshan78699/CodeTruthAgent*
*AI imagines. CodeTruth checks. Nature tests. Humans decide.*
