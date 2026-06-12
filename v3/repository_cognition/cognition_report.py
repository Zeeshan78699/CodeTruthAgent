# cognition_report.py
# Output schema for Repository Cognition Engine.
# CodeTruth Agent V3 — Module 1 — Universal Repository Discovery Engine
#
# Three-tier asset taxonomy:
#   detected_languages    — executable source code only (Python, C++, ABAP etc)
#   detected_file_types   — documents, flat files, data (PDF, Markdown, JSON etc)
#   detected_model_files  — ML/neural network weights (PyTorch, ONNX, SafeTensors etc)
#
# Module 2 consumes detected_languages only for AST parsing.
# Model files are tracked but never passed to any parser.

from dataclasses import dataclass
from typing import Literal


CognitionStatus = Literal["COMPLETE", "PARTIAL", "FAILED"]

ApplicationType = Literal[
    "WEB_APPLICATION",
    "API_SERVICE",
    "CLI_TOOL",
    "ML_PIPELINE",
    "DATA_ENGINEERING",
    "LIBRARY_FRAMEWORK",
    "SAP_INTEGRATION",
    "FINANCE_SYSTEM",
    "DEVOPS_TOOLING",
    "MONOREPO",
    "CODE_GOVERNANCE",
    "ERP_SYSTEM",
    "FRONTEND_APPLICATION",
    "DATABASE_SYSTEM",      # Redis, PostgreSQL, MySQL source repos
    "COMPILER_TOOLCHAIN",   # Rust compiler, LLVM, GCC
    "WEB_SERVER",           # Nginx, Apache source repos
    "GAME_ENGINE",          # Pygame, Panda3D, Unity, Godot
    "EMBEDDED_SYSTEM",      # MicroPython, CircuitPython, Arduino, IoT
    "OPERATING_SYSTEM",     # Linux kernel, FreeBSD
    "CAD_SYSTEM",           # AutoCAD, FreeCAD, SolidWorks, CATIA
    "SIMULATION_TOOL",      # Nastran, ANSYS, OpenFOAM, OpenMDAO
    "BLOCKCHAIN_NODE",      # Ethereum, Solana, Bitcoin
    "MEDICAL_SYSTEM",       # DICOM, HL7, FHIR, neuroimaging
    "QUANTUM_COMPUTING",    # Qiskit, PennyLane, Cirq
    "GIS_SYSTEM",           # GeoPandas, QGIS, ArcGIS
    "FINANCE_SYSTEM",       # QuantLib, Zipline, CCXT
    "ROBOTICS_SYSTEM",      # ROS, ROS2, Drake
    "SCIENTIFIC_COMPUTING", # Astropy, BioPython, RDKit
    "SECURITY_TOOL",        # Scapy, pwntools, Volatility
    "NLP_TOOL",             # spaCy, NLTK, Gensim
    "AUDIO_PROCESSING",     # librosa, SpeechBrain, Whisper
    "COMPUTER_VISION",      # OpenCV, YOLO, Detectron2
    "NETWORK_TOOL",         # Netmiko, NAPALM, Nornir
    "ENERGY_SYSTEM",        # pandapower, PyPSA, pvlib
    "OPTIMIZATION_TOOL",    # OR-Tools, PuLP, Pyomo, CVXPY
    "SPACE_SYSTEM",         # poliastro, sgp4, Skyfield
    "DOCUMENT_PROCESSING",  # pdfplumber, pytesseract, Camelot
    "GRAPH_ANALYTICS",      # NetworkX, iGraph, py2neo
    "ENVIRONMENTAL",        # geemap, pyeto, PlantCV
    "FPGA_HARDWARE",        # cocotb, Amaranth, MyHDL, Migen
    "FIRMWARE",             # Zephyr RTOS, U-Boot, PlatformIO
    "DSP_TOOL",             # GNU Radio, PySDR
    "MOBILE_APPLICATION",   # Kivy, BeeWare, Flet
    "CLOUD_INFRASTRUCTURE", # Terraform, Pulumi, AWS CDK
    "CONTAINER_ORCHESTRATION", # Kubernetes operators, Helm
    "CI_CD_PIPELINE",       # Jenkins, GitLab CI
    "MEDIA_STREAMING",      # FFmpeg, GStreamer
    "DRONE_UAV",            # ArduPilot, MAVLink, DroneKit
    "CLIMATE_SCIENCE",      # xarray, MetPy, Iris
    "UNKNOWN",
]


@dataclass(frozen=True)
class RepositoryCognitionReport:
    """
    Output of the Repository Cognition Engine.
    Frozen immutable contract consumed by all downstream V3 modules.

    Three-tier asset taxonomy:
      detected_languages    → Module 2 AST parser input
      detected_file_types   → logged, skipped by parser
      detected_model_files  → tracked, never parsed (binary blobs)
    """

    # --- Identity ---
    repository_root:        str
    scan_timestamp:         str

    # --- Scale ---
    total_files_scanned:    int
    total_python_files:     int
    total_model_files:      int         # count of ML weight/model files

    # --- Classification ---
    project_purpose:        str
    application_type:       ApplicationType
    primary_framework:      str
    secondary_frameworks:   tuple[str, ...]

    # --- Three-Tier Asset Taxonomy ---
    detected_languages:     tuple[str, ...]  # executable source code only
    detected_file_types:    tuple[str, ...]  # documents, data, flat files
    detected_model_files:   tuple[str, ...]  # ML models and weights

    # --- Infrastructure ---
    technology_stack:       tuple[str, ...]
    build_systems:          tuple[str, ...]
    entry_points:           tuple[str, ...]
    configuration_files:    tuple[str, ...]
    documentation_files:    tuple[str, ...]
    test_directories:       tuple[str, ...]

    # --- Confidence (split) ---
    discovery_score:        float
    classification_score:   float
    confidence_score:       float
    cognition_status:       CognitionStatus

    # --- Audit ---
    warnings:               tuple[str, ...]
    unknown_file_extensions: tuple[str, ...]
    error_message:          str

    def to_dict(self) -> dict:
        return {
            "repository_root":        self.repository_root,
            "scan_timestamp":         self.scan_timestamp,
            "total_files_scanned":    self.total_files_scanned,
            "total_python_files":     self.total_python_files,
            "total_model_files":      self.total_model_files,
            "project_purpose":        self.project_purpose,
            "application_type":       self.application_type,
            "primary_framework":      self.primary_framework,
            "secondary_frameworks":   list(self.secondary_frameworks),
            "detected_languages":     list(self.detected_languages),
            "detected_file_types":    list(self.detected_file_types),
            "detected_model_files":   list(self.detected_model_files),
            "technology_stack":       list(self.technology_stack),
            "build_systems":          list(self.build_systems),
            "entry_points":           list(self.entry_points),
            "configuration_files":    list(self.configuration_files),
            "documentation_files":    list(self.documentation_files),
            "test_directories":       list(self.test_directories),
            "discovery_score":        round(self.discovery_score, 4),
            "classification_score":   round(self.classification_score, 4),
            "confidence_score":       round(self.confidence_score, 4),
            "cognition_status":       self.cognition_status,
            "warnings":               list(self.warnings),
            "unknown_file_extensions": list(self.unknown_file_extensions),
            "error_message":          self.error_message,
        }

    @staticmethod
    def failed(repository_root: str, error_message: str) -> "RepositoryCognitionReport":
        from datetime import datetime, timezone
        return RepositoryCognitionReport(
            repository_root=repository_root,
            scan_timestamp=datetime.now(timezone.utc).isoformat(),
            total_files_scanned=0,
            total_python_files=0,
            total_model_files=0,
            project_purpose="UNKNOWN",
            application_type="UNKNOWN",
            primary_framework="None",
            secondary_frameworks=(),
            detected_languages=(),
            detected_file_types=(),
            detected_model_files=(),
            technology_stack=(),
            build_systems=(),
            entry_points=(),
            configuration_files=(),
            documentation_files=(),
            test_directories=(),
            discovery_score=0.0,
            classification_score=0.0,
            confidence_score=0.0,
            cognition_status="FAILED",
            warnings=(),
            unknown_file_extensions=(),
            error_message=error_message,
        )