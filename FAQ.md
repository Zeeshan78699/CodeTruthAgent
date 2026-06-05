# CodeTruth Agent V2 — FAQ

Common questions about V2's design, scope, behavior, and limitations.

---

## What V2 Is and Isn't

### What problem does V2 solve?

V2 decides whether a candidate code change should be applied to a Python
repository — **before any modification is attempted**. It produces a
SAFE / REVIEW / BLOCK decision for each candidate function-pair, backed
by deterministic semantic and behavioral analysis.

### Is V2 an AI code review tool?

No. AI code review tools (which post comments on PRs after code is written)
use LLMs to read diffs and generate natural-language feedback. V2 is a
**pre-modification gate** that runs before patches reach the codebase, and
uses deterministic embeddings — not LLMs — in the decision path.

### Is V2 a security scanner (SAST)?

No. SAST tools scan for known vulnerability patterns from established
taxonomies (CWE, OWASP). V2 analyzes semantic and behavioral similarity
between function pairs to decide if they're safe to merge or modify
together. Different problem, different output.

### Why no LLM in the decision path?

Three reasons:

1. **Explainability** — every V2 decision can be traced to specific
   engine signals (semantic score, behavioral tags, fusion logic).
2. **Reproducibility** — same input produces same output, every time.
3. **Cost** — V2 has no per-call API cost.

LLM scaffolding exists in V2's codebase (`ai/ai_interface.py`,
`ai/llm_adapter.py`) but is disabled. LLM integration is V3 scope.

### What languages does V2 support?

Python only. V2's parser is built on Python's standard `ast` module.
Multi-language support is V3 scope.

---

## Installation and Setup

### What Python version is required?

Python 3.11 or newer. Some V2 modules use match-case statements and
modern type-hint syntax that require 3.11+.

### Do I need an OpenAI / Anthropic / Google API key?

No. V2 has no LLM API dependencies.

### How big is the embedding model download?

Approximately 90MB for `sentence-transformers/all-MiniLM-L6-v2`.
Downloaded once to your local cache and reused for every subsequent run.

### Can I use a different embedding model?

The current release is configured for `all-MiniLM-L6-v2`. Swapping the
embedding model is an open research question — different models would
produce different semantic scores, which would require recalibration of
the fusion thresholds. This is documented as future calibration work.

### Will V2 send my code anywhere?

No. V2 runs entirely locally. The embedding model is downloaded once
from Hugging Face's model hub, then runs offline. No data is transmitted
externally during evaluation.

---

## Running V2

### How long does V2 take?

Depends on repository size:

| Repository size | Approximate runtime |
|---|---|
| <50 files | 5–15 seconds |
| 50–200 files | 15–60 seconds |
| 200–1000 files | 1–3 minutes |
| 1000+ files | 3–10 minutes |

The decision pipeline is bounded by the `pair_cap` parameter. Larger
caps produce more analyses but take longer.

### Where are the output reports?

Three locations:

- **V2 orchestrator runs (V2's own codebase):**
  `tests/output/v2/v2_orchestrator_report.json`
- **External repository evaluations:**
  `tests/output/v2/v2_1_repo_evaluation/<repo_name>_report.json`
- **Per-test reports:**
  `tests/output/v2/<test_category>_reports/<test_id>_report.json`

### How do I evaluate V2 on my own repository?

```bash
python -m tests.intelligence.fusion_tests.tc_v2_047_repo_evaluation \
    /path/to/your/repo \
    50
```

Replace `50` with your desired pair cap. Use 25 for fast smoke testing,
100 for thorough evaluation.

### Can I run V2 in CI/CD?

Yes — V2 is a Python CLI that returns JSON. Integration with CI/CD is
straightforward, but CI-specific tooling (GitHub Actions integrations,
GitLab CI hooks, etc.) is not yet packaged. Pull requests welcome.

---

## Interpreting Results

### What do SAFE, REVIEW, and BLOCK mean?

For each candidate function pair V2 analyzes:

- **SAFE** — Functions are similar in low-risk ways. Suggested governance
  action: AUTO_APPLY.
- **REVIEW** — Functions look similar but human judgment is needed.
  Suggested governance action: BATCH_APPROVAL or INDIVIDUAL_APPROVAL.
- **BLOCK** — Functions are too different to safely merge, OR they have
  opposing behaviors (e.g., one backs up while the other deletes).
  Suggested governance action: FREEZE_PATCH or escalated review.

### What does the 60% precision number mean?

In a 14-pair audit of V2 BLOCK and opposing-behavior decisions:

- **60%** of sampled BLOCK decisions (Groups A+B, 10 pairs) were classified
  as governance-significant distinctions worth surfacing (real semantic or
  behavioral differences).
- **30%** were family-pattern distinctions — technically correct but no
  merge intent in the first place (e.g., decorator factories, encode_* families).
- **10%** were embedding-model limitations — functions are closely related
  but the model under-scored similarity.

All 4 opposing-behavior detections (Group C, exhaustive)
were classified GENUINE — all carry `FREEZE_PATCH` governance action.

The 40% that aren't governance-significant are **not false positives**.
They are correct BLOCK decisions on pairs that nobody was going to merge
anyway. See `V2_BLOCK_PRECISION_AUDIT.md` for full reasoning.

### Why does V2 BLOCK pairs that look obviously different?

Two reasons:

1. **Conservative default** — when fusion signals conflict, V2 defaults to
   BLOCK to surface the pair for human review rather than risk a wrong
   AUTO_APPLY.
2. **Token-overlap pair extraction** — V2's pair selection currently uses
   shared naming tokens, which can pull in pairs that share a token but
   are functionally unrelated. This is documented as future calibration
   work (use V1's duplicate-detection output as candidate source).

### Why didn't V2 catch [some specific case]?

Common reasons:

- **The functions don't share enough naming tokens** → V2's candidate
  selection didn't pair them. Increase `pair_cap` or use a different
  candidate-extraction strategy.
- **The semantic difference is subtle and the embedding model rates them
  as similar** → known embedding-model limit; see audit document.
- **The functions are in test files** → V2 deliberately filters
  test-to-test pairs.
- **The functions are in backup or archive files** → V2 deliberately
  skips `.bak`, `_old`, etc.

---

## Limitations and Honest Scope

### What can V2 NOT do?

- V2 cannot generate patches autonomously (V3 scope).
- V2 has no interactive human-in-the-loop UI (V3 scope).
- V2 cannot govern non-Python code (V3 scope).
- V2 cannot replace LLM-based PR review for design or stylistic concerns.
- V2 cannot guarantee zero false positives.

### Why is the precision audit only 14 pairs?

A 14-pair audit (10 sampled + 4 exhaustive opposing-behavior detections)
was the deliberate scope chosen for V2's initial release — balancing audit
credibility against author time investment for a single-reviewer audit.
A larger audit (50–100 pairs) with multi-reviewer inter-rater agreement
is documented as future calibration work.

### Was the audit really single-reviewer?

Yes. Three of ten classifications were independently re-verified by the
author against local repository source code (3/3 confirmed). The other
seven rely on AI-assisted code reading only. This methodology is fully
documented in `V2_BLOCK_PRECISION_AUDIT.md`.

### How were the 8 evaluation repositories chosen?

To span codebase sizes (9 to 4,426 files), function-family patterns
(decorator-heavy click, encoder-heavy httpx, transaction-heavy Django,
model-heavy transformers), and to include both small targets (Flask
tutorial) and large production codebases (Django, transformers).

The repositories are not a random sample of all Python projects — they
skew toward framework/library code. Application code may show different
patterns. This is documented as a caveat in the audit and README.

---

## Architecture

### How does V2 differ from V1?

V1 was the first release: a rule-based safe-merge reasoning system that
identified duplicate functions and applied conservative merge governance.
V2 adds three new analysis stages on top of V1:

1. **Semantic similarity** — embedding-based scoring of function pairs
2. **Behavioral signatures** — AST-based classification of what functions
   do (FILE_WRITE, DELETE_OPERATION, BACKUP_OPERATION, etc.)
3. **Multi-signal fusion** — combines semantic + behavioral + risk scores
   into a single SAFE/REVIEW/BLOCK decision with conservative defaults.

V1 remains in V2 as the duplicate-detection ground truth, exposed via
`ai/v1_adapter.py`.

### What is the decision orchestrator?

`ai/decision_orchestrator.py` (class `DecisionOrchestrator`) is the layer
that wires the four engines together: semantic, behavioral, fusion, risk.
It exposes two methods:

- `analyze_function_pair(file_path, function_a, function_b)` — production
  entry point. Reads code, invokes all four engines, returns a decision.
- `analyze_signals(...)` — testing entry point. Accepts pre-computed
  signals for unit-testing fusion logic in isolation.

### Why is V2 deterministic instead of using an LLM?

Deterministic governance gates are:

- **Auditable** — every decision can be explained from the engine signals.
- **Reproducible** — same input produces same output across runs.
- **Cost-bounded** — no per-call API charges.
- **Independent of LLM availability** — works in air-gapped environments.

V3 will integrate LLM capabilities for patch generation and interactive
review, but the **governance gate itself** will remain deterministic.

---

## Contributing

### Can I contribute?

Yes — V2 is GPLv3 open source. Pull requests, issue reports, and feedback
are welcome via the GitHub repository.

### What areas need help most?

Documented in the README under "What's Next — V3 Scope" and in the
`Limitations` section:

- Behavioral engine family-pattern calibration (V2.3 — suppressing
  decorator/naming-family noise at candidate selection stage)
- Multi-reviewer precision audit expansion (50–100 pairs)
- Interactive HITL reviewer UI
- CI/CD integration packaging
- Multi-language support beyond Python

### Will my contributions be GPLv3?

Yes. Per GPLv3's terms, contributions become part of the GPLv3-licensed
project. If you need a different license for your use case, the project
offers commercial licensing — see the README for details.

---

## License and Legal

### What license is V2 released under?

**GNU General Public License v3.0 (GPLv3).** Full license text in
[`LICENSE`](./LICENSE).

### Can I use V2 in a commercial product?

GPLv3 permits commercial use. However, any derivative work must also be
released under GPLv3 (and made open source). If you need to integrate V2
into proprietary commercial software without open-sourcing your
modifications, a commercial license is available — contact the author.

### Is V2 safe for regulated industries (finance, healthcare, etc.)?

V2 is designed for governance use cases including regulated environments.
It runs entirely locally, has no external API calls, produces auditable
deterministic decisions, and maintains a complete audit trail. However,
**V2 is research prototype software** released under GPLv3 as-is, without
warranty. Compliance certification (SOC 2, HIPAA, FedRAMP, etc.) is the
deploying organization's responsibility.

### Are evaluation findings about open-source projects defamatory?

No. V2's audit findings (e.g., classifications of function pairs in click,
DRF, Django, transformers, etc.) describe V2's behavior on these
codebases at the evaluation timestamp. They are not judgments on the
quality, design, or correctness of the upstream code. The
**Attribution and Scope** section in both the README and the audit
document makes this explicit.

---

## Disclaimer

This FAQ is provided for educational and open-source collaboration
purposes. It does not constitute legal advice, formal benchmark claims,
or commercial product comparisons. All software is released under GPLv3
as-is, without warranty of any kind.
