# CodeTruth Agent V3 — Module 1
## Components and Capabilities

Module 1 provides deterministic repository understanding through the
following capabilities:

```
1. Repository Scanning
   - Scans repositories of any size and structure.
   - Validated from 35 files (python-sgp4) to 61,850 files (Zephyr RTOS).

2. Language Detection
   - Identifies programming, scripting, markup, and configuration languages
     (Python, C, C++, Rust, Go, JavaScript, TypeScript, Cython, Verilog,
     VHDL, Lua, Shell, and others).

3. Framework Detection
   - Detects frameworks, libraries, and technology ecosystems via package,
     import, and content-pattern signals.
   - Reports "No Framework Detected" honestly when none exists (correct
     for C/C++ system software such as Redis, Nginx, U-Boot).

4. Dependency Discovery
   - Discovers dependencies from manifests (requirements.txt,
     pyproject.toml, setup.py, package.json, Cargo.toml, etc.) and from
     source code import statements via AST parsing.

5. Technology Stack Detection
   - Identifies databases, cloud platforms, containers, CI/CD tools, and
     infrastructure (Docker, Redis, AWS, GCP, Kubernetes, Jenkins,
     GitLab CI, Travis CI, Vagrant, Ansible, and others).

6. Configuration Discovery
   - Finds and inventories configuration and build files (pyproject.toml,
     setup.cfg, Makefile, CMakeLists.txt, Dockerfile, .env, and others).

7. Build System Detection
   - Detects Make, CMake, Setuptools, Python Build, Cargo, Go Modules,
     NPM, Yarn, Gradle, Composer, Conda, and others.

8. Documentation Discovery
   - Identifies documentation assets and project knowledge sources
     (README, CONTRIBUTING, CHANGELOG, AUTHORS, LICENSE, and docs
     directories).

9. Entry Point Discovery
   - Detects likely application and execution entry points (CLI scripts,
     __main__.py, app.py, examples, and similar).

10. Test Suite Discovery
    - Identifies test directories and test-related frameworks (Pytest,
      cocotb test cases, Jest/Cypress specs, and others).

11. Repository Scale Analysis
    - Measures total file counts, Python file counts, and test directory
      counts as part of the scale profile of a repository.

12. Polyglot Repository Discovery
    - Understands repositories containing multiple languages and
      ecosystems (e.g. CCXT: Python, JS, TypeScript, Go, Java, C#, PHP,
      Rust in one repository).

13. ERP Asset Discovery
    - Detects enterprise platforms; validated against Odoo
      (ERP_SYSTEM, 47,562 files, 100% discovery/classification).
      Signature structure supports extension to other ERP platforms
      (SAP, Oracle, Salesforce, Dynamics, NetSuite) via
      MODULE1_EXTENSION_GUIDE.md.

14. Domain Classification
    - Classifies repositories into one of 46 supported application types
      across engineering domains; 39 of these were exercised in the
      69-repository validation set.

15. Unknown Asset Detection
    - Tracks previously unseen file extensions per repository as
      warnings/diagnostics, rather than silently ignoring them, for
      future addition to the language registry.

16. Confidence Scoring
    - Produces two separate scores: a discovery score (file/asset
      inventory completeness) and a classification score (confidence in
      application type and framework determination).

17. Governance Readiness Validation
    - Issues a governance gate decision (V3-003: APPROVED / BLOCKED)
      that determines whether downstream modules may proceed.

18. Deterministic Processing
    - Rule-based, not model-based — produces identical results for
      identical repository contents on repeated runs. No network access,
      no modification of the scanned repository.

19. Immutable Cognition Contract
    - Generates a frozen RepositoryCognitionReport dataclass — a fixed,
      versioned contract consumed by downstream V3 modules — plus
      human-readable .txt and .md reports.

20. Universal Repository Cognition
    - Provides a unified understanding layer validated across web, ERP,
      ML, CAD, aerospace/space, medical, quantum computing, finance/
      blockchain, robotics, embedded systems/firmware, networking,
      energy, GIS, security, NLP, audio/video, mobile, cloud
      infrastructure, and other domains — 69 real repositories, 39
      application types exercised, 0 crashes.
```

---

## Source of Validation Data

All figures above are drawn from the 69-repository validation run
recorded in `MODULE1_CAPABILITY_PROOF.md` and `FULL_DOMAIN_SUMMARY.md`.
