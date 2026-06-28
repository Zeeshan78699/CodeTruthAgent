"""
========================================================================
domain_signatures.py
CodeTruth Agent V3 — Module 1 Extension

PURPOSE:
    Domain signature expansion for specialized engineering domains
    not yet in framework_signatures.py (core — frozen).

    This module adds domain-specific detection for:
    - Aerospace / Structural Simulation
    - Oil & Gas / Well Logging
    - Drilling Engineering
    - Reservoir Engineering
    - Fluids / Pipeline Engineering
    - Mining / Geology / Mineral Exploration

    Does NOT modify Module 1 Core.
    framework_signatures.py stays frozen.

RULE:
    New domain discovered → add signatures here →
    run through normalise_application_type() →
    core report enhanced with correct domain label.

STATUS: Extension / Non-breaking
========================================================================
"""

from __future__ import annotations
from pathlib import Path
import re


# ------------------------------------------------------------------
# Domain signature map
# package_name / file_pattern → application_type override
# ------------------------------------------------------------------

DOMAIN_SIGNATURES: list[dict] = [

    {
        "name":         "AEROSPACE_STRUCTURAL_SIMULATION",
        "packages":     ["pynastran", "nastran", "pyansys", "feniics",
                         "openmdao", "avl"],
        "file_patterns":["*.bdf", "*.nas", "*.pch", "*.op4",
                         "*.fem", "*.neu"],   # removed .dat — too generic
        "keywords":     ["nastran", "finite_element", "structural",
                         "aerodynamic", "fuselage", "stress_analysis",
                         "aeroelastic"],
        "min_score":    3,   # higher threshold — prevents false positives
    },
    {
        "name":         "WELL_LOGGING",
        "packages":     ["lasio", "welly", "striplog", "wellpathpy"],
        "file_patterns":["*.las", "*.dlis", "*.dlisio"],
        "keywords":     ["well_log", "las_file", "wireline", "gamma_ray",
                         "resistivity", "formation", "borehole"],
    },
    {
        "name":         "DRILLING_SYSTEM",
        "packages":     ["welleng", "wellpathpy", "pydrill"],
        "file_patterns":["*.welleng", "*.trajectory"],
        "keywords":     ["wellbore", "trajectory", "drilling", "anti_collision",
                         "dogleg", "borehole", "bit_depth", "torque_drag"],
    },
    {
        "name":         "RESERVOIR_ENGINEERING",
        "packages":     ["pyreservoir", "reservoirpy", "mrst",
                         "ecl2df", "resfo"],
        "file_patterns":["*.grdecl", "*.egrid", "*.smspec"],
        "keywords":     ["reservoir", "permeability", "porosity",
                         "pvt", "ipr", "material_balance", "vlp",
                         "decline_curve", "fluid_contact"],
    },
    {
        "name":         "FLUIDS_ENGINEERING",
        "packages":     ["fluids", "thermo", "chemicals", "pipeflow"],
        "file_patterns":["*.pip", "*.pfd"],
        "keywords":     ["reynolds_number", "friction_factor", "pressure_drop",
                         "pipe_flow", "nozzle", "valve_cv", "fluid_dynamics",
                         "darcy", "bernoulli"],
    },
    {
        "name":         "MINING_GEOLOGY",
        "packages":     ["striplog", "gempy", "miningpy", "lasio",
                         "geoh5py", "omf", "welly"],
        "file_patterns":["*.omf", "*.gslib", "*.sgems", "*.las"],
        "keywords":     ["stratigraphy", "lithology", "ore_grade",
                         "assay", "drillhole", "geological_log",
                         "mineral_exploration", "mineral_deposit",
                         "striplog_interval", "well_log", "core_sample",
                         "rock_type", "borehole_collar"],
        # Raised from 2 → 4: generic words (component/interval/legend/fault)
        # appear in every large Python repo — require stronger evidence
        "min_score":    4,
    },

    {
        "name":         "AUTOMOTIVE_SYSTEM",
        "packages":     ["cantools", "python-can", "autosar", "pyautosarparser",
                         "udsoncan", "can"],
        "file_patterns":["*.arxml", "*.dbc", "*.ldf", "*.fibex"],
        "keywords":     ["can_bus", "ecu", "adas", "obd", "autosar",
                         "lin_bus", "vehicle_network", "flexray",
                         "diagnostic", "uds", "xcp"],
        "min_score":    2,
    },
    {
        "name":         "CYBERSECURITY_SYSTEM",
        "packages":     ["scapy", "pwntools", "impacket", "pyshark",
                         "cryptography", "paramiko", "nmap"],
        "file_patterns":["*.pcap", "*.pcapng", "*.cap"],
        "keywords":     ["exploit", "payload", "shellcode", "buffer_overflow",
                         "penetration_test", "vulnerability", "fuzzing",
                         "reverse_shell", "privilege_escalation"],
        "min_score":    2,
    },
    {
        "name":         "BIOINFORMATICS_SYSTEM",
        "packages":     ["biopython", "pysam", "pyvcf", "biotite",
                         "scikit-bio", "dendropy", "ete3"],
        "file_patterns":["*.fasta", "*.fastq", "*.vcf", "*.bam",
                         "*.bed", "*.gff", "*.gtf", "*.gb"],
        "keywords":     ["genome", "sequence", "dna", "rna", "protein",
                         "alignment", "phylogeny", "variant", "annotation",
                         "blast", "bowtie", "samtools"],
        "min_score":    2,
    },
    {
        "name":         "QUANTUM_COMPUTING",
        "packages":     ["qiskit", "cirq", "pennylane", "pyquil",
                         "braket", "strawberryfields"],
        "file_patterns":["*.qasm", "*.qpy"],
        "keywords":     ["qubit", "quantum_circuit", "entanglement",
                         "superposition", "quantum_gate", "bloch_sphere",
                         "transpile", "backend_simulator", "statevector"],
        "min_score":    2,
    },
    {
        "name":         "SDR_RADIO_SYSTEM",
        "packages":     ["gnuradio", "pyrtlsdr", "soapysdr", "gr-osmosdr",
                         "pysdr", "sigmf"],
        "file_patterns":["*.grc", "*.sigmf", "*.sigmf-meta"],
        "keywords":     ["software_defined_radio", "sdr", "flowgraph",
                         "modulation", "demodulation", "frequency",
                         "spectrum", "signal_processing", "rf_signal",
                         "gnuradio", "rtlsdr", "hackrf"],
        "min_score":    2,
    },
    {
        "name":         "EMBEDDED_RTOS",
        "packages":     ["zephyr", "micropython", "mbed", "freertos",
                         "uboot", "pyserial"],
        "file_patterns":["*.kconfig", "*.dtsi", "*.dts", "*.ld",
                         "*.cmake"],
        "keywords":     ["rtos", "bootloader", "device_tree", "kernel",
                         "firmware", "interrupt_handler", "scheduler",
                         "memory_map", "peripheral", "u_boot", "zephyr"],
        "min_score":    2,
    },
    {
        "name":         "GEOLOGY_STRATIGRAPHY",
        "packages":     ["striplog", "gempy", "welly", "lasio",
                         "bruges", "geoh5py"],
        "file_patterns":["*.las", "*.dlis", "*.omf", "*.gslib"],
        "keywords":     ["stratigraphy", "lithology", "formation",
                         "stratigraphic", "interval", "legend", "component",
                         "core_sample", "geological_column", "horizon",
                         "facies", "rock_type"],
        "min_score":    2,
    },
    {
        "name":         "CHEMICAL_ENGINEERING",
        "packages":     ["thermo", "chemicals", "fluids", "cantera",
                         "pychemqt", "openbabel"],
        "file_patterns":["*.mol", "*.sdf", "*.cif", "*.xyz"],
        "keywords":     ["thermodynamics", "heat_transfer", "reaction",
                         "enthalpy", "entropy", "fugacity", "vapor_pressure",
                         "distillation", "absorption", "chemical_process"],
        "min_score":    2,
    },
    {
        "name":         "GEOPHYSICS_SEISMIC",
        "packages":     ["obspy", "segyio", "pyrocko", "bruges",
                         "fatiando"],
        "file_patterns":["*.segy", "*.sgy", "*.seg", "*.mseed"],
        "keywords":     ["seismic", "waveform", "earthquake", "seismogram",
                         "velocity_model", "reflection", "refraction",
                         "p_wave", "s_wave", "magnitude", "epicenter"],
        "min_score":    2,
    },
    {
        "name":         "NUCLEAR_ENGINEERING",
        "packages":     ["openmc", "serpent", "pyne", "uncertainties"],
        "file_patterns":["*.xml", "*.inp"],
        "keywords":     ["reactor", "neutron", "fission", "cross_section",
                         "criticality", "burnup", "isotope", "radiation",
                         "shielding", "decay_heat", "fuel_assembly"],
        "min_score":    3,   # higher threshold — XML is too generic
    },

]


def detect_domain_from_signatures(repo_path: str) -> "str | None":
    """
    Scans the repository for domain-specific signals not covered
    by framework_signatures.py.

    Returns the domain name if matched, None otherwise.
    Each match is evidence-based — package presence or file patterns.
    """
    root = Path(repo_path)
    if not root.exists():
        return None

    # Collect package references from dependency files
    pkg_content = ""
    for dep_file in ["requirements.txt", "pyproject.toml",
                     "setup.py", "setup.cfg"]:
        p = root / dep_file
        if p.exists():
            try:
                pkg_content += p.read_text(
                    encoding="utf-8", errors="ignore"
                ).lower()
            except Exception:
                pass

    # Collect file extensions in repo (depth ≤ 4)
    repo_extensions: set[str] = set()
    repo_names: list[str] = []
    try:
        for item in root.rglob("*"):
            depth = len(item.relative_to(root).parts)
            if depth > 4:
                continue
            if item.is_file():
                repo_extensions.add(item.suffix.lower())
                repo_names.append(item.name.lower())
    except Exception:
        pass

    # Collect keyword signals from filenames and folder names
    name_blob = " ".join(repo_names)

    # Score each domain
    for sig in DOMAIN_SIGNATURES:
        score = 0

        # Package signal
        for pkg in sig["packages"]:
            if pkg.lower() in pkg_content:
                score += 3

        # File pattern signal
        for pattern in sig.get("file_patterns", []):
            ext = pattern.replace("*", "").lower()
            if ext in repo_extensions:
                score += 2

        # Keyword signal
        for kw in sig.get("keywords", []):
            if kw.replace("_", " ") in name_blob or kw in name_blob:
                score += 1

        min_score = sig.get("min_score", 2)   # per-signature threshold
        if score >= min_score:
            return sig["name"]

    return None


def get_enhanced_application_type(
    current_type: str,
    repo_path: str,
) -> str:
    """
    Returns a more specific application type if domain signatures
    provide stronger evidence than the core classification.

    Core type is only overridden when:
    1. Current type is generic (DATA_ENGINEERING, GRAPH_ANALYTICS,
       SIMULATION_TOOL, MONOREPO, UNKNOWN)
    2. Domain signatures find specific evidence

    Core-specific classifications (FINANCE_SYSTEM, ENERGY_SYSTEM etc.)
    are preserved as-is — they are already correct.
    """
    GENERIC_TYPES = {
        "DATA_ENGINEERING", "GRAPH_ANALYTICS", "SIMULATION_TOOL",
        "MONOREPO", "UNKNOWN", "SCIENTIFIC_SYSTEM", "LIBRARY",
    }

    # OI-010 FIX: ML/AI repos must not be overridden to engineering domains.
    # PyTorch/TensorFlow use networkx internally → GRAPH_ANALYTICS triggers
    # MINING_GEOLOGY incorrectly. Check ML signals first before any override.
    # Strict ML packages only — NOT scientific computing utilities
    # numpy/scipy/pandas are used by aerospace, climate, chemistry too
    ML_PACKAGES = {
        "torch", "pytorch", "tensorflow", "keras", "jax",
        "xgboost", "lightgbm", "transformers", "huggingface",
        "mxnet", "caffe", "theano", "paddlepaddle",
    }
    if current_type in GENERIC_TYPES:
        try:
            root = Path(repo_path)
            for dep_file in [root / "requirements.txt",
                             root / "pyproject.toml",
                             root / "setup.py",
                             root / "setup.cfg"]:
                if dep_file.exists():
                    content = dep_file.read_text(
                        encoding="utf-8", errors="ignore"
                    ).lower()
                    if any(ml in content for ml in ML_PACKAGES):
                        return "ML_PIPELINE"
        except Exception:
            pass

    # For ML_PIPELINE — only override if ML is NOT confirmed
    # PyTorch/TensorFlow repos ARE ML — never override them
    # OpenMDAO/pyNastran use scipy but ARE engineering — override them
    if current_type == "ML_PIPELINE":
        ML_CONFIRMED = {
            "torch", "pytorch", "tensorflow", "keras",
            "transformers", "huggingface", "mxnet", "caffe",
            # NOTE: jax removed — used by scientific/engineering repos too
            # (OpenMDAO uses jax for automatic differentiation)
        }
        try:
            root_p = Path(repo_path)
            # Check 1: repo folder name
            if any(ml in root_p.name.lower() for ml in ML_CONFIRMED):
                return current_type  # e.g. "pytorch" folder = ML confirmed

            # Check 2: top-level package directories
            for item in root_p.iterdir():
                if item.is_dir() and item.name.lower() in ML_CONFIRMED:
                    return current_type  # e.g. "torch/" dir = ML confirmed

            # Check 3: dependency files
            for dep in [root_p / "requirements.txt", root_p / "pyproject.toml",
                        root_p / "setup.py", root_p / "setup.cfg"]:
                if dep.exists():
                    content = dep.read_text(encoding="utf-8", errors="ignore").lower()
                    if any(ml in content for ml in ML_CONFIRMED):
                        return current_type  # ML package found = ML confirmed
        except Exception:
            pass

        # ML NOT confirmed — check if it is actually engineering
        engineering_domain = detect_domain_from_signatures(repo_path)
        if engineering_domain:
            return engineering_domain
        return current_type

    if current_type not in GENERIC_TYPES:
        return current_type   # already specific — preserve it

    domain = detect_domain_from_signatures(repo_path)
    return domain if domain else current_type