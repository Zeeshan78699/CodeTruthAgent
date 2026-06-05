# CodeTruth Agent V2

## Deterministic Pre-Modification Governance Layer for Python Code Changes

🚀 Open-source deterministic governance layer that analyzes candidate function pairs 
using semantic similarity and behavioral analysis, and determines whether a 
candidate code change should be considered SAFE, REVIEW, or BLOCK before 
modification is attempted.

---

# 📌 Overview

CodeTruth Agent V2 is a deterministic governance layer for code changes in Python projects. It scans a repository, identifies risky patterns, analyzes candidate function pairs across semantic and behavioral dimensions and produces SAFE / REVIEW / BLOCK decisions before any modification is applied.

V2 extends V1's safe-merge reasoning with two additional analysis stages — semantic similarity and behavioral signature detection — and wires them into a single governance pipeline.

Unlike traditional duplicate detection tools or LLM-based code review systems, CodeTruth V2 combines:

* Rule-based AST governance scanning
* Semantic similarity analysis (deterministic embeddings, no LLM)
* Behavioral signature detection (AST-based pattern matching)
* Multi-signal fusion with conservative-default risk classification
* Human-in-the-loop approval routing
* Safe execution with backup and rollback
* V1 duplicate detection integrated as ground truth

into one unified governance pipeline.

### What V2 catches that V1 alone does not

```text
commit() vs savepoint_commit()         → Django transaction risk     BLOCK
atomic() vs _non_atomic_requests()     → Decorator opposing pair     BLOCK
_get_new_csrf_string() vs              → CSRF security distinction   BLOCK
  _add_new_csrf_cookie()
replace_function_calls() vs            → Backup-operation difference REVIEW
  replace_function_calls_across_project()
```

V2 surfaces semantic and behavioral distinctions between similarly-named functions that V1's structural similarity scanner does not catch.

## 🌍 Where V2 Sits in the Landscape

The following list describes tool categories that exist in the June 2026 landscape and how V2's scope differs from each. No specific products are named, since the AI tooling ecosystem evolves rapidly.

### AI PR Review
- **What this category does:** An LLM reads code diffs and posts inline comments on pull requests, generating natural-language feedback and summaries.
- **When it runs:** After code is written, typically when a pull request is opened.
- **How V2 differs:** V2 runs before a patch is applied, not at PR time. V2 has no LLM in the decision path; decisions are deterministic.

### Static Application Security Testing (SAST)
- **What this category does:** Rule-based scanning for known vulnerability patterns and code-quality issues, drawing from established taxonomies (CWE, OWASP, language-specific lints).
- **When it runs:** At commit time, PR review, or in CI pipelines.
- **How V2 differs:** V2 focuses on semantic and behavioral function-pair analysis for governance decisions, not on security-rule pattern matching.

### Hybrid (Deterministic + LLM)
- **What this category does:** Combines static analysis with LLM-based contextual review, using deterministic rules as a baseline and LLM reasoning for context-dependent issues.
- **When it runs:** At PR review.
- **How V2 differs:** V2 is deterministic-only in the decision path. LLM scaffolding exists in V2's codebase but is disabled and reserved for V3.

### LLM Runtime Guardrails
- **What this category does:** Validates and constrains LLM outputs during generation — content safety, prompt-injection defense, output schema enforcement.
- **When it runs:** At LLM output, in the runtime pipeline.
- **How V2 differs:** V2 does not interact with LLM output. V2 operates on code in the repository, not on model-generated text streams.

### AI Agent Governance
- **What this category does:** Policy enforcement and audit trails for autonomous agent actions, including tool-use restrictions and decision logging.
- **When it runs:** At agent runtime, when an agent invokes a tool or takes an action.
- **How V2 differs:** V2 governs code modifications, not autonomous agent behavior. V2 is invoked by humans (or by future V3 components), not by general-purpose agents.

### Pre-Modification Code Governance — V2's Category
- **What this category does:** Deterministic gate that decides whether a candidate code change should be applied, based on semantic and behavioral analysis of the functions involved.
- **When it runs:** Before any patch is applied to the repository.
- **How V2 differs:** This is V2's category. The contribution is the combination of deterministic semantic + behavioral analysis with conservative-default fusion, sitting as a gate before modification rather than as a reviewer after the fact.

*Categories reflect a June 2026 landscape review and are illustrative, not a formal benchmark comparison. V2's differentiator is the combination of deterministic semantic + behavioral analysis as a pre-modification gate, not a claim that no adjacent tool exists in any other category.*

---

# ✅ Current Status

| Item | Status |
|---|---|
| Version | V2 (Governance Layer) |
| Architecture | Rule-Based + Deterministic Semantic + Behavioral |
| Language | Python 3.x |
| V1 Test Cases | 20 / 22 PASSED; 2 by-design exclusions (TC07 nested extraction, TC14 style variants) |
| V2 Multi-Repository Evaluation | 8 repositories, 7,862 files |
| V2 Pipeline errors across 1,241 pair analyses | 0 |
| V2 BLOCK audit (14-pair sample) | 60% governance-significant (Groups A+B); 4/4 opposing detections GENUINE |
| Opposing-behavior detections | 4 CRITICAL / FREEZE_PATCH across full evaluation |
| Prototype release ready | ✅ Cleared |

---

### Evaluation Repositories — Attribution and Scope

The 8 open-source Python repositories used in evaluation are cited as 
public test corpora under their respective licenses. The audit findings 
describe V2's behavior on these codebases, not the quality of the 
upstream code. All evaluation reports include the precise commit/version 
state at evaluation time, and reproducibility instructions are provided 
so any third party can verify V2's behavior independently. We thank the 
maintainers of these open-source projects for the codebases.

# 🎯 Problem V2 Addresses

V1 demonstrated that rule-based safe-merge reasoning can identify dangerous duplicate merges with no false positives observed during V1 evaluation. V2 addresses three remaining gaps:

1. **Semantic blindness.** V1 detects structural similarity but cannot reason about meaning. Two functions with identical structure but opposite semantics (e.g., `commit` vs `savepoint_commit`) look identical to V1.

2. **Behavioral blindness.** V1 does not classify what a function *does* (file write, database operation, deletion, backup). Risk varies enormously by behavior.

3. **Pre-modification governance.** V1 is invoked when a duplicate is suspected. V2 runs as a deterministic gate on any candidate change, before modification is attempted.

---

# 🧠 What V2 Adds Beyond V1

V1 contributes:

* Structural duplicate detection
* Cross-file dependency tracking
* Business-rule conflict detection
* Safe merge execution with backup

V2 adds, on top of V1:

✅ Semantic similarity analysis using sentence-transformer embeddings (no LLM)
✅ Behavioral signature classification (FILE_WRITE, DELETE_OPERATION, BACKUP_OPERATION, AUTH_OPERATION, etc.)
✅ Multi-signal fusion combining semantic + behavioral + risk scores
✅ Repository graph engine for pair candidate selection
✅ Decision orchestrator that wires the engines end-to-end
✅ Multi-repository evaluation methodology

Core philosophy carried from V1:

```text
same structure ≠ safe merge
```

Extended in V2 to:

```text
similar names + different behavior = governance review required
```

---

# ⚙️ V2 Pipeline (5 layers, 14 components)

```text
Layer 1 - Scanner
    └─ Repository Graph Engine

Layer 2 - Governance
    └─ Rule-Based Checks (global mutation, dangerous API)

Layer 3 - Orchestration
    ├─ Decision Orchestrator (semantic + behavioral + fusion + risk)
    ├─ V2 Orchestrator (master controller)
    ├─ Approval Engine
    ├─ V1 Adapter
    ├─ Fallback Orchestrator
    └─ Safe Execution Engine

Layer 4 - Patch Workflow
    ├─ Patch Generation (deterministic templates)
    ├─ Patch Validation
    ├─ Risk Classification
    └─ Test Execution

Layer 5 - AI Gateway (V3 scaffolding, disabled in V2)
    └─ ai_interface.py
```

Execution flow:

```text
Scan
→ Build Repository Graph
→ Decision Pipeline (Semantic → Behavioral → Fusion → Risk)
→ Governance Scan (rule-based)
→ V1 Adapter (duplicate detection ground truth)
→ Fallback Routing
→ Memory Update
→ Report Generation
```

---

# 🔍 V2 Capabilities

* All V1 detection capabilities (carried forward)
* Semantic similarity scoring on function pairs
* Behavioral signature classification (10+ categories)
* Multi-signal fusion with opposing-behavior detection (BACKUP ↔ RECOVERY, FILE_WRITE ↔ DELETE)
* SAFE / REVIEW / BLOCK decisions with governance action routing
* Repository-graph-based candidate pair extraction
* Multi-repository evaluation methodology

---

# 🛡️ Safety Features

All V1 safety features carried forward, plus:

* Conservative-default fusion (BLOCK when signals conflict)
* Reconciled governance actions (REVIEW never auto-applies)
* Test-pair filtering (avoids cross-test false positives)
* Backup-file skip (avoids analyzing archived code)
* Deterministic engines (no LLM dependency in decision path)

---

# 🧪 V2 Multi-Repository Evaluation

V2 was evaluated on 8 open-source Python repositories totalling 7,862 files. V1's 20 passing test cases (plus 2 by-design exclusions) continue to pass; V2's contribution was evaluated by:

1. Running V2's governance scanner on each repository
2. Running V2's decision pipeline on candidate function pairs
3. Comparing against V1's duplicate detection as ground truth where applicable

### Results

| Repo | Files | Gov Findings | Gov BLOCKs | Pipeline Pairs | Pipeline BLOCKs | Opposing | Errors |
|---|---|---|---|---|---|---|---|
| Flask tutorial | 9 | 2 | 0 | 4 | 0 | 0 | 0 |
| click | 60 | 3 | 1 | 25 | 3 | 0 | 0 |
| httpx | 60 | 0 | 0 | 25 | 3 | 0 | 0 |
| Flask full | 83 | 4 | 2 | 25 | 8 | 0 | 0 |
| DRF | 154 | 2 | 1 | 50 | 24 | 0 | 0 |
| Rich | 213 | 14 | 4 | 37 | 9 | 0 | 0 |
| Django | 2,917 | 68 | 16 | 100 | 55 | 0 | 0 |
| transformers | 4,426 | 296 | 76 | 1,000 | 464 | **4** | 0 |
| **Total** | **7,862** | **386** | **99** | **1,241** | **563** | **4** | **0** |

Gov = governance layer (rule-based). Pipeline = decision pipeline (semantic + behavioral + fusion).
Pipeline BLOCKs include NOISE_FAMILY cases documented in `V2_BLOCK_PRECISION_AUDIT.md`.

### Candidate Extraction

V2 uses V1-driven candidate extraction as the primary source, with token-overlap heuristic as fallback. In this evaluation, V1 found zero duplicates across all 8 repositories within the 25-file sampling cap, so token-overlap fallback was active in all runs. On repositories where V1 detects duplicates, V1-driven extraction replaces the heuristic entirely.

### Pipeline Error Rate

Zero pipeline errors across 1,241 pair analyses spanning repositories from 9 to 4,426 files. The pipeline completed without failure at all tested scales.

---

# 🔬 V2 BLOCK Precision Audit

A 14-pair audit of V2 BLOCK and opposing-behavior decisions was conducted across 3 groups, classifying each as:

* **GENUINE** — real semantic / behavioral distinction worth surfacing
* **NOISE_FAMILY** — decorator / factory family, technically correct but no merge intent
* **NOISE_EMBEDDING** — embedding model limitation

### Methodology

* **Group A (5 pairs)** — picked across click, DRF, Django for diversity (decorator families, helper families, transaction code, security code)
* **Group B (5 pairs)** — randomly selected from transformers BLOCK decisions (`random.seed(20260603)`)
* **Group C (4 pairs)** — all opposing-behavior detections (`fusion_opposing_detected: true`) across the full 8-repo evaluation, included exhaustively
* Each pair classified by reading actual upstream source code
* 3 of 10 original classifications independently verified by author (3/3 confirmed)

### Results — Groups A+B (sampled BLOCKs)

| Category | Count | Percentage | What this means |
|---|---|---|---|
| Governance-significant distinctions | 6 | 60% | Real semantic / behavioral differences worth surfacing for review |
| Family-pattern distinctions | 3 | 30% | Decorator / factory family members; BLOCK is technically correct but low governance value |
| Embedding-model limitations | 1 | 10% | Bodies differ but functions are closely related; embedding under-scores similarity |

### Results — Group C (opposing-behavior detections, exhaustive)

All 4 opposing-behavior detections classified GENUINE. All 4 carry `governance_action: FREEZE_PATCH` — the highest governance action level. Representative example:

```text
update_version_in_file ↔ update_version_in_examples    (utils/release.py)
Semantic score: 0.70   Fusion risk: CRITICAL   Action: FREEZE_PATCH
Tags A: FILE_READ, FILE_WRITE, STATE_MUTATION
Tags B: DELETE_OPERATION

Names are similar; semantic score alone would not block.
Behavioral opposition — one rewrites files, the other deletes — triggers FREEZE_PATCH.
```

This pair demonstrates the core value of multi-signal fusion: semantic similarity alone scores 0.70 (similar-looking names), but the opposing behavioral profiles correctly surface a governance-significant distinction that name-matching cannot catch.

### Behavioral Engine Scope

The behavioral engine classifies functions by detectable operations in their AST: FILE_READ, FILE_WRITE, DELETE_OPERATION, STATE_MUTATION, DATABASE_OPERATION, AUTH_OPERATION, NETWORK_CALL, PROCESS_OPERATION, OBJECT_CREATION, BACKUP_OPERATION. Functions with no detectable operations of these types receive empty behavioral tags (`[]`) — this is correct behavior, not a gap. Decorators, boolean predicates, and pure-computation functions commonly receive empty tags. Empty tags contribute LOW behavioral risk to the fusion score.

### Honest Interpretation

60% of sampled V2 BLOCK decisions represent governance-significant semantic distinctions. The remaining 40% are not "false positives" in a traditional sense — they are technically-correct BLOCK decisions on function pairs with no merge intent. 30% are members of intentionally-distinct decorator and factory families; 10% reflect embedding-model limitations.

The NOISE_FAMILY proportion is highest on codebases with large naming families 
(DRF's decorator configurators, httpx's encode_* family, transformers' 
weight-initialization registry). This is documented, expected, and planned 
for calibration in a future release.

### Audit Provenance

Source-code reading was AI-assisted (reading upstream open-source repositories directly), with author verification on 3 of 10 original classifications (3/3 confirmed). All classifications, function pairs, and reasoning are documented in `V2_BLOCK_PRECISION_AUDIT.md`. The reproducibility seed (`random.seed(20260603)`) is published with the repository.

### Caveats

* Groups A+B sample size 10 produces a wide confidence interval
* Single-reviewer audit; inter-rater agreement not measured
* Repositories audited skew toward framework code with decorator families; application code may show different distributions

---

# 🏗️ Repository Structure (V2)

```text
CodeTruthAgent/
│
├── ai/
│   ├── repository_graph_engine.py       ← Layer 1: Scanner
│   ├── governance_wiring.py             ← Layer 2: Rule-based checks
│   ├── decision_orchestrator.py         ← Layer 3: Semantic + Behavioral + Fusion + Risk
│   ├── v2_orchestrator.py               ← Layer 3: Master controller
│   ├── semantic_decision_engine.py      ← Semantic similarity
│   ├── behavioral_signature_engine.py   ← Behavioral classification
│   ├── fusion_engine.py                 ← Multi-signal fusion
│   ├── embedding_similarity.py
│   ├── lexical_prefilter.py
│   ├── purpose_analysis_engine.py
│   ├── risk_classification_engine.py    ← Layer 4
│   ├── patch_generation_engine.py
│   ├── patch_validation_engine.py
│   ├── test_execution_engine.py
│   ├── incremental_change_engine.py
│   ├── fallback_orchestrator.py
│   ├── v1_adapter.py
│   ├── ai_interface.py                  ← Layer 5 (V3 scaffolding, disabled)
│   └── llm_adapter.py                   ← V3 scaffolding, disabled
│
├── core/                                ← V1 components (preserved)
│   ├── duplicate_detector.py
│   ├── parser.py
│   ├── dependency_tracker.py
│   ├── risk_analyzer.py
│   ├── merge_advisor.py
│   ├── code_modifier.py
│   ├── memory_store.py
│   ├── quality_checker.py
│   └── project_scanner.py
│
├── validation/
│   ├── approval_engine.py               ← HITL approval API
│   ├── safe_execution_engine.py         ← Backup + execute + rollback
│   ├── rollback_manager.py
│   └── syntax_validator.py
│
├── memory/
│   └── governance_memory_engine.py
│
├── reporting/
│   └── report_generator.py
│
├── tests/
│   └── intelligence/
│       ├── orchestration/               ← V2 orchestration tests
│       ├── fusion_tests/                ← TC_V2_044, TC_V2_045, TC_V2_047
│       ├── semantic_validation/         ← TC_V2_042 series
│       ├── behavioral_validation/       ← TC_V2_043
│       └── output/v2/v2_1_repo_evaluation/   ← 8-repo evaluation reports
│
└── docs/
    ├── CodeTruth_V2_Project_Overview.docx
    └── V2_REFERENCE_STATE.md
```

---

# 🚀 Installation

## Prerequisites

* Python 3.11+
* `sentence-transformers` (for semantic engine)
* No LLM API keys required

```bash
git clone https://github.com/ZeeshanSaud/CodeTruthAgent.git
cd CodeTruthAgent
pip install -r requirements.txt
```

# ▶️ Run

## Full V2 Pipeline on a Repository

```bash
python -m ai.v2_orchestrator
```

## Evaluate V2 on an External Repository

```bash
python -m tests.intelligence.fusion_tests.tc_v2_047_repo_evaluation <repo_path> <pair_cap>
```

Example:

```bash
python -m tests.intelligence.fusion_tests.tc_v2_047_repo_evaluation C:/repos/django/django 100
```

Output: `tests/output/v2/v2_1_repo_evaluation/<repo_name>_report.json`

---

# 💡 Example V2 Workflow

```text
Scan repository
→ Build function-pair candidates (token-overlap heuristic)
→ For each candidate pair:
   → Semantic similarity (embedding model)
   → Behavioral classification (AST analysis)
   → Fusion decision (SAFE / REVIEW / BLOCK)
   → Risk classification (LOW / MEDIUM / HIGH / CRITICAL)
   → Governance action (AUTO_APPLY / BATCH_APPROVAL / INDIVIDUAL_APPROVAL / FREEZE_PATCH)
→ Governance rule-based scan
→ V1 duplicate detection (ground truth)
→ Memory update
→ Report
```

---

# ⚠️ Known Limitations (V2)

* **Decorator-family noise.** On codebases with decorator factory families (click's `*_option`, transformers' `require_*`), V2 produces elevated BLOCK rates that are technically correct but provide low governance value
* **Embedding model bottleneck.** `all-MiniLM-L6-v2` has known limitations on cross-domain semantic pairs; some functionally-similar pairs receive low similarity scores
* **Behavioral over-tagging.** Functions that call `findings.append(...)` are uniformly tagged `STATE_MUTATION + OBJECT_CREATION`
* **Programmatic HITL only.** Approval API and audit logging exist; an interactive reviewer UI does not (V3 scope)
* **Patch generation is deterministic-template only.** Four predefined patch templates; no LLM-driven patch generation (V3 scope)
* **Single-reviewer precision audit.** Inter-rater agreement not measured
* **V1's audit caveats carried forward.** Single-reviewer 0% FP claim on V1 governance findings

---

# 🔮 What's Next — V3 Scope

V2 is the deterministic governance gate. V3 will build on top of V2's governance foundation to add:

* LLM-driven patch generation (using V2's risk gates as guardrails)
* Interactive HITL reviewer UI
* Real-time CI/CD integration
* Behavioral engine calibration — family-pattern suppression at candidate level
* Multi-language support beyond Python

V2 is designed so V3's LLM-driven autonomous modification can be added without changing V2's governance contract.

---

# 📚 Research Positioning

CodeTruth Agent V2 represents:

* An open-source implementation of deterministic pre-modification code governance for Python
* An evaluated baseline of 22 audited BLOCK findings reproduced exactly across an 8-repository corpus
* A characterization of where deterministic semantic + behavioral analysis adds value vs where it produces structural over-flagging on framework-style codebases
* A research foundation for governance-gated AI-driven code modification (V3)

V2 demonstrates that:

```text
deterministic semantic + behavioral analysis
+
rule-based governance
+
HITL approval infrastructure
```

can serve as a governance layer for code modifications without requiring LLM reasoning in the decision path.

---

# 🤖 AI-Assisted Development Note

V2's test scenarios, source-code audits, and architectural reviews were developed with AI-assisted iteration, primarily through pair-programming with reasoning assistants. The 14-pair BLOCK precision audit involved AI-assisted reading of upstream open-source repositories, with author spot-check verification on a subset of classifications (3 of 10 original pairs confirmed against actual source code).

Final implementation, integration testing, multi-repository evaluation, and governance-discipline framing were manually reviewed by the author. AI assistance was used to accelerate code reading and architectural reasoning, not to fabricate evidence or decisions.

---

# 📄 License & Commercial Rights

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.

---

## Disclaimer

This document is provided for research, educational, and open-source 
collaboration purposes. It does not constitute legal advice, formal 
benchmark claims, or commercial product comparisons. Category descriptions 
of adjacent tooling are illustrative based on a June 2026 landscape review 
and reflect the author's understanding at that time; the AI tooling space 
evolves rapidly and may have changed since this writing. Evaluation 
findings describe V2's behavior on the cited open-source repositories at 
the evaluation timestamp, and are not judgments on the quality, design, 
or correctness of the upstream codebases. All software is released under 
GPLv3 as-is, without warranty of any kind.

---

### 🛡️ Open Source Usage

You are free to copy, modify, and distribute this software under the condition that any derivative works, extensions, or integrated modules (including V3 LLM-driven extensions or multi-language ports) are also released under the same GPLv3 terms.

### 💼 Enterprise & Commercial Licensing

The GPLv3 license is designed to protect this architecture from being consumed into closed-source commercial software. If your organization wishes to:

* Integrate CodeTruth V2's governance pipeline into closed-source commercial products
* Deploy this architecture internally without open-sourcing modifications
* Collaborate on proprietary enterprise implementations of V3

**You must obtain a commercial license.**

### ⚖️ Patent Non-Infringement Clause

Same patent terms as V1 carry forward to V2. Section 11 of GPLv3 applies.

* **Author:** Zeeshan Saud
* **Inquiries:** zeeshansaud786@gmail.com

---

# 👨‍💻 Author

Zeeshan Saud
CodeTruth Agent V2
Deterministic Pre-Modification Governance Layer
June 2026