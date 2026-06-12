# CodeTruth Agent V3 — Module 1
## Questions & Answers: The Problem and How It's Resolved

---

**Q1: What problem does Module 1 solve?**

Before any tool can analyze, modify, or govern changes to a code
repository, it must first answer: *"What kind of repository is this?"*
Without that context, the same signal (e.g. a `torch` import) can mean
different things in different repositories — an ML pipeline, a
computer-vision tool, an audio tool, or a quantum-computing library.
Shallow heuristics (file-extension counts, single-keyword matching)
produce misclassifications that cascade into every later stage of
analysis.

---

**Q2: How does Module 1 determine what a repository "is"?**

It combines three signal sources:
- **Package/dependency signals** — from `requirements.txt`,
  `pyproject.toml`, `setup.py`, etc.
- **Import signals** — `import` statements parsed via Python's `ast`
  module from a sample of source files.
- **Content-pattern signals** — for repositories not distributed as
  Python packages (C/C++, firmware, hardware bindings), specific
  identifying files/paths are checked directly (weight 15 — strong
  enough to establish identity even with many competing signals).

A type hierarchy then resolves conflicts between competing signals.

---

**Q3: What if the same package appears in many unrelated repositories
(e.g. `torch`, `requests`, `click`)?**

Generic/ubiquitous utility packages (Click, Requests, Pytest, Redis,
RQ, Pydantic, etc.) are excluded from the **primary** framework
candidate pool entirely. They can appear as *secondary* frameworks but
never become "the framework" of a repository. This was specifically
fixed after it caused Rust → "Click" and VSCode → "Next.js" — both now
resolve correctly (Rust → No Framework Detected, VSCode → React).

---

**Q4: What happens with repositories that have no Python framework at
all (Redis, Nginx, Go, Rust, U-Boot)?**

Module 1 reports **"No Framework Detected"** — an honest, correct
result, not an error. The application type and discovery score remain
100% correct; only the framework field is empty. This applies to 12 of
the 69 validated repositories (Redis, Nginx, Go, Rust, FreeCAD,
LibreCAD, Shapely, rclpy, gst-python, u-boot, gnuradio,
CodeTruthAgent).

---

**Q5: How does Module 1 handle a package whose pip name differs from
its repository name (e.g. `solana-py` repo vs. `solana` package)?**

A self-name resolution pass strips common affixes (`_py`, `python_`,
`py_`) and matches the repository's directory name against candidate
package names before falling back to other resolution passes. This
correctly resolves `solana-py` → `Solana`, `cvxpy` → `CVXPY`,
`circuitpython` → `CircuitPython`, etc.

---

**Q6: What if two frameworks both map to the same application type
(e.g. `astropy` and `sgp4`, both Space-related)?**

A type-match pass prefers the candidate package whose own mapped
application type equals the repository's determined type. This
resolves `astropy` → `Astropy` (not `sgp4`) correctly.

---

**Q7: How is confidence communicated?**

Two separate scores:
- **Discovery score** — file/asset inventory completeness (100% across
  all 69 validated repositories).
- **Classification score** — confidence in type/framework:
  - 100% = type and framework both resolved
  - 75% = type correct, genuinely "No Framework Detected" (correct by
    design, not a partial failure)

---

**Q8: What does the output look like, and what do downstream modules
receive?**

A frozen `RepositoryCognitionReport` dataclass (immutable contract),
plus human-readable `.txt`/`.md` reports and a governance gate decision
(V3-003: APPROVED/BLOCKED). Module 1 performs no network access and
makes no modifications to the scanned repository.

---

**Q9: How was this validated?**

Against 69 real, cloned, open-source repositories spanning 39
application types, from 35 files (python-sgp4) to 61,850 files
(Zephyr RTOS), including non-Python repositories (Redis, Nginx, Go,
Rust, U-Boot, Zephyr).

```
69/69 = 100% discovery score
69/69 = correct application type
69/69 = correct primary framework (or correctly "No Framework Detected")
69/69 = governance gate APPROVED
 0/69 = crashes
57/69 = 100% classification score
12/69 = 75% classification score (all "No Framework Detected", correct)
35/35 = unit tests pass
441,660 total files scanned
```

---

**Q10: What's the scope — does Module 1 modify code or make
governance decisions about changes?**

No. Module 1 is a discovery/classification layer only — the first of
several modules in CodeTruth Agent V3. Module 2 (Repository Graph
Engine) builds on its output next.
