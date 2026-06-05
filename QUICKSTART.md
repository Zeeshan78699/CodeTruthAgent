# CodeTruth Agent V2 — Quick Start

Get V2 running on a real codebase in 5 minutes.

---

## Prerequisites

- Python 3.11 or newer
- Git
- ~500MB free disk space (for the embedding model cache + sample repos)

Verify your Python version:

```bash
python --version
```

If it reports Python 3.10 or older, install Python 3.11+ before continuing.

---

## Step 1 — Clone and Install (2 minutes)

```bash
# Clone the repository
git clone https://github.com/ZeeshanSaud/CodeTruthAgent.git
cd CodeTruthAgent

# Install dependencies
pip install -r requirements.txt
```

The first install downloads the `sentence-transformers` package and prepares
the embedding model. The model itself (~90MB) is downloaded on first use,
not at install time.

---

## Step 2 — First Run on V2's Own Codebase (2 minutes)

This runs the V2 pipeline against V2's own source tree as a smoke test.

```bash
python -m ai.v2_orchestrator
```

Expected output (first time will be slower because the model has to download):

```
Loading weights: 100%|████████████| 103/103 [00:00<00:00, 6244.68it/s]

======================================================================
CODETRUTH V2 ORCHESTRATOR
======================================================================

[STEP 1]
Building Repository Graph

[STEP 2]
Running Decision Pipeline on Real Function Pairs
  Analyzing 25 function pair(s) (capped from 25)
  [1] compute_bill_amount <-> compute_factorial: BLOCK (MEDIUM)
  [2] factorial_number <-> compute_factorial: SAFE (LOW)
  [3] apply_customer_discount <-> apply_supplier_discount: SAFE (LOW)
  ...
  [25] split_name <-> get_name_intent: REVIEW (MEDIUM)

[STEP 3]
Running Governance Scan

[STEP 4]
Running V1 Adapter

[STEP 5]
Evaluating Fallback Routing

[STEP 6]
Updating Memory

[STEP 7]
Generating Report
```

**Total runtime:** ~3 minutes (first run includes one-time model download).
Subsequent runs take about 1 minute on V2's own codebase.

**Report saved to:**

```
tests/output/v2/v2_orchestrator_report.json
```

---

## Step 3 — Run V2 on an External Repository (1 minute setup + run time)

Use the `tc_v2_047_repo_evaluation` script to evaluate any Python repo.

```bash
# Example: evaluate the Flask tutorial
git clone https://github.com/pallets/flask C:\repos\flask
python -m tests.intelligence.fusion_tests.tc_v2_047_repo_evaluation \
    C:\repos\flask\examples\tutorial \
    25
```

The arguments are:

```
<repo_path>      Path to the Python repository you want to evaluate
<pair_cap>       Maximum function pairs to analyze (25 = quick, 100 = thorough)
```

**Report saved to:**

```
tests/output/v2/v2_1_repo_evaluation/<repo_name>_report.json
```

---

## What Success Looks Like

A clean V2 run produces a JSON report with this structure:

```json
{
    "repository_files": 194,
    "governance_findings": 19,
    "safe": 0,
    "review": 12,
    "block": 7,
    "v1_findings": 9,
    "decision_pipeline_pairs_analyzed": 25,
    "decision_pipeline_safe": 5,
    "decision_pipeline_review": 13,
    "decision_pipeline_block": 7,
    "decision_pipeline_errors": 0,
    "status": "PASSED"
}
```

Three key indicators of a healthy run:

1. **`decision_pipeline_errors: 0`** — pipeline completed without crashes
2. **`status: "PASSED"`** — overall run succeeded
3. **A mix of SAFE / REVIEW / BLOCK in decision_pipeline_*** — engines are
   discriminating between pair types (not all one category)

---

## Understanding the Decision Categories

For each analyzed function pair, V2 outputs one of:

| Decision | What it means | Suggested action |
|---|---|---|
| **SAFE** | Functions are similar in safe ways — merge candidate is low-risk | Auto-apply may proceed |
| **REVIEW** | Functions look similar but require human judgment | Route to human approval |
| **BLOCK** | Functions are too different to safely merge OR have opposing behaviors | Reject merge candidate |

V2 conservatively defaults to BLOCK when signals conflict. This is by design:
**better to surface a false alarm than miss a real conflict.**

---

## Where to Go Next

- **Read [`README.md`](./README.md)** for the full architecture and methodology.
- **Read [`V2_BLOCK_PRECISION_AUDIT.md`](./V2_BLOCK_PRECISION_AUDIT.md)** for
  the 14-pair audit with reasoning for each classification.
- **Explore `tests/output/v2/v2_1_repo_evaluation/`** to see V2's behavior on
  8 different open-source repositories.

---

## Common Issues — Troubleshooting

### "ModuleNotFoundError: No module named 'sentence_transformers'"
You skipped `pip install -r requirements.txt`. Run it.

### First run hangs at "Loading weights"
The embedding model is downloading (~90MB on first use). Be patient on the
first run; subsequent runs use the local cache and start instantly.

### "FileNotFoundError: Repository not found"
The path you passed to `tc_v2_047_repo_evaluation` doesn't exist or is not a
directory. Double-check with `ls` (or `dir` on Windows) before re-running.

### Run finishes but `decision_pipeline_pairs_analyzed: 0`
The repository may have too few function pairs that share tokens, or the
pair cap is too low. Try increasing the pair cap (e.g., 100) or running on
a larger codebase.

### Reports keep appending; how do I start fresh?
Delete `tests/output/v2/` and the run will regenerate it. Memory files
(`memory_v2.json`, `governance_memory.json`) can be reset by replacing
with their `_template.json` counterparts.

---

## Performance Notes

| Repository | Files | Approximate runtime |
|---|---|---|
| Small (≤50 files) | e.g. Flask tutorial | 5–15 seconds |
| Medium (50–200 files) | e.g. click, httpx, DRF, Rich | 15–60 seconds |
| Large (200–3000 files) | e.g. Flask full, Django | 1–3 minutes |
| Very large (3000+ files) | e.g. transformers (4,426 files, 1,000 pairs) | 5–10 minutes |

The decision pipeline is bounded by the `pair_cap` parameter. On large
codebases, V2 selects up to `pair_cap` candidate pairs to analyze rather
than analyzing every possible pair.

---

## License and Disclaimer

CodeTruth Agent V2 is released under **GNU GPLv3**. See [`LICENSE`](./LICENSE)
for the full text.

This software is provided as-is, without warranty of any kind. See the
disclaimer section in [`README.md`](./README.md) for scope and limitations.
