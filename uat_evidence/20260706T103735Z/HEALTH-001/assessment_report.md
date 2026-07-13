# CodeTruth Engineering Assessment Report

**Repository:** `C:\repos\v3\django`  
**Generated:** 2026-07-06T10:48:09.178145+00:00  
**Pipeline:** Module 1 (cognition + gate) -> Module 2 (structure) -> Module 3 (reasoning)

---

## 1. Executive Summary

- **Repository type:** WEB_APPLICATION (python)
- **Overall health:** SOUND
- **Risk level:** LOW
- **Governance gate:** APPROVED

**Why this rating (explicit metrics):**

| Metric | Value |
|---|---|
| call graph edges total | 67289 |
| reasoning edges added | 2198 |
| attribute calls resolved | 1935 |
| attribute call baseline | 66252 |
| attr resolution coverage pct | 2.9 |
| unresolved calls | 104871 |
| guesses | 0 |
| fixable inrepo miss | 128 |
| uncategorized declines | 0 |

**Health = analysis integrity, not resolution coverage.** CodeTruth's guarantee is *no fabrications; every decline categorized* - not *resolves all dynamic calls*. A dynamic framework with low coverage but 0 guesses is SOUND (the analysis is trustworthy); it is not penalized for the code being dynamic.

Rating rule: SOUND if `guesses == 0` AND `uncategorized_declines == 0` (here: 0 guesses, 0 uncategorized). Otherwise UNVERIFIED. Risk LOW unless notable fixable gaps (128 in-repo inheritance misses).

*Informational:* attribute-call resolution coverage 1935/66252 = 2.9% (low is EXPECTED for dynamic frameworks; not a health signal - most unresolved calls are dynamic dispatch, correctly declined).

**Executive recommendation:** Analysis is trustworthy (0 fabrications, all declines categorized). The verified call graph is safe to use for change-impact checks. Unresolved calls are dynamic/external and correctly flagged, not guessed - treat them as known-unknowns when refactoring those paths.

---

## 2. Repository Overview (Module 1)

- **Application type:** WEB_APPLICATION
- **Framework:** Django
- **Architecture:** MVC
- **Governance status:** APPROVED
- **Cognition confidence:** 1.0

*Source: Module 1 (Repository Cognition). Detected from code, not assumed.*

---

## 3. Structural Analysis (Module 2)

- **Language:** python
- **Files scanned:** 2920
- **Functions:** 32331
- **Classes:** 11007
- **Call-graph edges (M2):** 65091
- **Unresolved attribute-calls:** 104871 (handed to Module 3 for reasoning)

*Source: Module 2 (Structural Analysis). Deterministic AST parse + call graph.*

---

## 4. Architecture Analysis (Module 1 + Module 2)

- **Detected architecture pattern:** MVC (Module 1)
- **Coupling (structural):** 67289 call-graph edges across 32331 functions (avg fan-out 2.08)

**Candidate architecture concerns:**
- **No architecture policy provided.** CodeTruth reports structural dependency and coupling *facts* only. To assess **violations**, supply a layering policy (e.g. "presentation must not import data-layer"). Without a declared policy, no dependency is labeled a violation (Truth Boundary: we do not guess intended architecture).

*Source: Module 1 (pattern) + Module 2 (coupling facts). Violation assessment is policy-dependent.*

---

## 5. Engineering Findings (Module 3)

**Verified findings (resolved with certainty):**
- Attribute-calls resolved: 1849
- Net new edges merged into call graph: 2198
- Resolutions computed (may coincide with existing M2 edges): inherited 1095, super() 1274
- Total call-graph edges after reasoning: 67289

**Engineering issues / declines (categorized):**
- Inferred (bounded): 0
- Ambiguous: 86
- Uncertain: 0
- Unresolvable: 0

**Unknown (Truth Boundary):**
- Guesses made: **0**
- Numeric confidence scores: 0 (categorical labels only)

*Source: Module 3 (Deterministic Reasoning).*

---

## 6. Impact Analysis (Module 3)

- No target specified. Run with `--impact <qualified.function.name>` to compute change impact (who-calls, transitive affected set, call chains) for a specific method before modifying it.

*Source: Module 3 reasoning queries (who-calls / impact-of over the verified call graph).*

---

## 7. Engineering Gaps (Module 2 + Module 3)

- **Unresolved calls:** 104871 attribute-calls whose receiver type is not statically determinable
- **Inheritance limitations:** super() declines broken down as:
    - external base (correct, Truth Boundary): 188
    - in-repo miss (fixable): 128
    - no bases / non-class context: 155
    - cyclic (declined by guard): 164
- **Ambiguous receivers:** 86

*Source: Module 2 (unresolved sites) + Module 3 (categorized declines). Every gap has a documented reason; none is silently dropped.*

---

## 8. Recommendations

**HIGH priority:**
- None.

**MEDIUM priority:**
- 128 in-repo inheritance resolutions are incomplete; qualified-name resolution would recover these.  
  *(linked finding: Module 3 super_decline_inrepo_miss)*

**LOW priority:**
- 104871 calls remain unresolved (dynamic/external receivers); expected for dynamic code, flagged not guessed.  
  *(linked finding: Module 2 unresolved_calls)*

*Every recommendation is linked to a verified finding above.*

---

## 9. Confidence & Truth Boundary

- **Verified facts:** 1849 resolved calls, 67289 call-graph edges
- **Unknowns (explicitly flagged):** 104871 unresolved calls, each with a documented reason
- **Declined analyses:** categorized in section 7 (not silently dropped)
- **Guesses made: 0**

> **No unsupported conclusions generated.** Every finding in this report is either directly computed from module output or explicitly marked as a derived metric or policy-dependent assessment. Where the analysis cannot resolve a fact, it is reported as unknown rather than guessed.

---

## 10. Evidence & Traceability

| Finding | Source | Evidence | Status |
|---|---|---|---|
| Repository type = WEB_APPLICATION | Module 1 | cognition scan | verified |
| 65091 edges (M2) -> 67289 (after M3) | Module 2 + 3 | AST + reasoning | verified |
| 2198 reasoning edges added | Module 3 | C3 MRO + super() resolution | verified (in index) |
| 0 guesses | Module 3 | Truth Boundary | verified |

*Every major finding links back to the module and evidence that produced it.*

---

## 11. Module Contributions

- **Module 1 (Repository Cognition):** identified as WEB_APPLICATION / Django / MVC; governance gate APPROVED.
- **Module 2 (Structural Graph):** 2920 files, 32331 functions, 11007 classes, 65091 call-graph edges, 104871 unresolved sites.
- **Module 3 (Deterministic Reasoning):** +2198 verified reasoning edges, declines categorized, 0 guesses.

*This shows how the final conclusions were reached — each module's contribution to the assessment.*
