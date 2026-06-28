# CodeTruth Agent V3 — Module 1 Extension Layer
## Full Documentation

**Version:** v3.0.0-module1-complete
**Date:** 2026-06-25
**Status:** FROZEN ✅
**DOI:** 10.5281/zenodo.20669542

---

## Objective

> *Before any automated software analysis or modification begins,
> the repository must first be understood.*

Module 1 Extension Layer adds domain-specific intelligence on top of the
frozen Module 1 Core engine. It resolves generic classifications into precise
engineering domain types, expands file extension recognition to 218 entries,
and provides a full governance gate for AI agent decisions.

---

## What the Extension Layer Adds

```
Module 1 Core (frozen):
  framework_signatures.py    ← never modified
  cognition_engine.py        ← never modified

Module 1 Extension Layer (living):
  domain_signatures.py       ← 16 engineering domains
  language_registry_expansion.py ← 218 file extensions
  + 13 extension modules
```

---


## Module 1 Core vs Extension Layer — Side by Side

This section clarifies exactly what existed before the extension layer
and what was added.

### Before Extension Layer (Module 1 Core Only)

```
What the core engine returned:
  application_type : DATA_ENGINEERING
  primary_framework: None
  confidence_score : 0.7
  domain_enhanced  : not available
  gate_decision    : not available
  validate_fw      : not available
  file_extensions  : 18 known
  engineering_domains : 0 specific domains
```

**Real example — lasio repository:**
```
Core output:
  application_type : DATA_ENGINEERING   ← generic
  primary_framework: None
  confidence_score : 0.7
```

**Real example — welleng repository:**
```
Core output:
  application_type : GRAPH_ANALYTICS    ← wrong domain family
  primary_framework: None
```

**Real example — fluids repository:**
```
Core output:
  primary_framework: Astropy            ← FALSE POSITIVE
  (Astropy was in the code but not a dependency)
```

**Real example — pyreservoir repository:**
```
Core output:
  application_type : MONOREPO           ← generic
  ERP structure    : not detected
```

---

### After Extension Layer (Module 1 Complete)

```
What the enhanced engine returns:
  application_type         : WELL_LOGGING
  primary_framework        : lasio
  confidence_score         : 1.0
  domain_enhanced          : WELL_LOGGING
  gate_decision            : APPROVED
  validate_framework()     : active — prevents false positives
  file_extensions known    : 218
  engineering_domains      : 16 specific domains
  assumptions_found        : 169
  constraints_found        : 104
  risk_score               : 7/10
  architecture_pattern     : LIBRARY
```

**Same example — lasio repository after extension:**
```
Enhanced output:
  application_type : WELL_LOGGING       ← precise domain
  primary_framework: lasio              ← correct framework
  confidence_score : 1.0               ← HIGH
  gate_decision    : APPROVED
```

**Same example — welleng repository after extension:**
```
Enhanced output:
  application_type : DRILLING_SYSTEM    ← correct domain
  primary_framework: welleng
  gate_decision    : APPROVED
```

**Same example — fluids repository after extension:**
```
Enhanced output:
  primary_framework: fluids             ← CORRECT (Astropy removed)
  validate_framework() caught Astropy false positive
  gate_decision    : APPROVED
```

**Same example — pyreservoir after extension:**
```
Enhanced output:
  application_type : RESERVOIR_ENGINEERING ← precise
  gate_decision    : APPROVED
```

---

### Feature Comparison Table

| Feature | Core Only | With Extension |
|---|---|---|
| Application type | Generic (DATA_ENGINEERING) | Precise (WELL_LOGGING) |
| Engineering domains | 0 specific | 16 specific |
| File extensions | 18 | 218 |
| Framework validation | None | validate_framework() ✅ |
| Governance gate | None | APPROVED / REVIEW / BLOCKED |
| False positive prevention | None | Active ✅ |
| ERP/Monorepo detection | Basic | __manifest__.py support ✅ |
| Risk score | None | 0-10 scale |
| Assumptions detected | None | Active ✅ |
| Constraints detected | None | Active ✅ |
| Architecture pattern | None | LIBRARY / MONOLITH / etc. |
| Evidence traceability | None | Document → code pointers |
| Scale tested | 69 repos (core validation) | 32 repos (targeted extension validation) |

---

### What NEVER Changed (Frozen Core)

```
framework_signatures.py   ← 200+ framework patterns — FROZEN
cognition_engine.py       ← core analysis engine — FROZEN

These two files were never modified.
All new capability lives in module1_extensions/
```

---

## 1. Domain Signatures — 16 Engineering Domains

Resolves generic implementation patterns into precise engineering domains.

### Before vs After

| Repository | Core Classification | Domain Enhancement |
|---|---|---|
| pyNastran | SIMULATION_TOOL | AEROSPACE_STRUCTURAL_SIMULATION |
| lasio | DATA_ENGINEERING | WELL_LOGGING |
| welleng | GRAPH_ANALYTICS | DRILLING_SYSTEM |
| pyreservoir | MONOREPO | RESERVOIR_ENGINEERING |
| fluids | DATA_ENGINEERING | FLUIDS_ENGINEERING |
| striplog | UNKNOWN | WELL_LOGGING |

### Domain Signature Table

| Domain | Key Packages | Key Signals |
|---|---|---|
| AEROSPACE_STRUCTURAL_SIMULATION | pynastran, nastran | *.bdf, *.fem, *.op4 |
| WELL_LOGGING | lasio, welly, striplog | *.las, wireline, gamma_ray |
| DRILLING_SYSTEM | welleng, wellpathpy | wellbore, trajectory, dogleg |
| RESERVOIR_ENGINEERING | pyreservoir, ecl2df | reservoir, pvt, porosity |
| FLUIDS_ENGINEERING | fluids, thermo | reynolds_number, pipe_flow |
| MINING_GEOLOGY | striplog, gempy | stratigraphy, lithology, mineral |
| AUTOMOTIVE_SYSTEM | cantools, python-can | *.arxml, *.dbc, can_bus |
| CYBERSECURITY_SYSTEM | scapy, pwntools | *.pcap, exploit, payload |
| BIOINFORMATICS_SYSTEM | biopython, pysam | *.fasta, *.vcf, genome |
| QUANTUM_COMPUTING | qiskit, cirq | *.qasm, qubit, quantum_circuit |
| SDR_RADIO_SYSTEM | gnuradio, pyrtlsdr | *.grc, sdr, modulation |
| EMBEDDED_RTOS | zephyr, micropython | *.dts, rtos, bootloader |
| GEOLOGY_STRATIGRAPHY | striplog, welly | *.las, stratigraphy, horizon |
| CHEMICAL_ENGINEERING | thermo, chemicals | thermodynamics, distillation |
| GEOPHYSICS_SEISMIC | obspy, segyio | *.segy, seismic, waveform |
| NUCLEAR_ENGINEERING | openmc, pyne | reactor, neutron, fission |

### How it Works

```python
# Only overrides generic types — specific types preserved
GENERIC_TYPES = {
    "DATA_ENGINEERING", "GRAPH_ANALYTICS", "SIMULATION_TOOL",
    "MONOREPO", "UNKNOWN", "SCIENTIFIC_SYSTEM", "LIBRARY",
}

# FINANCE_SYSTEM, ENERGY_SYSTEM, DRONE_UAV etc. → never overridden
# DATA_ENGINEERING → scanned → WELL_LOGGING if lasio detected
```

---

## 2. Language Registry — 218 File Extensions / 25 Domain Blocks

### Growth During Validation

| After repo | Extensions | New block |
|---|---|---|
| ccxt | 18 | C#/.NET, Go, TypeScript, WebAssembly |
| pyNastran | 69 | Aerospace/FEM (51 entries) |
| dronekit | 73 | Drone/UAV/Aviation |
| pandapower | 89 | Energy/Power Grid |
| PyPSA | 91 | Citation/Config |
| astropy | 114 | Astronomy/Planetary |
| odoo | 146 | ERP/Enterprise |
| MetPy | 162 | Climate/Meteorology |
| cocotb | 184 | FPGA/EDA |
| transformers | 187 | ML/AI |
| (new domains) | 218 | Automotive, Bioinformatics, Seismic, Chemical |

### Domain Blocks (25)

```
C#/.NET            Go              TypeScript
WebAssembly        Native Libraries Source Maps
Grammar            Metadata        Templates
Medical Imaging    HL7/FHIR        Aerospace/FEM
Drone/UAV          Energy/Power    Citation/Config
Astronomy          ERP/Enterprise  Automotive/CAN
Cybersecurity      Bioinformatics  Quantum Computing
SDR/Radio          Embedded/RTOS   Geophysics/Seismic
Chemical/Molecular
```

---

## 3. Extension Modules (13)

| Module | Purpose |
|---|---|
| repository_identity.py | Identity + validate_framework() |
| architecture_detector.py | Architecture pattern recognition |
| boundary_detector.py | Repository boundary + monorepo detection |
| signal_analyzer.py | Package/import/content signals |
| classification_reason.py | Evidence + reason builder |
| gate_validator.py | V3-003 Governance gate |
| domain_knowledge_discovery.py | Document pointer discovery |
| assumption_discovery.py | Hidden assumption detection |
| constraint_discovery.py | Business/technical constraints |
| decision_discovery.py | Design decision discovery |
| knowledge_loss_detector.py | SPOF + undocumented logic |
| evidence_traceability.py | Document → code pointers |
| repository_risk_discovery.py | Critical component identification |

---

## 4. validate_framework() — False Positive Prevention

```python
# Prevents fluids repo detecting "Astropy" as framework
# Checks if detected framework is actually in dependencies

def validate_framework(detected_framework: str, repo_path: str) -> str | None:
    # Searches requirements.txt, pyproject.toml, setup.py, setup.cfg
    # Returns None if framework not found in dependencies
```

---

## 5. Monorepo Detection Improvements

```python
# ERP/Odoo module structure now detected:
SUBPROJECT_MARKERS = {
    "setup.py", "pyproject.toml", "package.json",
    "__manifest__.py",   ← Odoo module marker (added)
    "__openerp__.py",    ← Odoo legacy marker (added)
    "plugin.json",
}
MAX_DEPTH = 5            # increased from 4
MONOREPO_THRESHOLD = 3   # minimum sub-projects
```

---

## 6. Validation Suite — 32 Tests

### Group A — Core Domain (10 tests)

| Test | Repository | Domain | Gate |
|---|---|---|---|
| TC_M1_001 | ccxt | FINANCE_SYSTEM | APPROVED |
| TC_M1_002 | pydicom | MEDICAL_SYSTEM | APPROVED |
| TC_M1_003 | rclpy | ROBOTICS_SYSTEM | APPROVED |
| TC_M1_004 | MetPy | CLIMATE_SCIENCE | APPROVED |
| TC_M1_005 | cocotb | FPGA_HARDWARE | APPROVED |
| TC_M1_006 | fastapi | API_SERVICE | APPROVED |
| TC_M1_007 | flask | WEB_APPLICATION | APPROVED |
| TC_M1_008 | transformers | ML_PIPELINE | APPROVED |
| TC_M1_009 | click | CLI_TOOL | MAINTAINED |
| TC_M1_010 | home-assistant | MULTI_DOMAIN | DEFERRED |

### Group B — Strategic Industry (5 tests)

| Test | Repository | Domain | Gate |
|---|---|---|---|
| TC_M1_011 | pyNastran | AEROSPACE_STRUCTURAL_SIMULATION | APPROVED |
| TC_M1_012 | dronekit-python | DRONE_UAV | APPROVED |
| TC_M1_013 | zipline | FINANCE_SYSTEM | APPROVED |
| TC_M1_014 | lasio | WELL_LOGGING | APPROVED |
| TC_M1_015 | pymodbus | EMBEDDED_SYSTEM | APPROVED |

### Group C — Energy Engineering (5 tests)

| Test | Repository | Domain | Gate |
|---|---|---|---|
| TC_M1_016 | welleng | DRILLING_SYSTEM | APPROVED |
| TC_M1_017 | pandapower | ENERGY_SYSTEM | APPROVED |
| TC_M1_018 | pyreservoir | RESERVOIR_ENGINEERING | APPROVED |
| TC_M1_019 | PyPSA | ENERGY_SYSTEM | APPROVED |
| TC_M1_020 | fluids | FLUIDS_ENGINEERING | APPROVED |

### Group D — Mining and Space (3 tests)

| Test | Repository | Domain | Gate |
|---|---|---|---|
| TC_M1_021 | striplog | WELL_LOGGING | REVIEW_REQUIRED |
| TC_M1_022 | poliastro | SPACE_SYSTEM | APPROVED |
| TC_M1_023 | astropy | SPACE_SYSTEM | APPROVED |

### Group E — Edge Cases and Scale (9 tests)

| Test | Scenario | Result |
|---|---|---|
| TC_M1_024 | Monorepo (odoo/ERP) | APPROVED |
| TC_M1_025 | Broken repository | NO CRASH |
| TC_M1_026 | Incomplete repository | NO CRASH |
| TC_M1_027 | Custom framework (kivy) | APPROVED |
| TC_M1_028 | No dependencies | NO CRASH |
| TC_M1_029 | Mixed stack (FreeCAD) | APPROVED |
| TC_M1_030 | Large 10K+ (django) | APPROVED |
| TC_M1_031 | Very large 50K+ (pytorch) | APPROVED |
| TC_M1_032 | Extreme 100K+ (CPython) | APPROVED |

**Result: 32/32 PASS — 0 crashes**

---

## 7. Open Items Resolved (9)

| ID | Issue | Fix |
|---|---|---|
| OI-001 | Assumption count too high | Per-file cap in assumption_discovery.py |
| OI-002 | Constraint count too high | Per-file cap in constraint_discovery.py |
| OI-003 | Risk 10/10 on small repos | Secondary calibration added |
| OI-004 | Framework: None on rclpy | Robotics signals added |
| OI-005 | Test script format inconsistency | All rebuilt to v2.0 format |
| OI-006 | Application type naming | APPLICATION_TYPE_NORMALISE map added |
| OI-007 | FAILED state no gate detail | GateValidator returns BLOCKED |
| OI-008 | fluids → Astropy false positive | validate_framework() added |
| OI-009 | Monorepo misses ERP structures | __manifest__.py added |

---

## 8. Validated Capabilities

| Capability | Validation Evidence |
|---|---|
| Repository Cognition | 32/32 PASS across 21 engineering disciplines |
| Framework Detection | Validated on 69 repos — false positive OI-008 fixed |
| Application Type | 32 domain-specific classifications confirmed |
| Architecture Detection | LIBRARY / MONOLITH / MICROSERVICE / MONOREPO detected |
| Governance | APPROVED / REVIEW_REQUIRED / BLOCKED across all 32 repos |
| Scale Validation | Validated at 10K+ / 50K+ / 100K+ files with 0 crashes |
| Edge Cases | Broken / Incomplete / No-deps / Custom FW — all NO CRASH |
| Domain Coverage | 16 specific + generic fallback — 1 REVIEW_REQUIRED (correct) |

> Note: These are evidence-based capability statements derived from the
> validation suite, not self-assessed scores.

---

## 9. Adding New Domains

```python
# domain_signatures.py — add to DOMAIN_SIGNATURES list:
{
    "name":         "YOUR_DOMAIN",
    "packages":     ["package1", "package2"],
    "file_patterns":["*.ext1", "*.ext2"],
    "keywords":     ["keyword1", "keyword2"],
    "min_score":    2,
}

# language_registry_expansion.py — add extensions:
".ext1": "Description of file type",
```

---

## Module 1 Extension — Status

```
domain_signatures.py           LIVING — 16 domains, add new here
language_registry_expansion.py LIVING — 218 extensions, add new here
framework_signatures.py        FROZEN — core, never modify
cognition_engine.py            FROZEN — core, never modify

Module 1 Extension Layer       FROZEN ✅
Module 1 Architecture          FROZEN ✅
```

---

*CodeTruth Agent V3 — AI imagines. CodeTruth checks. Nature tests. Humans decide.*
