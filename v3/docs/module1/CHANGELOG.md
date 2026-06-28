# Changelog — CodeTruth Agent V3

All notable changes documented here.
Format: [version] — date — description

---

## [v3.0.0-module1-complete] — 2026-06-25

> **Validation scope:** 32 targeted repositories (extension layer).
> Overall Module 1 core validation: 69 repositories.
> The 32 cover specialised engineering domains not in the 69-repo corpus.

### Added — Module 1 Extension Layer

- `domain_signatures.py` — 16 engineering domain signatures
  covering aerospace, energy, mining, space, automotive,
  cybersecurity, bioinformatics, quantum, SDR, embedded,
  geology, chemical, geophysics, nuclear engineering
- `language_registry_expansion.py` — 218 unique file extensions
  across 25 domain blocks
- `repository_identity.py` — validate_framework() added to prevent
  false-positive framework detection (fluids/Astropy gap fixed)
- `boundary_detector.py` — ERP module markers added (__manifest__.py,
  __openerp__.py); scan depth increased to 5
- `domain_weights.py` — Domain hierarchy + generic subsumption
- `final_enterprise_report.py` — Enterprise report with conflict
  detection and hypothesis generation
- `executive_report_builder.py` — Executive summary format
- `domain_knowledge_discovery.py` — Document pointer discovery
- `assumption_discovery.py` — Hidden assumption detection
- `constraint_discovery.py` — Business/technical constraint discovery
- `decision_discovery.py` — Design decision discovery
- `knowledge_loss_detector.py` — SPOF + undocumented logic detection
- `evidence_traceability.py` — Document → code pointer traceability
- `repository_risk_discovery.py` — Critical component identification
- `enhanced_report_builder.py` — Unified enhanced report builder
- `gate_validator.py` — V3-003 governance gate
- `signal_analyzer.py` — Package/import/content signal analysis
- `architecture_detector.py` — Architecture pattern recognition
- `boundary_detector.py` — Repository boundary detection
- `classification_reason.py` — Classification evidence + reason

### Added — Test Suite

- 32 test scripts (TC_M1_001 through TC_M1_032)
- All scripts follow TC_M1_001 v2.0 format
- Evidence saved as MD + JSON per test
- All 32 tests PASS, 0 crashes

### Fixed

- OI-001: Assumption count too high — per-file cap added
- OI-002: Constraint count too high — per-file cap added
- OI-003: Risk score miscalibration on small repos — secondary calibration
- OI-004: Framework detection gap on rclpy — robotics signals added
- OI-005: Test script format inconsistency — all rebuilt to v2.0
- OI-006: Application type naming — APPLICATION_TYPE_NORMALISE added
- OI-007: FAILED cognition state — GateValidator now returns BLOCKED
- OI-008: fluids framework false positive — validate_framework() added
- OI-009: Monorepo detection misses ERP — __manifest__.py added

### Architecture

- framework_signatures.py — FROZEN (core, never modified)
- domain_signatures.py — LIVING (add new domains here)
- language_registry_expansion.py — LIVING (add new extensions here)

---

## [v3.0.0-module2-complete] — 2026-06-25

### Published

- 8 graph types: function, class, module, import, dependency, call,
  package, component
- 76/76 repos validated, 0 crashes
- 54,435 files processed
- 1,521,476 baseline resolved calls
- Deep Resolution pipeline: 7 proven resolvers
  - builtin_type: 286,477 resolutions
  - constructor:   54,194 resolutions
  - factory:          558 resolutions
  - property:       3,175 resolutions
  - inheritance:   23,209 resolutions
  - annotation:    27,183 resolutions (new — DR Resolver #7)
  - reflection:         0 (correct — documented known limit)
- Total additional resolutions: 394,796 (+25.9%)
- Language adapters: Python, Oracle SQL, C#, Go,
  Java, JavaScript/TypeScript, C/C++
- D-008 src-layout fix: 6 repos corrected
- DOI: 10.5281/zenodo.20706591

## [v3.0.0-module2] — 2026-06-23

### Published (initial)

- 6 structural graphs: function, class, module, import, dependency, call
- 69/69 repos validated, 0 crashes
- 1,005,321 resolved calls (2.5x over baseline)
- Deep Resolution extension: 6 resolvers + cause classifier
- Language adapters: Python, Java, JavaScript/TypeScript, C/C++
- DOI: 10.5281/zenodo.20706591

---

## [v3.0.0-module1] — 2026-06-22

### Published

- Repository Cognition Engine
- Framework Detection
- Domain Classification
- 69/69 repos validated, 0 crashes
- DOI: 10.5281/zenodo.20669542

---

*CodeTruth Agent V3 — github.com/Zeeshan78699/CodeTruthAgent*
