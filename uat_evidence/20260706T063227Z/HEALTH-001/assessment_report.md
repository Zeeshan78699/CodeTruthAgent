# CodeTruth Engineering Assessment Report

**Repository:** `C:\repos\v3\flask`  
**Generated:** 2026-07-06T06:32:48.146216+00:00  
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
| call graph edges total | 697 |
| reasoning edges added | 11 |
| attribute calls resolved | 18 |
| attribute call baseline | 2506 |
| attr resolution coverage pct | 0.7 |
| unresolved calls | 2732 |
| guesses | 0 |
| fixable inrepo miss | 0 |
| uncategorized declines | 0 |

**Health = analysis integrity, not resolution coverage.** CodeTruth's guarantee is *no fabrications; every decline categorized* - not *resolves all dynamic calls*. A dynamic framework with low coverage but 0 guesses is SOUND (the analysis is trustworthy); it is not penalized for the code being dynamic.

Rating rule: SOUND if `guesses == 0` AND `uncategorized_declines == 0` (here: 0 guesses, 0 uncategorized). Otherwise UNVERIFIED. Risk LOW unless notable fixable gaps (0 in-repo inheritance misses).

*Informational:* attribute-call resolution coverage 18/2506 = 0.7% (low is EXPECTED for dynamic frameworks; not a health signal - most unresolved calls are dynamic dispatch, correctly declined).

**Executive recommendation:** Analysis is trustworthy (0 fabrications, all declines categorized). The verified call graph is safe to use for change-impact checks. Unresolved calls are dynamic/external and correctly flagged, not guessed - treat them as known-unknowns when refactoring those paths.

---

## 2. Repository Overview (Module 1)

- **Application type:** WEB_APPLICATION
- **Framework:** Flask
- **Architecture:** LIBRARY
- **Governance status:** APPROVED
- **Cognition confidence:** 1.0

*Source: Module 1 (Repository Cognition). Detected from code, not assumed.*

---

## 3. Structural Analysis (Module 2)

- **Language:** python
- **Files scanned:** 83
- **Functions:** 1460
- **Classes:** 160
- **Call-graph edges (M2):** 686
- **Unresolved attribute-calls:** 2732 (handed to Module 3 for reasoning)

*Source: Module 2 (Structural Analysis). Deterministic AST parse + call graph.*

---

## 4. Architecture Analysis (Module 1 + Module 2)

- **Detected architecture pattern:** LIBRARY (Module 1)
- **Coupling (structural):** 697 call-graph edges across 1460 functions (avg fan-out 0.48)

**Candidate architecture concerns:**
- **No architecture policy provided.** CodeTruth reports structural dependency and coupling *facts* only. To assess **violations**, supply a layering policy (e.g. "presentation must not import data-layer"). Without a declared policy, no dependency is labeled a violation (Truth Boundary: we do not guess intended architecture).

*Source: Module 1 (pattern) + Module 2 (coupling facts). Violation assessment is policy-dependent.*

---

## 5. Engineering Findings (Module 3)

**Verified findings (resolved with certainty):**
- Attribute-calls resolved: 18
- Net new edges merged into call graph: 11
- Resolutions computed (may coincide with existing M2 edges): inherited 17, super() 0
- Total call-graph edges after reasoning: 697

**Engineering issues / declines (categorized):**
- Inferred (bounded): 0
- Ambiguous: 0
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

- **Unresolved calls:** 2732 attribute-calls whose receiver type is not statically determinable
- **Inheritance limitations:** super() declines broken down as:
    - external base (correct, Truth Boundary): 0
    - in-repo miss (fixable): 0
    - no bases / non-class context: 4
    - cyclic (declined by guard): 0
- **Ambiguous receivers:** 0

*Source: Module 2 (unresolved sites) + Module 3 (categorized declines). Every gap has a documented reason; none is silently dropped.*

---

## 8. Recommendations

**HIGH priority:**
- None.

**MEDIUM priority:**
- None.

**LOW priority:**
- 2732 calls remain unresolved (dynamic/external receivers); expected for dynamic code, flagged not guessed.  
  *(linked finding: Module 2 unresolved_calls)*

*Every recommendation is linked to a verified finding above.*

---

## 9. Confidence & Truth Boundary

- **Verified facts:** 18 resolved calls, 697 call-graph edges
- **Unknowns (explicitly flagged):** 2732 unresolved calls, each with a documented reason
- **Declined analyses:** categorized in section 7 (not silently dropped)
- **Guesses made: 0**

> **No unsupported conclusions generated.** Every finding in this report is either directly computed from module output or explicitly marked as a derived metric or policy-dependent assessment. Where the analysis cannot resolve a fact, it is reported as unknown rather than guessed.

---

## 10. Evidence & Traceability

| Finding | Source | Evidence | Status |
|---|---|---|---|
| Repository type = WEB_APPLICATION | Module 1 | cognition scan | verified |
| 686 edges (M2) -> 697 (after M3) | Module 2 + 3 | AST + reasoning | verified |
| 11 reasoning edges added | Module 3 | C3 MRO + super() resolution | verified (in index) |
| 0 guesses | Module 3 | Truth Boundary | verified |

*Every major finding links back to the module and evidence that produced it.*

---

## 11. Module Contributions

- **Module 1 (Repository Cognition):** identified as WEB_APPLICATION / Flask / LIBRARY; governance gate APPROVED.
- **Module 2 (Structural Graph):** 83 files, 1460 functions, 160 classes, 686 call-graph edges, 2732 unresolved sites.
- **Module 3 (Deterministic Reasoning):** +11 verified reasoning edges, declines categorized, 0 guesses.

*This shows how the final conclusions were reached — each module's contribution to the assessment.*
