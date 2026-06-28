# CodeTruth Agent V3 — Module 1 Extension Layer

**Status:** FROZEN ✅
**Date:** 2026-06-25
**Architecture:** Core frozen — extension via subfolder only

---

## Design Principle

```
framework_signatures.py  — FROZEN forever
cognition_engine.py      — FROZEN forever

module1_extensions/      — LIVING
  Add new domains here
  Add new extensions here
  Never touch the core
```

---

## File Structure

```
v3/repository_cognition/module1_extensions/
├── __init__.py
├── repository_identity.py        — Identity + Domain Classification
│     └── validate_framework()   — Prevents false-positive framework detection
├── architecture_detector.py      — Architecture Pattern Recognition
├── boundary_detector.py          — Repository Boundary Detection
│     └── __manifest__.py        — ERP module marker added
│     └── MAX_DEPTH = 5          — Increased for large ERP structures
├── signal_analyzer.py            — Package / Import / Content Signals
├── classification_reason.py      — Classification Evidence + Reason
├── gate_validator.py             — V3-003 Governance Gate
├── domain_knowledge_discovery.py — Document POINTERS only (not extractor)
├── assumption_discovery.py       — Hidden Assumption Detection
├── constraint_discovery.py       — Constraint Discovery
├── decision_discovery.py         — Design Decision Discovery
├── knowledge_loss_detector.py    — SPOF + Undocumented Logic Detection
├── evidence_traceability.py      — Document → Code Pointers
├── repository_risk_discovery.py  — Critical Component Identification
├── enhanced_report_builder.py    — Unified Enhanced Report
├── executive_report_builder.py   — Executive Summary Format
├── final_enterprise_report.py    — Enterprise Report + Governance
├── domain_weights.py             — Domain Hierarchy + Subsumption
├── domain_signatures.py          — Engineering Domain Signatures ← LIVING
└── language_registry_expansion.py — File Extension Registry ← LIVING
```

---

## Adding a New Domain

**Step 1 — Add to domain_signatures.py:**

```python
{
    "name":         "AUTOMOTIVE_SYSTEM",
    "packages":     ["cantools", "python-can", "autosar"],
    "file_patterns":["*.arxml", "*.dbc", "*.ldf"],
    "keywords":     ["can_bus", "ecu", "adas", "obd"],
    "min_score":    2,
},
```

**Step 2 — Add file extensions to language_registry_expansion.py:**

```python
# Automotive / CAN Bus
".arxml": "AUTOSAR XML",
".dbc":   "CAN Database",
".ldf":   "LIN Description File",
```

**Step 3 — Run the test suite.**
No other file needs to change.

---

## Adding a New File Extension

```python
# language_registry_expansion.py
# Find the correct domain block and add:
".ext": "Description of file type",
```

Rule: one file, one line, done.
Never touch framework_signatures.py.

---

## Domain Signatures — 16 Domains

| Domain | Key Packages | Key Signals |
|---|---|---|
| AEROSPACE_STRUCTURAL_SIMULATION | pynastran, nastran | *.bdf, *.fem, *.op4 |
| WELL_LOGGING | lasio, welly, striplog | *.las, wireline, gamma_ray |
| DRILLING_SYSTEM | welleng, wellpathpy | wellbore, trajectory, dogleg |
| RESERVOIR_ENGINEERING | pyreservoir, ecl2df | reservoir, pvt, porosity |
| FLUIDS_ENGINEERING | fluids, thermo | reynolds_number, pipe_flow |
| MINING_GEOLOGY | striplog, gempy | stratigraphy, lithology, mineral |
| AUTOMOTIVE_SYSTEM | cantools, python-can | *.arxml, *.dbc, can_bus, ecu |
| CYBERSECURITY_SYSTEM | scapy, pwntools | *.pcap, exploit, payload |
| BIOINFORMATICS_SYSTEM | biopython, pysam | *.fasta, *.vcf, genome |
| QUANTUM_COMPUTING | qiskit, cirq | *.qasm, qubit, quantum_circuit |
| SDR_RADIO_SYSTEM | gnuradio, pyrtlsdr | *.grc, sdr, modulation |
| EMBEDDED_RTOS | zephyr, micropython | *.dts, rtos, bootloader |
| GEOLOGY_STRATIGRAPHY | striplog, welly | *.las, stratigraphy, horizon |
| CHEMICAL_ENGINEERING | thermo, chemicals | thermodynamics, distillation |
| GEOPHYSICS_SEISMIC | obspy, segyio | *.segy, seismic, waveform |
| NUCLEAR_ENGINEERING | openmc, pyne | reactor, neutron, fission |

---

## Language Registry — 218 Extensions / 25 Domain Blocks

```
C#/.NET            Go              TypeScript
WebAssembly        Native Libraries Source Maps
Grammar            Metadata        Templates
Medical Imaging    HL7/FHIR        Aerospace/FEM
Drone/UAV          Energy/Power    Citation/Config
Astronomy          ERP/Enterprise  Automotive/CAN
Cybersecurity      Bioinformatics  Quantum Computing
SDR/Radio          Embedded/RTOS   Geophysics/Seismic
Chemical/Molecular Climate Science FPGA/EDA
ML/AI
```

---

## Governance Gate

```
APPROVED        — all checks passed, proceed to Module 2
REVIEW_REQUIRED — domain unknown or confidence low
BLOCKED         — critical checks failed, must not proceed
```

Gate checks:
1. Cognition Status = COMPLETE
2. Domain Classification known
3. Repository Boundary detected
4. Repository not empty
5. Confidence Score present

---

## Truth Boundary

```
Core classification is the authority.
Evidence strength NONE is acceptable
for specialized engineering repositories
where signal analyzer has no matching keywords.

UNKNOWN is honest — never force a domain.
HUMAN_OVERRIDE stores the human decision
with confidence = UNVERIFIED.
```

---

*CodeTruth Agent V3 — github.com/Zeeshan78699/CodeTruthAgent*
*AI imagines. CodeTruth checks. Nature tests. Humans decide.*
