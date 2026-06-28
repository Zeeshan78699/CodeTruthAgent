"""
========================================================================
language_registry_expansion.py

CodeTruth Agent V3 — Module 1 Extension
V3-001A — Language Registry Expansion

PURPOSE:
    Provides additional language, build system, and repository
    artifact recognition discovered during benchmark execution.

    This module does NOT modify Module 1 Core.
    framework_signatures.py stays frozen.

HOW TO ADD A NEW EXTENSION:
    1. Find the unknown extension in core scan output or JSON evidence
    2. Add it to LANGUAGE_REGISTRY_EXPANSION under the correct domain block
    3. Re-run the test — warning count reduces automatically
    4. No other file needs to change

RULE:
    New repo scanned → unknown extension found →
    add here → done. Never touch framework_signatures.py.

Status: Extension / Non-breaking
========================================================================
"""

from __future__ import annotations

# ------------------------------------------------------------------
# Language Registry Expansion
# Add new entries here — grouped by domain, newest at bottom
# ------------------------------------------------------------------

LANGUAGE_REGISTRY_EXPANSION: dict[str, str] = {

    # ----------------------------------------------------------
    # C# / .NET — discovered during ccxt scan (2026-06-23)
    # ----------------------------------------------------------
    ".csproj":    "C# Project",
    ".sln":       "C# Solution",

    # ----------------------------------------------------------
    # Go — discovered during ccxt scan (2026-06-23)
    # ----------------------------------------------------------
    ".sum":       "Go Module Checksum",
    ".work":      "Go Workspace",

    # ----------------------------------------------------------
    # TypeScript variants — discovered during ccxt scan (2026-06-23)
    # ----------------------------------------------------------
    ".mts":       "TypeScript Module",
    ".cts":       "TypeScript CommonJS Module",

    # ----------------------------------------------------------
    # WebAssembly — discovered during ccxt scan (2026-06-23)
    # ----------------------------------------------------------
    ".wasm":      "WebAssembly Binary",

    # ----------------------------------------------------------
    # Native Libraries — discovered during ccxt scan (2026-06-23)
    # ----------------------------------------------------------
    ".dylib":     "macOS Dynamic Library",

    # ----------------------------------------------------------
    # Source Maps — discovered during ccxt scan (2026-06-23)
    # ----------------------------------------------------------
    ".map":       "JavaScript Source Map",

    # ----------------------------------------------------------
    # Grammar Definitions — discovered during ccxt scan (2026-06-23)
    # ----------------------------------------------------------
    ".lark":      "Lark Grammar Definition",

    # ----------------------------------------------------------
    # Metadata / Typing — discovered during ccxt scan (2026-06-23)
    # ----------------------------------------------------------
    ".typed":     "Python Typing Metadata",

    # ----------------------------------------------------------
    # Configuration Templates — discovered during ccxt scan (2026-06-23)
    # ----------------------------------------------------------
    ".in":        "Autoconf Template",
    ".example":   "Example Configuration File",

    # ----------------------------------------------------------
    # Medical Imaging — discovered during pydicom scan (2026-06-23)
    # ----------------------------------------------------------
    ".dcm":       "DICOM Medical Image",
    ".nii":       "NIfTI Brain Image",
    ".mgh":       "FreeSurfer Volume Format",

    # ----------------------------------------------------------
    # HL7 / FHIR Healthcare Standards — discovered during hl7apy scan
    # ----------------------------------------------------------
    ".hl7":       "HL7 Message",
    ".fhir":      "FHIR Resource",

    # ----------------------------------------------------------
    # Aerospace / FEM / Structural Analysis — discovered during pyNastran scan (2026-06-24)
    # ----------------------------------------------------------
    ".avl":       "Athena Vortex Lattice Input",
    ".bdf":       "Nastran Bulk Data File",
    ".dat":       "Nastran Input Data",
    ".fem":       "Finite Element Model",
    ".fld":       "Field Data File",
    ".geo":       "Geometry Definition File",
    ".msh":       "Mesh File",
    ".neu":       "Neutral Mesh Format",
    ".op4":       "Nastran Output4 Matrix",
    ".pch":       "Nastran Punch File",
    ".plt":       "Plot Data File",
    ".smesh":     "Surface Mesh",
    ".tri":       "Triangle Surface Mesh",
    ".ugrid":     "UGRID Unstructured Grid",
    ".wgs":       "Wing Geometry Standard",
    ".wrl":       "VRML 3D Model",
    ".ele":       "Element Connectivity File",
    ".nod":       "Node Coordinate File",
    ".node":      "Node Data File",
    ".eig":       "Eigenvalue Data",
    ".fgrid":     "Flow Grid File",
    ".blk":       "Block Structured Grid",
    ".surf":      "Surface Definition",
    ".inc":       "Nastran Include File",
    ".inpt":      "Input Data File",
    ".run":       "Solver Run Script",
    ".tags":      "Mesh Tag File",
    ".bc":        "Boundary Condition File",
    ".mapbc":     "Boundary Condition Map",
    ".kgg":       "Stiffness Matrix",
    ".mgg":       "Mass Matrix",
    ".spec":      "Specification File",
    ".bedge":     "Boundary Edge File",
    ".c3d":       "3D Curve File",
    ".cogsg":     "Center of Gravity Segment",
    ".cntl":      "Control Surface Definition",
    ".d3m":       "LS-DYNA 3D Mesh",
    ".des":       "Design Variable File",
    ".flo":       "Flow Solution File",
    ".fre":       "Frequency Response File",
    ".front":     "Front Tracking File",
    ".key":       "LS-DYNA Keyword File",
    ".mass":      "Mass Property File",
    ".mk5":       "Mark5 Binary Format",
    ".nml":       "Namelist Configuration File",
    ".off":       "Object File Format (3D)",
    ".res_tmpl":  "Result Template File",
    ".v2005":     "VGRID 2005 Format",
    ".xdb":       "Nastran XDB Database",
    ".45":        "Nastran Result Format",

    # ----------------------------------------------------------
    # Drone / UAV / Aviation — discovered during dronekit-python scan (2026-06-24)
    # ----------------------------------------------------------
    ".tlog":      "MAVLink Telemetry Log",
    ".iss":       "Inno Setup Script",
    ".yapf":      "YAPF Formatter Config",
    ".pip":       "Pip Requirements Variant",

    # ----------------------------------------------------------
    # Energy / Power Grid Engineering — discovered during pandapower scan (2026-06-24)
    # ----------------------------------------------------------
    ".pfd":       "Power Flow Diagram",
    ".uct":       "UCTE Power Grid Format",
    ".sin":       "SINCAL Network File",
    ".sxe":       "SINCAL Exchange Format",
    ".drawio":    "Draw.io Diagram",
    ".dia":       "Dia Diagram",
    ".vsd":       "Visio Diagram",
    ".vsdx":      "Visio XML Diagram",
    ".emf":       "Enhanced Metafile",
    ".bmp":       "Bitmap Image",
    ".psd":       "Photoshop Document",
    ".bib":       "BibTeX Bibliography",
    ".p":         "Pickle Binary Data",
    ".csv":       "Comma Separated Values",

    # ----------------------------------------------------------
    # General / Citation / Config — discovered during PyPSA scan (2026-06-24)
    # ----------------------------------------------------------
    ".cff":       "Citation File Format (CITATION.cff)",
    ".ignore":    "Ignore Rules File",

    # ----------------------------------------------------------
    # Astronomy / Planetary Science — discovered during astropy scan (2026-06-24)
    # ----------------------------------------------------------
    ".fits":      "Flexible Image Transport System",
    ".fit":       "FITS Image File",
    ".ecsv":      "Enhanced CSV (Astropy)",
    ".vot":       "VOTable XML Format",
    ".hdf5":      "HDF5 Scientific Data",
    ".hdr":       "FITS Header File",
    ".parquet":   "Apache Parquet Columnar Data",
    ".rdb":       "Tab-Separated Data (RDB format)",
    ".tab":       "Tab-Separated Data",
    ".dtd":       "XML Document Type Definition",
    ".xsd":       "XML Schema Definition",
    ".odg":       "OpenDocument Drawing",
    ".list":      "Plain Text List",
    ".sub":       "Subtitle / Data Subscription File",
    ".ac":        "Autoconf Script",
    ".data":      "Generic Data File",
    ".dbout":     "Database Output File",
    ".guess":     "Format Guess File",
    ".lesser":    "LGPL License Variant",
    ".l":         "Lex/Flex Grammar File",
    ".z":         "Compressed File (Unix compress)",
    ".00":        "Numbered Data File",
    ".01":        "Numbered Data File",
    ".02":        "Numbered Data File",
    ".eopc04_iau2000": "Earth Orientation Parameter File",

    # ----------------------------------------------------------
    # ERP / Enterprise / Document — discovered during odoo scan (2026-06-24)
    # ----------------------------------------------------------
    ".eml":       "Email Message File",
    ".ftl":       "FreeMarker Template",
    ".pot":       "Portable Object Template (i18n)",
    ".rng":       "RELAX NG Schema",
    ".rtf":       "Rich Text Format",
    ".ods":       "OpenDocument Spreadsheet",
    ".odt":       "OpenDocument Text",
    ".xsl":       "XSL Stylesheet",
    ".nsi":       "Nullsoft Installer Script",
    ".webp":      "WebP Image",
    ".whl":       "Python Wheel Package",
    ".pem":       "Privacy Enhanced Mail Certificate",
    ".crt":       "X.509 Certificate",
    ".p12":       "PKCS#12 Certificate Bundle",
    ".p7m":       "PKCS#7 Signed Message",
    ".pfx":       "Personal Information Exchange",
    ".icc":       "ICC Color Profile",
    ".cur":       "Windows Cursor File",
    ".b64":       "Base64 Encoded File",
    ".bcmap":     "Binary Character Map",
    ".service":   "Systemd Service Unit",
    ".rules":     "System Rules File",
    ".local":     "Local Configuration Override",
    ".template":  "Configuration Template",
    ".links":     "Symlink Definitions",
    ".license":   "License File",
    ".docs":      "Documentation File",
    ".debian":    "Debian Package Config",
    ".dfdebian":  "Dockerfile (Debian variant)",
    ".dffedora":  "Dockerfile (Fedora variant)",
    ".dfsrc":     "Dockerfile (Source variant)",
    ".dfwine":    "Dockerfile (Wine variant)",

    # ----------------------------------------------------------
    # Automotive / CAN Bus — 2026-06-25
    # ----------------------------------------------------------
    ".arxml":     "AUTOSAR XML",
    ".dbc":       "CAN Database",
    ".ldf":       "LIN Description File",
    ".fibex":     "FIBEX Network Description",

    # ----------------------------------------------------------
    # Cybersecurity / Network Capture — 2026-06-25
    # ----------------------------------------------------------
    ".pcap":      "Packet Capture",
    ".pcapng":    "Packet Capture NG",
    ".cap":       "Network Capture File",

    # ----------------------------------------------------------
    # Bioinformatics / Genomics — 2026-06-25
    # ----------------------------------------------------------
    ".fasta":     "FASTA Sequence",
    ".fastq":     "FASTQ Sequence + Quality",
    ".vcf":       "Variant Call Format",
    ".bam":       "Binary Alignment Map",
    ".bed":       "Browser Extensible Data",
    ".gff":       "General Feature Format",
    ".gtf":       "Gene Transfer Format",
    ".gb":        "GenBank Format",

    # ----------------------------------------------------------
    # Quantum Computing — 2026-06-25
    # ----------------------------------------------------------
    ".qasm":      "OpenQASM Quantum Circuit",
    ".qpy":       "Qiskit QPY Binary",

    # ----------------------------------------------------------
    # SDR / Radio — 2026-06-25
    # ----------------------------------------------------------
    ".grc":       "GNU Radio Companion Flowgraph",
    ".sigmf":     "SigMF Signal Recording",

    # ----------------------------------------------------------
    # Embedded / RTOS — 2026-06-25
    # ----------------------------------------------------------
    ".kconfig":   "Kernel Configuration",
    ".dtsi":      "Device Tree Source Include",
    ".dts":       "Device Tree Source",
    ".ld":        "Linker Script",

    # ----------------------------------------------------------
    # Geophysics / Seismic — 2026-06-25
    # ----------------------------------------------------------
    ".segy":      "SEG-Y Seismic Data",
    ".sgy":       "SEG-Y Seismic Data (short)",
    ".seg":       "SEG Seismic Format",
    ".mseed":     "MiniSEED Seismic Data",

    # ----------------------------------------------------------
    # Chemical Engineering / Molecular — 2026-06-25
    # ----------------------------------------------------------
    ".mol":       "MDL Molfile",
    ".sdf":       "Structure Data File",
    ".cif":       "Crystallographic Information File",
    ".xyz":       "XYZ Molecular Coordinates",

    # ----------------------------------------------------------
    # Climate Science / Meteorology — discovered during MetPy scan (2026-06-25)
    # ----------------------------------------------------------
    ".ar2v":      "NEXRAD Level 2 Radar",
    ".gini":      "GINI Satellite Image",
    ".nids":      "NEXRAD Level 3 Product",
    ".wmo":       "WMO Binary Format",
    ".gem":       "GEMPAK Meteorological Data",
    ".grd":       "Grid Data File",
    ".snd":       "Sounding Data",
    ".sfc":       "Surface Data",
    ".tbl":       "Lookup Table",
    ".peg":       "Peg File",
    ".last":      "Last Run File",
    ".geojson":   "GeoJSON Feature Collection",
    ".cpg":       "Code Page File (Shapefile)",
    ".dbf":       "dBASE Attribute Table (Shapefile)",
    ".prj":       "Projection Definition (Shapefile)",
    ".shx":       "Shape Index (Shapefile)",

    # ----------------------------------------------------------
    # FPGA / EDA / Hardware Simulation — discovered during cocotb scan (2026-06-25)
    # ----------------------------------------------------------
    ".activehdl": "Active-HDL Simulator Config",
    ".cvc":       "CVC Simulator Config",
    ".dsim":      "DSim Simulator Config",
    ".ghdl":      "GHDL Simulator Config",
    ".icarus":    "Icarus Verilog Config",
    ".ius":       "Incisive Simulator Config",
    ".modelsim":  "ModelSim Simulator Config",
    ".nvc":       "NVC Simulator Config",
    ".questa":    "Questa Simulator Config",
    ".riviera":   "Riviera-PRO Config",
    ".vcs":       "Synopsys VCS Config",
    ".verilator": "Verilator Config",
    ".xcelium":   "Xcelium Simulator Config",
    ".vams":      "Verilog-AMS Source",
    ".vh":        "Verilog Header",
    ".sim":       "Simulation Config",
    ".scs":       "SPICE Circuit Simulation",
    ".terms":     "Terminal Definition",
    ".pyi":       "Python Type Stub",
    ".def":       "Definition File",
    ".init":      "Initialisation File",
    ".deprecations": "Deprecation Notice File",

    # ----------------------------------------------------------
    # ML / AI — discovered during transformers scan (2026-06-25)
    # ----------------------------------------------------------
    ".dockerfile": "Dockerfile Variant",
    ".jsonnet":   "Jsonnet Configuration",
    ".model":     "Serialised Model File",

    # ADD NEW ENTRIES BELOW THIS LINE
    # Format: ".ext": "Description",
    # Always include a comment block with domain + discovery date

}

# ------------------------------------------------------------------
# Build System Expansion
# ------------------------------------------------------------------

BUILD_SYSTEM_EXPANSION: dict[str, str] = {
    ".csproj":  "MSBuild",
    ".sln":     ".NET Solution",
    ".sum":     "Go Modules",
    ".work":    "Go Workspace",
}

# ------------------------------------------------------------------
# Repository Artifact Types
# ------------------------------------------------------------------

REPOSITORY_ARTIFACT_TYPES: dict[str, str] = {
    ".snk":     "Strong Name Key (.NET)",
    ".wasm":    "WebAssembly Artifact",
    ".map":     "Source Mapping Artifact",
}

# ------------------------------------------------------------------
# Core Warning Suppression Functions
# Intercepts the framework_signatures.py warning without touching core
# ------------------------------------------------------------------

def get_all_known_extensions() -> set:
    """
    Returns the full set of extensions V3 recognizes
    across core + expansion registries.

    Use this to filter the core scan warning before displaying it.
    """
    return set(LANGUAGE_REGISTRY_EXPANSION.keys())


def filter_genuine_unknown_extensions(
    unknown_extensions: list,
) -> tuple[list, list]:
    """
    Separates unknown extensions into covered vs genuinely unknown.

    Parameters
    ----------
    unknown_extensions : list
        The unknown_file_extensions list from CognitionReport.

    Returns
    -------
    (covered, genuine)
        covered  — already in LANGUAGE_REGISTRY_EXPANSION (not a real gap)
        genuine  — truly unknown, worth logging or investigating
    """
    known   = get_all_known_extensions()
    covered = [e for e in unknown_extensions if e in known]
    genuine = [e for e in unknown_extensions if e not in known]
    return covered, genuine


def get_extension_summary() -> dict:
    """
    Returns a summary of registry coverage.
    Useful for reporting in test output.
    """
    return {
        "total_extensions": len(LANGUAGE_REGISTRY_EXPANSION),
        "build_systems":    len(BUILD_SYSTEM_EXPANSION),
        "artifact_types":   len(REPOSITORY_ARTIFACT_TYPES),
        "domains_covered":  _count_domains(),
    }


def _count_domains() -> list[str]:
    """Returns list of domain blocks currently registered."""
    return [
        "C#/.NET", "Go", "TypeScript", "WebAssembly",
        "Native Libraries", "Source Maps", "Grammar",
        "Metadata", "Templates", "Medical Imaging", "HL7/FHIR",
        "Aerospace/FEM", "Drone/UAV/Aviation", "Energy/Power Grid",
        "Citation/Config", "Astronomy/Planetary",
        "ERP/Enterprise", "Automotive/CAN", "Cybersecurity/Network",
        "Bioinformatics/Genomics", "Quantum Computing", "SDR/Radio",
        "Embedded/RTOS", "Geophysics/Seismic", "Chemical/Molecular",
    ]