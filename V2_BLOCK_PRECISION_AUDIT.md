# V2 BLOCK Precision Audit

**Sample size:** 14 BLOCK / OPPOSING decisions
**Reviewer:** Zeeshan Saud
**Audit methodology:** AI-assisted source-code reading with author spot-check verification
**Date:** June 2026
**Status:** Complete — V2 refresh

---

## Methodology

14 decisions sampled from V2's decision-pipeline runs across 6 repositories.
Sample composition:

- **Group A (5 picked for diversity):** Across click, DRF, Django. Picked to
  span decorator families, helper families, transaction code, and security
  code. Reviewer-selected, not random.

- **Group B (5 random from transformers):** Selected with
  `random.seed(20260603)` from 464 transformers BLOCK decisions, for
  reproducibility and to defend against cherry-pick claims on the most
  numerous BLOCK pool.

- **Group C (4 opposing-behavior detections from transformers):** All 4 pairs
  where V2's fusion engine raised `fusion_opposing_detected: true` across the
  full 8-repo evaluation. Included in full because opposing-behavior detection
  is a distinct V2 capability; exhaustive inclusion removes any selection bias
  concern for this category.

**Classifications:**

| Code | Meaning |
|---|---|
| GENUINE | A real semantic / behavioral distinction. Naive merge would cause a bug. The BLOCK is useful governance signal. |
| NOISE_FAMILY | Decorator / factory / helper family. Shares a token by design but each member has an intentionally distinct purpose. No merge intent. BLOCK is technically correct but low governance value. |
| NOISE_EMBEDDING | The embedding model rates the pair as different; a human would call them similar enough to at least review. Model limitation. |
| UNCERTAIN | Could not classify cleanly. |

**Caveats up front:**

- Single-reviewer audit. Inter-rater agreement not measured. Same
  methodological caveat as V1's original UAT process.
- Sample size 14 gives a wide confidence interval; the precision number is a
  point estimate, not a high-confidence proportion.
- Group A is reviewer-selected (not random). Group B is randomly sampled.
  Group C is exhaustive (all opposing detections).
- Source-code reading was AI-assisted (reading upstream open-source
  repositories on GitHub). Author independently verified 3 of 10 original
  classifications by opening local repository files; 3/3 verifications
  confirmed the classifications. Group C classifications rely on
  AI-assisted reading plus behavioral tag evidence from the pipeline output.

---

## Evaluation Repositories — Attribution and Scope

The open-source Python repositories from which BLOCK decisions were sampled
are cited as public test corpora under their respective licenses. The audit
findings describe V2's behavior on these codebases, not the quality of the
upstream code. All evaluation reports include the precise run state at
evaluation time, and reproducibility instructions are provided so any third
party can verify V2's behavior independently. We thank the maintainers of
these open-source projects for the codebases.

---

## Audit

For each pair: the actual source file in the upstream repository was read,
both function bodies were examined, and the classification was made on what
the code does.

---

### Group A — Diversity Sample (5 pairs)

#### 1. click :: `option ↔ password_option`

- **Repository:** pallets/click
- **File:** `src/click/decorators.py`
- **Semantic score:** 0.43
- **Risk level:** MEDIUM
- **Classification:** ☑ NOISE_FAMILY
- **Reason:** `password_option` is a documented one-line shortcut that calls
  `option()` after setting password-prompt kwargs (`prompt=True`,
  `confirmation_prompt=True`, `hide_input=True`). The docstring says
  "Shortcut for password prompts." It is part of click's public API by
  design. Merging the two would destroy the public shortcut interface.
  V2's BLOCK is technically correct (function bodies differ) but provides
  no governance value because no developer would consider merging a
  shortcut wrapper into the function it explicitly delegates to.
- **Verification:** AI-assisted code read on GitHub upstream. Not
  independently verified by author.

#### 2. DRF :: `_get_error_details ↔ _get_full_details`

- **Repository:** encode/django-rest-framework
- **File:** `rest_framework/exceptions.py`
- **Semantic score:** 0.29
- **Risk level:** HIGH
- **Classification:** ☑ NOISE_FAMILY
- **Reason:** Both are internal error-handling helpers in DRF's exception
  system. `_get_error_details` recursively converts strings / dicts / lists
  into typed `ErrorDetail` objects (string normalizer). `_get_full_details`
  builds full error response dicts of the form `{"message": ..., "code": ...}`.
  Same naming prefix and same module, different responsibilities. Family
  members; no merge intent.
- **Verification:** AI-assisted code read on GitHub upstream. Not
  independently verified by author.

#### 3. Django :: `commit ↔ savepoint_commit`

- **Repository:** django/django
- **File:** `django/db/transaction.py` (lines 48–51 and 76–81)
- **Semantic score:** 0.63
- **Risk level:** CRITICAL
- **Classification:** ☑ GENUINE
- **Reason:** These execute fundamentally different SQL transaction operations.
  `commit()` calls `get_connection(using).commit()` — finalizes the entire
  outer transaction block and writes changes permanently.
  `savepoint_commit(sid, using=None)` calls
  `get_connection(using).savepoint_commit(sid)` — targets a specific nested
  savepoint identifier and maps (on backends like PostgreSQL) to
  `RELEASE SAVEPOINT`, which merges nested state into the parent while the
  outer transaction continues. Merging these would invert transaction
  semantics and could cause data corruption during partial-failure rollbacks.
  This is the canonical example of why governance-significant BLOCKs matter.
- **Verification:** ✅ Independently verified by author against local
  `django/db/transaction.py` source. Author confirmed line numbers and
  classification.

#### 4. Django :: `atomic ↔ _non_atomic_requests`

- **Repository:** django/django
- **File:** `django/db/transaction.py`
- **Semantic score:** 0.50
- **Risk level:** HIGH
- **Classification:** ☑ GENUINE
- **Reason:** Deliberately opposing decorators in Django's transaction API.
  `atomic` wraps code in a database transaction (enables transactional
  behavior). `_non_atomic_requests` decorator marks views that should NOT
  receive the per-request `ATOMIC_REQUESTS` wrapping (disables it). They
  share the "atomic" token and live in the same module, but their effects
  are inverse. Merging them would invert transaction-wrapping behavior on
  marked views.
- **Verification:** AI-assisted code read on GitHub upstream. Not
  independently verified by author.

#### 5. Django :: `_get_new_csrf_string ↔ _add_new_csrf_cookie`

- **Repository:** django/django
- **File:** `django/middleware/csrf.py`
- **Semantic score:** 0.64
- **Risk level:** HIGH
- **Classification:** ☑ GENUINE
- **Reason:** Two security-critical CSRF helpers operating at different layers.
  `_get_new_csrf_string` PRODUCES a new random CSRF secret string (value
  generation). `_add_new_csrf_cookie` CONSUMES a secret and ATTACHES the
  CSRF cookie to an outgoing response object (response modification). One
  is a generator; the other is a side-effecting writer. Merging them would
  lose either the secret-generation step or the response-modification step.
  Security-sensitive code where confusion would create real CSRF bugs.
- **Verification:** AI-assisted code read on GitHub upstream. Not
  independently verified by author.

---

### Group B — Random Sample from transformers (5 pairs)

Selected with `random.seed(20260603)` from 464 transformers BLOCK decisions.

#### 6. transformers :: `xavier_normal_ ↔ trunc_normal_`

- **Repository:** huggingface/transformers
- **File:** `src/transformers/initialization.py` (with backing in
  `src/transformers/modeling_utils.py::TORCH_INIT_FUNCTIONS`)
- **Semantic score:** 0.32
- **Risk level:** MEDIUM
- **Classification:** ☑ NOISE_FAMILY
- **Reason:** Both functions are entries in the same `TORCH_INIT_FUNCTIONS`
  registry and act as thin wrappers around `torch.nn.init.xavier_normal_`
  and `torch.nn.init.trunc_normal_` respectively. They are documented
  orthogonal members of PyTorch's weight-initialization API: Xavier/Glorot
  normal distribution vs truncated normal distribution. Different
  statistical strategies for the same broad domain (weight initialization)
  with no overlap in implementation purpose. No merge candidate.
- **Verification:** ✅ Independently verified by author against local
  source. Author confirmed both are wrappers around `torch.nn.init.*` and
  represent different statistical initializers.

#### 7. transformers :: `causal_mask_function ↔ _can_skip_causal_mask_xpu`

- **Repository:** huggingface/transformers
- **File:** `src/transformers/masking_utils.py`
- **Semantic score:** 0.57
- **Risk level:** MEDIUM
- **Classification:** ☑ GENUINE
- **Reason:** Different operations at different layers of the attention-mask
  pipeline. `causal_mask_function` returns a CALLABLE — a mask factory
  closure used to compute mask values per position. `_can_skip_causal_mask_xpu`
  returns a BOOLEAN — an optimization gate that decides whether mask
  construction can be skipped on XPU backends. Different return types,
  different stages of the pipeline (construction vs skip-optimization).
  Merging would conflate construction with skip logic.
- **Verification:** AI-assisted code read on GitHub upstream. Not
  independently verified by author.

#### 8. transformers :: `prepare_padding_mask ↔ create_causal_mask`

- **Repository:** huggingface/transformers
- **File:** `src/transformers/masking_utils.py`
- **Semantic score:** 0.39
- **Risk level:** MEDIUM
- **Classification:** ☑ GENUINE
- **Reason:** Both produce mask-related output but at different scopes.
  `prepare_padding_mask` is a helper that handles the padding portion of an
  attention mask (subset of mask responsibilities). `create_causal_mask`
  constructs the full causal mask tensor (the main mask). One is a helper
  for one mask component; the other is the primary constructor. Different
  responsibilities in the masking pipeline.
- **Verification:** AI-assisted code read on GitHub upstream. Not
  independently verified by author.

#### 9. transformers :: `_get_constant_lambda ↔ get_cosine_with_min_lr_schedule_with_warmup`

- **Repository:** huggingface/transformers
- **File:** `src/transformers/optimization.py`
- **Semantic score:** 0.12
- **Risk level:** MEDIUM
- **Classification:** ☑ NOISE_EMBEDDING (borderline; see reason)
- **Reason:** Both are LR-scheduling helpers, but at vastly different scopes.
  `_get_constant_lambda` is a trivial helper: `def _get_constant_lambda(_=None): return 1`
  (returns a constant LR multiplier). `get_cosine_with_min_lr_schedule_with_warmup`
  is a full LR-scheduler factory handling warmup steps, total training steps,
  cosine cycles, minimum LR floor, validation, partial lambda construction,
  and returns a `LambdaLR` object. The embedding model correctly rated them
  as different (0.12, lowest in sample). Classification as NOISE_EMBEDDING
  reflects that both ARE LR-scheduling helpers in the same family but
  governance value is low — no developer would consider merging a
  one-line constant with a multi-parameter scheduler. Borderline case
  between NOISE_FAMILY and NOISE_EMBEDDING; recorded as NOISE_EMBEDDING
  because the embedding model's low score is what governance acted on.
- **Verification:** ✅ Independently verified by author against local
  source. Author confirmed `_get_constant_lambda` is one-line `return 1`
  and the cosine scheduler is a complex multi-parameter factory.

#### 10. transformers :: `is_pipeline_test ↔ init_test_logger`

- **Repository:** huggingface/transformers
- **File:** `src/transformers/testing_utils.py`
- **Semantic score:** 0.31
- **Risk level:** HIGH
- **Classification:** ☑ GENUINE
- **Reason:** Predicate vs side-effecting initializer. `is_pipeline_test` is
  a BOOLEAN PREDICATE (reads state, returns whether this run is a pipeline
  test). `init_test_logger` is an INITIALIZER with side effects (creates
  and configures a logger object — V2's behavioral engine correctly tagged
  it `OBJECT_CREATION`). They share only the `test` domain token; their
  operational categories (read state vs write state) are fundamentally
  different. Merging would either drop the logger initialization or turn
  the predicate into a side-effecting call.
- **Verification:** AI-assisted code read on GitHub upstream. Not
  independently verified by author.

---

### Group C — Exhaustive Opposing-Behavior Detections (4 pairs)

All 4 pairs where V2's fusion engine raised `fusion_opposing_detected: true`
across the complete 8-repository evaluation. Included exhaustively to avoid
selection bias on this category.

All 4 pairs carry `governance_action: FREEZE_PATCH` — the highest governance
action level, triggered when opposing behavioral signatures are detected
alongside high semantic similarity.

#### 11. transformers :: `update_version_in_file ↔ update_version_in_examples`

- **Repository:** huggingface/transformers
- **File:** `utils/release.py`
- **Semantic score:** 0.70
- **Fusion risk score:** 90 / CRITICAL
- **Behavioral tags A:** FILE_READ, FILE_WRITE, STATE_MUTATION
- **Behavioral tags B:** DELETE_OPERATION
- **Classification:** ☑ GENUINE
- **Reason:** This is the strongest opposing-detection example in the full
  evaluation. Semantic score 0.70 — names are genuinely similar (both are
  version-update functions in the release script). But the behavioral
  signatures are opposite: `update_version_in_file` reads a file, rewrites
  its version string in place (FILE_READ + FILE_WRITE + STATE_MUTATION).
  `update_version_in_examples` performs deletions (DELETE_OPERATION only).
  An AI agent confusing these during an automated release operation would
  either skip version updates or trigger unintended deletions. The fusion
  engine's opposing-behavior detection is the only layer that catches this —
  semantic score alone would not block it. This pair demonstrates the core
  value of multi-signal fusion over name-similarity alone.
- **Verification:** AI-assisted code read on GitHub upstream. Behavioral
  tag evidence from pipeline output independently corroborates the
  classification.

#### 12. transformers :: `get_all_tests ↔ infer_tests_to_run`

- **Repository:** huggingface/transformers
- **File:** `utils/tests_fetcher.py`
- **Semantic score:** 0.56
- **Fusion risk score:** 100 / CRITICAL
- **Behavioral tags A:** DELETE_OPERATION
- **Behavioral tags B:** FILE_READ, FILE_WRITE, STATE_MUTATION
- **Classification:** ☑ GENUINE
- **Reason:** Both functions operate in the test-selection pipeline but at
  opposite ends of it. `get_all_tests` retrieves the list of all known test
  files — its DELETE_OPERATION tag indicates it clears or resets some
  intermediate state during collection. `infer_tests_to_run` performs
  the active inference: reads file dependencies (FILE_READ), writes
  intermediate results (FILE_WRITE), and mutates state (STATE_MUTATION).
  The behavioral inversion (DELETE vs READ+WRITE+MUTATE) correctly
  identifies these as operationally opposite. Fusion risk score 100 —
  the pipeline's highest possible score — reflects the full signal
  stack firing simultaneously.
- **Verification:** AI-assisted code read on GitHub upstream. Pipeline
  behavioral tags corroborate the classification.

#### 13. transformers :: `get_all_tests ↔ filter_tests`

- **Repository:** huggingface/transformers
- **File:** `utils/tests_fetcher.py`
- **Semantic score:** 0.61
- **Fusion risk score:** 100 / CRITICAL
- **Behavioral tags A:** DELETE_OPERATION
- **Behavioral tags B:** FILE_READ, FILE_WRITE, STATE_MUTATION
- **Classification:** ☑ GENUINE
- **Reason:** Same file as pair 12, same `get_all_tests` function paired
  with a different partner. `filter_tests` reads test dependency data,
  writes filtered output, and mutates state — again a full READ+WRITE+MUTATE
  profile against `get_all_tests`'s DELETE profile. Semantic score 0.61
  reflects name similarity in the test-management domain. The opposing
  detection fires correctly: a function that collects all tests and a
  function that filters them down have genuinely different behavioral
  purposes. Merging or confusing them in an automated refactoring operation
  would break the test selection pipeline.
- **Verification:** AI-assisted code read on GitHub upstream. Pipeline
  behavioral tags corroborate the classification.

#### 14. transformers :: `check_dependencies_and_create_import_node ↔ create_modules`

- **Repository:** huggingface/transformers
- **File:** `utils/modular_model_converter.py`
- **Semantic score:** 0.36
- **Fusion risk score:** 90 / CRITICAL
- **Behavioral tags A:** DELETE_OPERATION, FILE_WRITE, STATE_MUTATION
- **Behavioral tags B:** FILE_WRITE, STATE_MUTATION
- **Classification:** ☑ GENUINE
- **Reason:** Both functions operate in the modular model converter — a
  utility that assembles model source files from modular components.
  `check_dependencies_and_create_import_node` carries DELETE_OPERATION
  alongside FILE_WRITE and STATE_MUTATION: it performs dependency checks
  and may remove or replace import nodes as it builds the AST node.
  `create_modules` performs FILE_WRITE and STATE_MUTATION only — it
  creates module files without deletion. The DELETE asymmetry is the
  opposing signal: one function can destroy while building; the other
  only creates. Confusing them in a code-generation context would either
  introduce unintended deletions or suppress necessary cleanup steps.
- **Verification:** AI-assisted code read on GitHub upstream. Pipeline
  behavioral tags corroborate the classification.

---

## Results

### Tally

| Classification | Group A (n=5) | Group B (n=5) | Group C (n=4) | Total (n=14) |
|---|---|---|---|---|
| GENUINE | 3 | 3 | 4 | 10 / 14 = 71% |
| NOISE_FAMILY | 2 | 1 | 0 | 3 / 14 = 21% |
| NOISE_EMBEDDING | 0 | 1 | 0 | 1 / 14 = 7% |
| UNCERTAIN | 0 | 0 | 0 | 0 / 14 = 0% |

### Groups A+B only (original 10-pair baseline)

| Classification | Count | Proportion |
|---|---|---|
| GENUINE | 6 | 60% |
| NOISE_FAMILY | 3 | 30% |
| NOISE_EMBEDDING | 1 | 10% |

Group C is reported separately because it is exhaustive (all opposing
detections), not sampled. Including it in the main proportion would inflate
the GENUINE rate in a way that is not representative of the general BLOCK
population.

### Honest interpretation

Of 10 sampled V2 BLOCK decisions (Groups A+B), **60% were classified as
governance-significant semantic / behavioral distinctions worth surfacing
for human review.** The remaining 40% are not "false positives" in a
traditional sense — they are technically-correct BLOCK decisions on function
pairs that simply have no merge intent.

- **30% (3 of 10) NOISE_FAMILY** — Members of intentionally-distinct
  decorator and factory function families (e.g., click's `*_option`
  decorators, transformers' weight-initialization helpers, DRF's
  `_get_*_details` exception helpers). Sharing a naming token is by design;
  merging is not on the table.

- **10% (1 of 10) NOISE_EMBEDDING** — Embedding model under-scores
  similarity for cases like trivial-helper-vs-complex-scheduler where
  bodies differ greatly but the broader family is the same.

All 4 opposing-behavior detections (Group C) were classified GENUINE. These
represent the fusion engine's strongest signal: high-risk behavioral
asymmetry that neither the semantic engine nor the governance layer alone
would have surfaced at CRITICAL level. The `update_version_in_file ↔
update_version_in_examples` pair (semantic score 0.70, FREEZE_PATCH) is the
clearest illustration: name-similarity alone would not block it; behavioral
opposition detection does.

### Future calibration direction

Future calibration work (V2.3) may improve the governance-significant
proportion by reducing family-pattern over-flagging at the candidate
selection stage. The V2.2 test-pair filter already eliminates a significant
noise category; a family-name filter at the token-overlap stage is the
natural next step. V1-driven candidate extraction — when V1 detects actual
duplicates — provides a higher-quality candidate set by design; the 25-file
sampling cap limits its activation on large repositories in this evaluation.

### Confidence and caveats

- Sample size 10 (Groups A+B). The 60% point estimate has a wide confidence
  interval due to the small sample size. This is acknowledged as a
  small-sample audit, not a definitive precision figure.
- Single-reviewer audit. Inter-rater agreement not measured.
- The repositories audited skew toward framework / library code with
  decorator families. Application code may show different distributions.
- Group A is reviewer-selected for diversity; Group B is randomly sampled;
  Group C is exhaustive for the opposing-detection category.
- Source-code reading methodology: AI-assisted (reading upstream open-source
  repositories on GitHub). Author independently verified 3 of 10
  original classifications by opening local repository files. All 3
  verifications matched the AI-assisted classifications (3/3 confirmed).

### Independently verified classifications

The following 3 classifications were independently verified by the author
against local repository source code, confirming the AI-assisted reads:

| Pair | Classification | Verified |
|---|---|---|
| Django `commit ↔ savepoint_commit` | GENUINE | ✅ |
| transformers `xavier_normal_ ↔ trunc_normal_` | NOISE_FAMILY | ✅ |
| transformers `_get_constant_lambda ↔ get_cosine_with_min_lr_schedule_with_warmup` | NOISE_EMBEDDING | ✅ |

3 of 10 spot-checks confirmed. Remaining 7 classifications (Groups A+B)
rely on AI-assisted code reading only. Group C classifications rely on
AI-assisted reading plus pipeline behavioral tag evidence.

---

## Reproducibility

To reproduce the random sample selection (Group B):

```python
import json
import random

# Load transformers evaluation report
with open('tests/output/v2/v2_1_repo_evaluation/transformers_report.json') as f:
    data = json.load(f)

# Filter to BLOCK decisions only
blocks = [r for r in data['decision_pipeline_results']
          if r['fusion_decision'] == 'BLOCK']

# Random sample with the audit seed
random.seed(20260603)
random_sample_10 = random.sample(blocks, 10)

# First 5 of these are Group B (used in the 10-sample audit)
group_b = random_sample_10[:5]
```

To reproduce Group C (all opposing detections):

```python
# All pairs where opposing behavior was detected
group_c = [r for r in data['decision_pipeline_results']
           if r['fusion_opposing_detected']]
# Returns exactly 4 pairs from utils/release.py and utils/tests_fetcher.py
# and utils/modular_model_converter.py
```

The Group A picks were reviewer-selected and are listed by name above.

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

## Document History

- **June 2026** — Initial 10-pair audit completed (Groups A+B), AI-assisted
  methodology, author verification on 3 classifications.
- **June 2026 (V2 final refresh)** — V2.1 and V2.2 internal development labels
  consolidated into V2 for publication. Group C added: 4 exhaustive
  opposing-behavior detections from transformers evaluation. Sample expanded
  from 10 to 14. Tally and results section updated. Reproducibility section
  extended. V2.2 wiring changes (V1-driven candidate extraction, cross-file
  support, test filter, backup file skip) reflected throughout.