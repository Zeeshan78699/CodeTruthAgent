# Module 2 — Real-World Problems Addressed

**CodeTruth Agent V3 — Module 2 — Repository Graph Engine**

V3's overall problem statement targets 20 real-world software engineering
problems (see project-level documentation). Module 2 directly addresses one
of these, and provides the foundational data for several more.

---

## Directly Addressed

### #17 — Large Codebase Navigation Difficulty
**V3 Solution: Repository Graph**

Before Module 2, answering "what calls this function?" or "what does this
function depend on?" in a 500,000-function codebase (the scale of the
69-repo validation set) required manual grep/search with no guarantee of
completeness. Module 2's `call_graph` provides this as structured data:
1,005,321 verified call edges across 69 real repositories, with every
unresolved case explicitly logged rather than silently missing.

---

## Foundation Provided (not yet complete solutions)

These problems need an additional reasoning/analysis layer on top of
Module 2's graphs - that layer doesn't exist yet, but the data it would
consume does:

### #4 — Unknown Impact of Code Changes (Causal Impact Engine)
`call_graph` + `class_graph` (inheritance) together describe "if function X
changes, which functions call X (directly or via inheritance) and could be
affected." A future Causal Impact Engine would traverse this graph.

### #11 — Lack of Repository Understanding (Repository DNA)
Combined with Module 1's classification (languages, frameworks, domains),
Module 2's 6 graphs give a structural fingerprint of a repository - the
raw material for a "DNA" profile.

### #18 — Manual Impact Assessments (Automated Impact Analysis)
Same underlying data as #4 - the difference is presentation/automation
layer, not data availability.

### #19 — Late Discovery of Architectural Problems (Architecture Governance)
Gap 3's cycle detection (`cyclic_clusters`) is a first architectural signal
(circular module dependencies). A future Architecture Governance module
would extend this with layering rules, coupling metrics, etc.

---

## Honest Scope Statement

Module 2 does not perform impact analysis, risk scoring, or architectural
judgment itself - it produces the verified structural facts those future
modules would need. This mirrors Module 1's relationship to the same
problems: Module 1 says "what kind of repo is this," Module 2 says "how is
the code wired together," and both wait for a reasoning layer (Module 3+)
to act on that information.

---

*CodeTruth Agent V3 — Module 2 — Repository Graph Engine*
*github.com/Zeeshan78699/CodeTruthAgent*
