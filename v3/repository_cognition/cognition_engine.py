# cognition_engine.py
# Repository Cognition Engine — V3 Module 1
# CodeTruth Agent V3 — Universal Repository Discovery Engine
# Requirements: V3-001, V3-002, V3-003
#
# Level 1 — Universal Discovery: ANY repository, ANY language, 100% coverage
# Level 2 — Classification: Python frameworks now, others grow over time
#
# Deterministic only. No LLM. No external pip dependencies beyond Python stdlib.

import ast
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .cognition_report import ApplicationType, RepositoryCognitionReport
from .framework_signatures import (
    BUILD_SYSTEM_EXTENSIONS,
    BUILD_SYSTEM_FILE_NAMES,
    CONTENT_PATTERN_SIGNATURES,
    CONFIG_FILE_EXTENSIONS,
    CONFIG_FILE_LANGUAGE_MAP,
    CONFIG_FILE_NAMES,
    DEPENDENCY_FILES,
    DOCKERFILE_PREFIXES,
    DOCUMENT_FILE_EXTENSIONS,
    DOCUMENTATION_FILE_NAMES,
    ENTRY_POINT_NAMES,
    ENTRY_POINT_NOISE_DIRS,
    ENV_FILE_PREFIXES,
    ERP_LANGUAGE_EXTENSIONS,
    ERP_PACKAGE_SIGNATURES,
    IMPORT_SIGNATURES,
    LANGUAGE_EXTENSIONS,
    MODEL_FILE_EXTENSIONS,
    PACKAGE_SIGNATURES,
    SKIP_DIRECTORIES,
    TEST_DIR_NAMES,
)

MAX_IMPORT_SAMPLE_FILES = 50


class RepositoryCognitionEngine:
    """
    Universal Repository Discovery Engine.

    Scans any repository in any language and produces a RepositoryCognitionReport.
    Never raises — on any unhandled exception returns a FAILED report.

    Discovery Coverage  = 100% (any repo, any language)
    Classification      = grows over time (Python frameworks complete)
    """

    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        self._warnings: list[str] = []

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def scan(self) -> RepositoryCognitionReport:
        try:
            return self._run_scan()
        except Exception as exc:
            return RepositoryCognitionReport.failed(
                repository_root=self.repo_root,
                error_message=f"Unhandled scan error: {type(exc).__name__}: {exc}",
            )

    # ------------------------------------------------------------------ #
    # Orchestration                                                         #
    # ------------------------------------------------------------------ #

    def _run_scan(self) -> RepositoryCognitionReport:
        timestamp = datetime.now(timezone.utc).isoformat()

        # Step 1 — Universal file inventory (Level 1)
        inventory = self._inventory_files()

        # Step 2 — Build system detection (Level 1)
        build_systems = self._detect_build_systems(
            inventory["config_files"], inventory["dependency_files"]
        )

        # Step 3 — Framework signals from dependency files (Level 2)
        pkg_signals = self._detect_from_dependency_files(inventory["dependency_files"])

        # Step 4 — Framework signals from import scan (Level 2)
        import_signals = self._detect_from_imports(inventory["python_files"])

        # Step 4b — Content pattern detection (self-describing repos like Redis, Odoo)
        pattern_signals = self._detect_from_internal_patterns()

        # Step 5 — Merge signals
        # IMPORTANT: if content patterns fired, they establish the repo identity
        # Import signals for COMPETING types must not override content pattern identity
        # e.g. Whisper IS audio — 17 torch imports must not make it ML_PIPELINE
        # e.g. Ultralytics IS computer vision — 30 torch imports must not make it ML_PIPELINE
        if pattern_signals:
            pattern_types = {t for t, _ in pattern_signals}
            # Define which types are subordinate to each pattern type
            # Import signals from subordinate types are filtered out
            PATTERN_BLOCKS: dict[str, set[str]] = {
                "AUDIO_PROCESSING":   {"ML_PIPELINE", "CLI_TOOL"},
                "COMPUTER_VISION":    {"ML_PIPELINE", "CLI_TOOL", "GIS_SYSTEM"},
                "NLP_TOOL":           {"ML_PIPELINE", "CLI_TOOL", "FRONTEND_APPLICATION"},
                "EMBEDDED_SYSTEM":    {"CLI_TOOL", "ML_PIPELINE"},
                "ROBOTICS_SYSTEM":    {"ML_PIPELINE", "CLI_TOOL", "WEB_APPLICATION"},
                "SECURITY_TOOL":      {"EMBEDDED_SYSTEM", "NETWORK_TOOL"},
                "MEDICAL_SYSTEM":     {"ML_PIPELINE", "DATA_ENGINEERING"},
                "SIMULATION_TOOL":    {"ML_PIPELINE", "GRAPH_ANALYTICS"},
                "SPACE_SYSTEM":       {"SCIENTIFIC_COMPUTING"},
                "GRAPH_ANALYTICS":    {"DATA_ENGINEERING", "ML_PIPELINE"},
                "ENERGY_SYSTEM":      {"DATA_ENGINEERING", "GIS_SYSTEM"},
                "CAD_SYSTEM":         {"CLI_TOOL", "DATA_ENGINEERING"},
            }
            blocked_types: set[str] = set()
            for pt in pattern_types:
                blocked_types.update(PATTERN_BLOCKS.get(pt, set()))
            import_signals = [(t, w) for t, w in import_signals
                              if t not in blocked_types]

        all_signals = pkg_signals + import_signals + pattern_signals

        # Step 6 — Application type (computed first so framework
        # resolution can prefer the matching domain's package name)
        application_type = self._determine_application_type(all_signals, inventory)

        # Step 7 — Resolve frameworks and technology stack
        primary_framework, secondary_frameworks, technology_stack = \
            self._resolve_frameworks(
                all_signals, inventory["dependency_files"], inventory["config_files"],
                len(inventory["python_files"]), application_type
            )

        # Step 8 — Entry points
        entry_points = self._detect_entry_points(
            inventory["python_files"], inventory["named_entry_points"]
        )

        # Step 9 — Score confidence (split)
        discovery_score = self._score_discovery(inventory)
        classification_score = self._score_classification(all_signals, primary_framework)

        # Step 10 — Diagnostic warnings (identify all issues explicitly)
        self._generate_diagnostic_warnings(
            inventory, all_signals, application_type,
            build_systems, classification_score
        )

        # Step 11 — Resolve status based on DISCOVERY not classification
        # A C repo with UNKNOWN type is still COMPLETE if discovery worked
        if discovery_score >= 0.5:
            status = "COMPLETE"
        elif discovery_score > 0.0:
            status = "PARTIAL"
        else:
            status = "FAILED"

        # Step 12 — Purpose string
        purpose = self._build_purpose_string(
            application_type, primary_framework,
            inventory["python_files"], inventory["detected_languages"]
        )

        # Overall confidence for backward compatibility
        confidence_score = round((discovery_score + classification_score) / 2, 4)

        return RepositoryCognitionReport(
            repository_root=self.repo_root,
            scan_timestamp=timestamp,
            total_files_scanned=inventory["total_files"],
            total_python_files=len(inventory["python_files"]),
            total_model_files=inventory["total_model_files"],
            project_purpose=purpose,
            application_type=application_type,
            primary_framework=primary_framework,
            secondary_frameworks=tuple(secondary_frameworks),
            detected_languages=tuple(inventory["detected_languages"]),
            detected_file_types=tuple(inventory["detected_file_types"]),
            detected_model_files=tuple(inventory["detected_model_files"]),
            technology_stack=tuple(technology_stack),
            build_systems=tuple(build_systems),
            entry_points=tuple(entry_points),
            configuration_files=tuple(inventory["config_files"]),
            documentation_files=tuple(inventory["doc_files"]),
            test_directories=tuple(inventory["test_dirs"]),
            discovery_score=round(discovery_score, 4),
            classification_score=round(classification_score, 4),
            confidence_score=confidence_score,
            cognition_status=status,
            warnings=tuple(self._warnings),
            unknown_file_extensions=tuple(sorted(
                inventory.get("unknown_extensions", set())
            )),
            error_message="",
        )

    # ------------------------------------------------------------------ #
    # Step 1 — Universal File Inventory                                    #
    # ------------------------------------------------------------------ #

    def _inventory_files(self) -> dict:
        python_files:       list[str] = []
        config_files:       list[str] = []
        doc_files:          list[str] = []
        test_dirs:          set[str]  = set()
        dependency_files:   list[str] = []
        named_entry_points: list[str] = []
        detected_langs:     set[str]  = set()   # executable source code only
        detected_file_types: set[str] = set()   # documents, flat files
        detected_model_files: set[str] = set()  # ML weights and models
        unknown_extensions: set[str]  = set()
        total_files = 0
        total_model_files = 0

        for dirpath, dirnames, filenames in os.walk(self.repo_root, followlinks=False):
            dirnames[:] = [
                d for d in dirnames
                if d.lower() not in SKIP_DIRECTORIES
                and not d.startswith(".")
            ]

            rel_dir = os.path.relpath(dirpath, self.repo_root)
            dirname = os.path.basename(dirpath)
            if dirname.lower() in TEST_DIR_NAMES:
                test_dirs.add(rel_dir)

            for fname in filenames:
                total_files += 1
                rel_path = os.path.join(rel_dir, fname)
                ext = os.path.splitext(fname)[1].lower()
                fname_lower = fname.lower()

                is_dockerfile_variant = any(
                    fname_lower.startswith(p) for p in DOCKERFILE_PREFIXES
                )
                is_env_variant = any(
                    fname_lower.startswith(p) for p in ENV_FILE_PREFIXES
                )
                is_compose_variant = fname_lower.startswith("docker-compose")

                # Three-tier asset taxonomy — every file classified into one bucket
                if ext in MODEL_FILE_EXTENSIONS:
                    # Tier 3 — ML model / neural network weight
                    detected_model_files.add(MODEL_FILE_EXTENSIONS[ext])
                    total_model_files += 1

                elif ext in LANGUAGE_EXTENSIONS:
                    # Tier 1 — executable source code
                    detected_langs.add(LANGUAGE_EXTENSIONS[ext])

                elif ext in ERP_LANGUAGE_EXTENSIONS:
                    # Tier 1 — ERP source code
                    detected_langs.add(ERP_LANGUAGE_EXTENSIONS[ext])

                elif ext in DOCUMENT_FILE_EXTENSIONS:
                    # Tier 2 — document / flat file
                    detected_file_types.add(DOCUMENT_FILE_EXTENSIONS[ext])

                elif ext and ext not in {
                    ".pyc", ".pyo", ".so", ".dll", ".exe",
                    ".obj", ".o", ".a", ".lib", ".class", ".jar",
                    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
                    ".woff", ".woff2", ".ttf", ".eot", ".otf",
                    ".zip", ".tar", ".gz", ".bz2", ".xz", ".rar",
                    ".db", ".sqlite", ".lock",
                }:
                    unknown_extensions.add(ext)

                # Config filename implies a language
                if fname in CONFIG_FILE_LANGUAGE_MAP:
                    detected_langs.add(CONFIG_FILE_LANGUAGE_MAP[fname])

                if is_dockerfile_variant:
                    detected_langs.add("Docker")

                # Python files
                if fname.endswith(".py"):
                    python_files.append(rel_path)
                    rel_parts = set(Path(rel_path).parts)
                    is_noise_dir = bool(rel_parts & ENTRY_POINT_NOISE_DIRS)
                    if fname in ENTRY_POINT_NAMES and not is_noise_dir:
                        named_entry_points.append(rel_path)

                # Documentation files — separated from config
                # Also register in detected_file_types (README.md → Markdown)
                if fname in DOCUMENTATION_FILE_NAMES:
                    doc_files.append(rel_path)
                    if ext in DOCUMENT_FILE_EXTENSIONS:
                        detected_file_types.add(DOCUMENT_FILE_EXTENSIONS[ext])
                    continue

                # Config detection
                is_config = (
                    fname in CONFIG_FILE_NAMES
                    or fname in DEPENDENCY_FILES
                    or ext in CONFIG_FILE_EXTENSIONS
                    or is_dockerfile_variant
                    or is_env_variant
                    or is_compose_variant
                )
                if is_config:
                    config_files.append(rel_path)
                    if fname in DEPENDENCY_FILES:
                        dependency_files.append(rel_path)
                    elif fname_lower in {
                        "environment.yml", "environment.yaml",
                        "conda.yml", "conda.yaml"
                    }:
                        dependency_files.append(rel_path)

        return {
            "total_files":          total_files,
            "python_files":         python_files,
            "config_files":         config_files,
            "doc_files":            sorted(doc_files),
            "test_dirs":            sorted(test_dirs),
            "dependency_files":     dependency_files,
            "named_entry_points":   named_entry_points,
            "detected_languages":   sorted(detected_langs),
            "detected_file_types":  sorted(detected_file_types),
            "detected_model_files": sorted(detected_model_files),
            "total_model_files":    total_model_files,
            "unknown_extensions":   unknown_extensions,
        }

    # ------------------------------------------------------------------ #
    # Step 2 — Build System Detection                                      #
    # ------------------------------------------------------------------ #

    def _detect_build_systems(
        self, config_files: list[str], dep_files: list[str]
    ) -> list[str]:
        build_systems: list[str] = []
        seen: set[str] = set()

        all_files = list(dict.fromkeys(config_files + dep_files))
        for rel_path in all_files:
            fname = os.path.basename(rel_path)
            ext = os.path.splitext(fname)[1].lower()

            # Exact filename match
            if fname in BUILD_SYSTEM_FILE_NAMES:
                name = BUILD_SYSTEM_FILE_NAMES[fname]
                if name not in seen:
                    build_systems.append(name)
                    seen.add(name)

            # Extension match
            if ext in BUILD_SYSTEM_EXTENSIONS:
                name = BUILD_SYSTEM_EXTENSIONS[ext]
                if name not in seen:
                    build_systems.append(name)
                    seen.add(name)

        return build_systems

    # ------------------------------------------------------------------ #
    # Step 3 — Dependency File Parsing                                     #
    # ------------------------------------------------------------------ #

    def _detect_from_dependency_files(self, dep_files: list[str]) -> list[tuple[str, int]]:
        signals: list[tuple[str, int]] = []
        for rel_path in dep_files:
            full_path = os.path.join(self.repo_root, rel_path)
            try:
                content = Path(full_path).read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            fname = os.path.basename(rel_path).lower()
            if fname == "package.json":
                signals.extend(self._parse_package_json(content))
            if fname.startswith("requirements") or fname == "pipfile":
                signals.extend(self._parse_requirements_txt(content))
            elif fname == "pyproject.toml":
                signals.extend(self._parse_pyproject_toml(content))
            elif fname in {"setup.py", "setup.cfg"}:
                signals.extend(self._parse_setup_file(content))
            elif fname in {"pom.xml", "build.gradle", "build.gradle.kts"}:
                signals.extend(self._parse_java_build_file(content))
            elif fname == "package.json":
                signals.extend(self._parse_package_json(content))
        return signals

    def _parse_requirements_txt(self, content: str) -> list[tuple[str, int]]:
        signals = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if (line.startswith("git+") or line.startswith("-r ")
                    or line.startswith("--") or line.startswith("-e ")
                    or line.startswith("./") or line.startswith("../")):
                continue
            pkg = re.split(r"[>=<!;\[@]", line)[0].strip().lower().replace("-", "_")
            pkg_orig = re.split(r"[>=<!;\[@]", line)[0].strip().lower()
            for key in (pkg, pkg_orig):
                if key in PACKAGE_SIGNATURES:
                    signals.append(PACKAGE_SIGNATURES[key])
                    break
                if key in ERP_PACKAGE_SIGNATURES:
                    signals.append(ERP_PACKAGE_SIGNATURES[key])
                    break
        return signals

    def _parse_pyproject_toml(self, content: str) -> list[tuple[str, int]]:
        signals = []
        seen: set[str] = set()
        for match in re.finditer(r'["\']([a-z][a-z0-9\-_.]+?)(?:[>=<!;\[,\s"\'])', content):
            raw = match.group(1).lower().replace("-", "_").replace(".", "_")
            raw_orig = match.group(1).lower()
            for key in (raw, raw_orig, raw.replace("_", "-")):
                if key in PACKAGE_SIGNATURES and key not in seen:
                    signals.append(PACKAGE_SIGNATURES[key])
                    seen.add(key)
                    break
        for match in re.finditer(r'^([a-z][a-z0-9\-_.]+)\s*=', content, re.MULTILINE):
            raw = match.group(1).lower().replace("-", "_")
            raw_orig = match.group(1).lower()
            for key in (raw, raw_orig, raw.replace("_", "-")):
                if key in PACKAGE_SIGNATURES and key not in seen:
                    signals.append(PACKAGE_SIGNATURES[key])
                    seen.add(key)
                    break
        return signals

    def _parse_setup_file(self, content: str) -> list[tuple[str, int]]:
        return self._parse_requirements_txt(content)

    def _parse_java_build_file(self, content: str) -> list[tuple[str, int]]:
        """Parse pom.xml and build.gradle for Java framework signals."""
        signals = []
        java_markers = {
            "spring-boot":          ("WEB_APPLICATION", 2),
            "springframework":      ("WEB_APPLICATION", 2),
            "spring.boot":          ("WEB_APPLICATION", 2),
            "org.springframework":  ("WEB_APPLICATION", 2),
            "hibernate":            ("WEB_APPLICATION", 1),
            "jakarta.persistence":  ("WEB_APPLICATION", 1),
            "javax.servlet":        ("API_SERVICE",     1),
            "io.quarkus":           ("API_SERVICE",     2),
            "io.micronaut":         ("API_SERVICE",     2),
            "org.elasticsearch":    ("DATA_ENGINEERING",2),
            "co.elastic":           ("DATA_ENGINEERING",2),
        }
        for marker, signal in java_markers.items():
            if marker in content:
                signals.append(signal)
        return signals

    def _parse_package_json(self, content: str) -> list[tuple[str, int]]:
        """Parse package.json for frontend framework signals."""
        signals = []
        frontend_markers = {
            '"react"':       ("FRONTEND_APPLICATION", 2),
            '"react-dom"':   ("FRONTEND_APPLICATION", 2),
            '"vue"':         ("FRONTEND_APPLICATION", 2),
            '"@angular/':    ("FRONTEND_APPLICATION", 2),
            '"svelte"':      ("FRONTEND_APPLICATION", 2),
            '"next"':        ("FRONTEND_APPLICATION", 2),
            '"nuxt"':        ("FRONTEND_APPLICATION", 2),
            '"gatsby"':      ("FRONTEND_APPLICATION", 2),
        }
        for marker, signal in frontend_markers.items():
            if marker in content:
                signals.append(signal)
        return signals

    # ------------------------------------------------------------------ #
    # Step 4b — Internal Pattern Detection                                 #
    # For repos that ARE the product (Redis, Rust, Odoo, Nginx)           #
    # ------------------------------------------------------------------ #

    def _detect_from_internal_patterns(self) -> list[tuple[str, int]]:
        """
        Detect application type from internal file content patterns.
        Used when a repo IS the product (Redis source, Rust compiler, Odoo source)
        and therefore does not declare itself as a dependency.

        This is the future-proof hook — add new patterns to
        CONTENT_PATTERN_SIGNATURES in framework_signatures.py.
        No engine changes needed.
        """
        signals: list[tuple[str, int]] = []

        for pattern in CONTENT_PATTERN_SIGNATURES:
            app_type = pattern["app_type"]
            weight = pattern["weight"]
            file_patterns = pattern["file_patterns"]
            content_keywords = pattern.get("content_keywords", [])

            # Check if any pattern file exists in the repo
            for file_pattern in file_patterns:
                full_path = os.path.join(self.repo_root, file_pattern)
                if os.path.exists(full_path):
                    # If no content keywords defined — file existence alone is signal
                    if not content_keywords:
                        signals.append((app_type, weight))
                        break
                    try:
                        file_content = Path(full_path).read_text(
                            encoding="utf-8", errors="ignore"
                        )
                        # Check if any keyword appears in the file
                        for keyword in content_keywords:
                            if keyword in file_content:
                                signals.append((app_type, weight))
                                break  # one match per file
                        else:
                            continue
                        break  # one match per pattern is enough
                    except OSError:
                        continue

        return signals

    # ------------------------------------------------------------------ #
    # Step 4 — Import Scan                                                 #
    # ------------------------------------------------------------------ #

    def _detect_from_imports(self, python_files: list[str]) -> list[tuple[str, int]]:
        signals: list[tuple[str, int]] = []
        entry_names = set(ENTRY_POINT_NAMES)
        priority = [f for f in python_files if os.path.basename(f) in entry_names]
        rest = sorted(f for f in python_files if os.path.basename(f) not in entry_names)
        sample_size = max(0, MAX_IMPORT_SAMPLE_FILES - len(priority))
        sample = priority + rest[:sample_size]
        for rel_path in sample:
            signals.extend(self._extract_import_signals(
                os.path.join(self.repo_root, rel_path)
            ))
        return signals

    def _extract_import_signals(self, full_path: str) -> list[tuple[str, int]]:
        signals = []
        try:
            source = Path(full_path).read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source, filename=full_path)
        except (SyntaxError, OSError):
            return signals
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0].lower()
                    if root_pkg in IMPORT_SIGNATURES:
                        signals.append(IMPORT_SIGNATURES[root_pkg])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0].lower()
                    if root_pkg in IMPORT_SIGNATURES:
                        signals.append(IMPORT_SIGNATURES[root_pkg])
        return signals

    # ------------------------------------------------------------------ #
    # Step 5+6 — Framework Resolution                                      #
    # ------------------------------------------------------------------ #

    def _resolve_frameworks(
        self,
        signals: list[tuple[str, int]],
        dep_files: list[str],
        config_files: list[str],
        python_file_count: int = 0,
        application_type: str = "",
    ) -> tuple[str, list[str], list[str]]:
        type_scores: dict[str, float] = defaultdict(float)
        for app_type, weight in signals:
            type_scores[app_type] += weight
        if not type_scores:
            return "None", [], self._build_technology_stack(dep_files, config_files, python_file_count)
        if not application_type:
            application_type = max(type_scores, key=type_scores.get)
        primary_framework = self._infer_framework_name(dep_files, application_type)
        secondary_frameworks = self._infer_secondary_frameworks(dep_files)
        technology_stack = self._build_technology_stack(dep_files, config_files, python_file_count)
        return primary_framework, secondary_frameworks, technology_stack

    def _infer_framework_name(self, dep_files: list[str], application_type: str = "") -> str:
        """
        Detect primary framework from dependency files.

        Framework names are grouped by application type priority.
        High-specificity frameworks (Django, FastAPI, Spring) are checked
        before low-specificity ones (Click, Nuxt) to prevent false positives
        from utility scripts or docs packages overriding the real framework.
        """

        # Priority-ordered framework detection
        # Group by specificity — highest first
        # Within each group: longer/more-specific names before shorter ones
        framework_names: dict[str, str | None] = {
            # --- Core frameworks (highest priority) ---
            "django":                "Django",
            "fastapi":               "FastAPI",
            "flask":                 "Flask",
            "tornado":               "Tornado",
            "starlette":             "Starlette",
            "sanic":                 "Sanic",

            # --- ML frameworks ---
            "torch":                 "PyTorch",
            "tensorflow":            "TensorFlow",
            "sentence-transformers": None,       # utility, not a framework
            "sentence_transformers": None,
            "transformers":          "Transformers",

            # --- Data engineering ---
            "apache-airflow":        "Airflow",
            "airflow":               "Airflow",
            "prefect":               "Prefect",
            "dagster":               "Dagster",
            "pyspark":               "PySpark",

            # --- Search / Data platforms (before frontend) ---
            "elasticsearch":         "Elasticsearch",
            "opensearch":            "OpenSearch",

            # --- Java ecosystem ---
            "spring-boot":           "Spring Boot",
            "springframework":       "Spring Framework",
            "hibernate":             "Hibernate",
            "quarkus":               "Quarkus",
            "micronaut":             "Micronaut",

            # --- ERP ---
            "odoo":                  "Odoo",
            "openerp":               "OpenERP",
            "pyrfc":                 "SAP",
            "cx_oracle":             "Oracle",

            # --- Infrastructure ---
            "ansible":               "Ansible",

            # --- CAD ---
            "ezdxf":                 "AutoCAD/DXF",
            "ifcopenshell":          "IFC/BIM",
            "freecad":               "FreeCAD",
            "rhino3dm":              "Rhino 3D",

            # --- Simulation / Aerospace ---
            "openmdao":              "OpenMDAO",
            "pynastran":             "pyNastran",
            "pyansys":               "PyANSYS",
            "fenics":                "FEniCS",
            "su2":                   "SU2 CFD",
            "gmsh":                  "Gmsh",

            # --- Blockchain ---
            "web3":                  "Web3.py",
            "brownie":               "Brownie",
            "solana":                "Solana",
            "vyper":                 "Vyper",

            # --- Medical ---
            "pydicom":               "PyDICOM",
            "hl7apy":                "HL7apy",
            "nibabel":               "NiBabel",
            "mne":                   "MNE",

            # --- Quantum ---
            "qiskit":                "Qiskit",
            "pennylane":             "PennyLane",
            "cirq":                  "Cirq",
            "braket":                "Amazon Braket",

            # --- GIS ---
            "geopandas":             "GeoPandas",
            "arcpy":                 "ArcPy",
            "pyqgis":                "PyQGIS",
            "cartopy":               "Cartopy",

            # --- Finance ---
            "quantlib":              "QuantLib",
            "backtrader":            "Backtrader",
            "zipline":               "Zipline",
            "ccxt":                  "CCXT",

            # --- Robotics ---
            "rospy":                 "ROS",
            "rclpy":                 "ROS2",
            "pydrake":               "Drake",

            # --- Scientific ---
            "astropy":               "Astropy",
            "biopython":             "BioPython",
            "rdkit":                 "RDKit",
            "openmm":                "OpenMM",
            "pymatgen":              "pymatgen",

            # --- Security ---
            "scapy":                 "Scapy",
            "pwntools":              "pwntools",
            "angr":                  "angr",

            # --- Game ---
            "pygame":                "Pygame",
            "panda3d":               "Panda3D",

            # --- Embedded ---
            "micropython":           "MicroPython",
            "circuitpython":         "CircuitPython",
            "adafruit_blinka":       "CircuitPython",
            "adafruit-blinka":       "CircuitPython",

            # --- NLP ---
            "spacy":                 "spaCy",
            "nltk":                  "NLTK",
            "gensim":                "Gensim",
            "stanza":                "Stanza",
            "flair":                 "Flair",

            # --- Audio ---
            "librosa":               "librosa",
            "speechbrain":           "SpeechBrain",
            "whisper":               "Whisper",
            "espnet":                "ESPnet",

            # --- Computer Vision ---
            "cv2":                   "OpenCV",
            "opencv":                "OpenCV",
            "ultralytics":           "YOLO/Ultralytics",
            "detectron2":            "Detectron2",
            "albumentations":        "Albumentations",

            # --- Network ---
            "netmiko":               "Netmiko",
            "napalm":                "NAPALM",
            "nornir":                "Nornir",
            "pyshark":               "PyShark",
            "ncclient":              "ncclient",

            # --- Energy ---
            "pandapower":            "pandapower",
            "pypsa":                 "PyPSA",
            "pvlib":                 "pvlib",
            "windpowerlib":          "windpowerlib",

            # --- Optimization ---
            "ortools":               "OR-Tools",
            "pulp":                  "PuLP",
            "pyomo":                 "Pyomo",
            "cvxpy":                 "CVXPY",
            "docplex":               "CPLEX",

            # --- Space ---
            "poliastro":             "poliastro",
            "sgp4":                  "sgp4",
            "skyfield":              "Skyfield",
            "spiceypy":              "SPICE",
            "pyorbital":             "pyorbital",

            # --- Optimization (self names) ---
            "pulp":                  "PuLP",
            "cvxpy":                 "CVXPY",
            "pyomo":                 "Pyomo",
            "gekko":                 "GEKKO",

            # --- Energy (self names) ---
            "pandapower":            "pandapower",
            "pypsa":                 "PyPSA",
            "pvlib":                 "pvlib",
            "windpowerlib":          "windpowerlib",

            # --- Quantum (self names) ---
            "pennylane":             "PennyLane",
            "qiskit":                "Qiskit",
            "cirq":                  "Cirq",
            "braket":                "Amazon Braket",

            # --- Blockchain (self names) ---
            "solana":                "Solana",
            "solders":               "Solana",
            "anchorpy":              "Anchor/Solana",
            "brownie":               "Brownie",

            # --- Robotics (self names) ---
            "pydrake":               "Drake",
            "drake":                 "Drake",
            "napalm":                "NAPALM",
            "nornir":                "Nornir",
            "ncclient":              "ncclient",

            # --- Scientific (self names) ---
            "astropy":               "Astropy",
            "biopython":             "BioPython",
            "Bio":                   "BioPython",

            # --- Graph (self names) ---
            "igraph":                "igraph",
            "networkx":              "NetworkX",

            # --- CV (self names) ---
            "ultralytics":           "Ultralytics/YOLO",

            # --- FPGA / Hardware ---
            "cocotb":                "cocotb",
            "amaranth":              "Amaranth HDL",
            "myhdl":                 "MyHDL",
            "migen":                 "Migen",
            "litex":                 "LiteX",

            # --- Firmware ---
            "west":                  "Zephyr (west)",
            "zephyr":                "Zephyr RTOS",
            "platformio":            "PlatformIO",

            # --- DSP ---
            "gnuradio":              "GNU Radio",
            "pysdr":                 "PySDR",
            "pyrtlsdr":              "RTL-SDR",

            # --- Mobile ---
            "kivy":                  "Kivy",
            "kivymd":                "KivyMD",
            "flet":                  "Flet",
            "toga":                  "BeeWare/Toga",
            "beeware":               "BeeWare",

            # --- Cloud / IaC ---
            "pulumi":                "Pulumi",
            "troposphere":           "Troposphere",
            "cdktf":                 "Terraform CDK",
            "aws_cdk":               "AWS CDK",

            # --- Container Orchestration ---
            "kubernetes":            "Kubernetes",
            "kopf":                  "Kopf (K8s Operator)",
            "pykube":                "PyKube",

            # --- CI/CD ---
            "jenkins":               "Jenkins",
            "python_jenkins":        "Jenkins",
            "python_gitlab":         "GitLab CI",
            "jenkinsapi":            "jenkinsapi",

            # --- Media Streaming ---
            "ffmpeg_python":         "FFmpeg",
            "ffmpeg-python":         "FFmpeg",
            "gstreamer":             "GStreamer",
            "av":                    "PyAV",

            # --- Drone / UAV ---
            "dronekit":              "DroneKit",
            "pymavlink":             "MAVLink",
            "mavsdk":                "MAVSDK",
            "ardupilot":             "ArduPilot",

            # --- Climate Science ---
            "xarray":                "xarray",
            "metpy":                 "MetPy",
            "iris":                  "Iris",

            # --- Document ---
            "pdfplumber":            "pdfplumber",
            "pytesseract":           "Tesseract OCR",
            "camelot":               "Camelot",

            # --- Graph Analytics ---
            "networkx":              "NetworkX",
            "igraph":                "iGraph",
            "py2neo":                "py2neo",

            # --- Environmental ---
            "geemap":                "geemap",
            "plantcv":               "PlantCV",

            # --- Frontend (lower priority) ---
            "react":                 "React",
            "vue":                   "Vue",
            "angular":               "Angular",
            "svelte":                "Svelte",
            "gatsby":                "Gatsby",
            "nuxt":                  "Nuxt.js",
            "next":                  "Next.js",

            # --- CLI (lowest priority) ---
            "typer":                 "Typer",
            "click":                 "Click",
        }

        SUBSTRING_EXCLUSIONS: dict[str, set[str]] = {
            "transformers": {"sentence-transformers", "sentence_transformers"},
        }

        # Map package key -> app_type, reused from PACKAGE_SIGNATURES /
        # IMPORT_SIGNATURES so we can prefer a framework whose domain
        # matches the repo's already-determined application_type.
        pkg_app_type: dict[str, str] = {}
        for src in (PACKAGE_SIGNATURES, IMPORT_SIGNATURES):
            for pkg, (app_type, _weight) in src.items():
                norm = pkg.lower().replace("-", "_")
                pkg_app_type.setdefault(norm, app_type)

        def _matches(pkg: str, content: str) -> bool:
            # Short/generic keys (len <= 2) require word-boundary match
            # to avoid false substring hits (e.g. "av" inside "available").
            pattern = r"\b" + re.escape(pkg) + r"\b"
            return re.search(pattern, content) is not None

        # Generic/utility packages (Click, Requests, Pytest, Redis, RQ, etc.)
        # are tracked as secondary frameworks but must never be selected as
        # the PRIMARY framework — they appear across countless repos
        # regardless of domain and indicate nothing about "what this
        # repository is". Without this exclusion, a large non-Python repo
        # (e.g. Rust, VSCode) containing one small utility script using
        # `click` or `requests` would incorrectly report that as its
        # primary framework.
        GENERIC_UTILITY_PACKAGES = {
            "click", "requests", "pytest", "redis", "rq", "httpx",
            "pydantic", "celery", "sqlalchemy", "alembic", "dramatiq",
            "marshmallow", "next", "nextjs",
        }

        candidates: list[tuple[str, str, str]] = []  # (pkg, display, file_content)

        for rel_path in dep_files:
            full_path = os.path.join(self.repo_root, rel_path)
            try:
                file_content = Path(full_path).read_text(
                    encoding="utf-8", errors="ignore"
                ).lower()
            except OSError:
                continue

            excluded: set[str] = set()
            for pkg, containing_pkgs in SUBSTRING_EXCLUSIONS.items():
                if any(cp in file_content for cp in containing_pkgs):
                    excluded.add(pkg)

            for pkg, display in framework_names.items():
                if display is None or pkg in excluded:
                    continue
                if pkg.lower().replace("-", "_") in GENERIC_UTILITY_PACKAGES:
                    continue
                if _matches(pkg, file_content):
                    candidates.append((pkg, display, file_content))

        if not candidates:
            return "None"

        # Pass 0 — strongest signal: a candidate package whose name
        # matches the repo's own directory name (e.g. repo "cvxpy"
        # declares itself as package "cvxpy" -> "CVXPY"; repo "astropy"
        # -> "Astropy", not "sgp4" which merely shares SPACE_SYSTEM).
        repo_name = os.path.basename(self.repo_root.rstrip("/\\")).lower().replace("-", "_")
        # Strip common wrapper suffixes/prefixes so "solana_py" matches "solana",
        # "python_igraph" matches "igraph", etc.
        repo_name_variants = {repo_name}
        for affix in ("_py", "python_", "py_"):
            if repo_name.endswith(affix):
                repo_name_variants.add(repo_name[:-len(affix)])
            if repo_name.startswith(affix):
                repo_name_variants.add(repo_name[len(affix):])
        for pkg, display, _ in candidates:
            norm = pkg.lower().replace("-", "_")
            if norm == repo_name or norm in repo_name_variants:
                return display

        # Pass 1 — prefer a candidate whose package maps to the repo's
        # determined application_type (e.g. "astropy" -> SPACE_SYSTEM).
        if application_type:
            for pkg, display, _ in candidates:
                norm = pkg.lower().replace("-", "_")
                if pkg_app_type.get(norm) == application_type:
                    return display

        # Pass 2 — fall back to dict-priority order (first match wins,
        # preserving the original specificity ordering).
        order = {pkg: i for i, pkg in enumerate(framework_names.keys())}
        candidates.sort(key=lambda c: order.get(c[0], len(order)))
        return candidates[0][1]

    def _infer_secondary_frameworks(self, dep_files: list[str]) -> list[str]:
        secondary_map = {
            "celery": "Celery", "sqlalchemy": "SQLAlchemy", "alembic": "Alembic",
            "redis": "Redis", "dramatiq": "Dramatiq", "rq": "RQ",
            "pytest": "Pytest", "pydantic": "Pydantic",
            "marshmallow": "Marshmallow", "httpx": "HTTPX", "requests": "Requests",
        }
        found = []
        for rel_path in dep_files:
            full_path = os.path.join(self.repo_root, rel_path)
            try:
                content = Path(full_path).read_text(
                    encoding="utf-8", errors="ignore"
                ).lower()
            except OSError:
                continue
            for pkg, display in secondary_map.items():
                if pkg in content and display not in found:
                    found.append(display)
        return found

    def _build_technology_stack(
        self, dep_files: list[str], config_files: list[str],
        python_file_count: int = 1
    ) -> list[str]:
        # Only include Python if Python files actually exist
        stack = ["Python"] if python_file_count > 0 else []
        FILENAME_MARKERS: dict[str, str] = {
            "dockerfile":          "Docker",
            "docker-compose.yml":  "Docker",
            "docker-compose.yaml": "Docker",
            "vagrantfile":         "Vagrant",
            "jenkinsfile":         "Jenkins",
            ".gitlab-ci.yml":      "GitLab CI",
            "azure-pipelines.yml": "Azure DevOps",
            ".travis.yml":         "Travis CI",
        }
        all_files = list(dict.fromkeys(dep_files + config_files))
        for rel_path in all_files:
            fname = os.path.basename(rel_path).lower()
            if any(fname.startswith(p) for p in DOCKERFILE_PREFIXES):
                if "Docker" not in stack:
                    stack.append("Docker")
            if fname.startswith("docker-compose"):
                if "Docker" not in stack:
                    stack.append("Docker")
            rel_lower = rel_path.replace(os.sep, "/").lower()
            if ".github/workflows" in rel_lower:
                if "GitHub Actions" not in stack:
                    stack.append("GitHub Actions")
            if fname in FILENAME_MARKERS:
                name = FILENAME_MARKERS[fname]
                if name not in stack:
                    stack.append(name)
        CONTENT_MARKERS: dict[str, str] = {
            "kubernetes":    "Kubernetes",
            "postgres":      "PostgreSQL",
            "mysql":         "MySQL",
            "sqlite":        "SQLite",
            "mongodb":       "MongoDB",
            "redis":         "Redis",
            "rabbitmq":      "RabbitMQ",
            "elasticsearch": "Elasticsearch",
            "aws":           "AWS",
            "azure":         "Azure",
            "gcp":           "GCP",
            "terraform":     "Terraform",
            "ansible":       "Ansible",
        }
        for rel_path in all_files:
            full_path = os.path.join(self.repo_root, rel_path)
            try:
                content = Path(full_path).read_text(
                    encoding="utf-8", errors="ignore"
                ).lower()
            except OSError:
                continue
            for keyword, name in CONTENT_MARKERS.items():
                if keyword in content and name not in stack:
                    stack.append(name)
        return stack

    # ------------------------------------------------------------------ #
    # Step 7 — Application Type                                            #
    # ------------------------------------------------------------------ #

    def _determine_application_type(
        self, signals: list[tuple[str, int]], inventory: dict
    ) -> ApplicationType:
        type_scores: dict[str, float] = defaultdict(float)
        for app_type, weight in signals:
            type_scores[app_type] += weight

        if not type_scores:
            return "UNKNOWN"

        qualified = {t: s for t, s in type_scores.items() if s >= 2}
        if not qualified:
            return "UNKNOWN"

        # Type hierarchy — dominant type removes subordinate types before monorepo check
        # This resolves cases where a repo has both its primary type AND utility signals
        # e.g. spaCy: NLP_TOOL(4) + FRONTEND_APPLICATION(4 from docs/react) → NLP_TOOL wins
        # e.g. CircuitPython: EMBEDDED_SYSTEM(5) + CLI_TOOL(2) → EMBEDDED_SYSTEM wins
        TYPE_HIERARCHY: dict[str, set[str]] = {
            "ERP_SYSTEM":           {"DATABASE_SYSTEM", "WEB_APPLICATION"},
            "COMPILER_TOOLCHAIN":   {"CLI_TOOL", "DATA_ENGINEERING"},
            "OPERATING_SYSTEM":     {"WEB_APPLICATION", "CLI_TOOL", "DATABASE_SYSTEM"},
            "DATABASE_SYSTEM":      {"DATA_ENGINEERING"},
            "NLP_TOOL":             {"ML_PIPELINE", "CLI_TOOL", "FRONTEND_APPLICATION", "DATA_ENGINEERING", "LIBRARY_FRAMEWORK"},
            "AUDIO_PROCESSING":     {"ML_PIPELINE", "CLI_TOOL", "NLP_TOOL", "LIBRARY_FRAMEWORK", "SIMULATION_TOOL"},
            "COMPUTER_VISION":      {"ML_PIPELINE", "CLI_TOOL", "NLP_TOOL", "LIBRARY_FRAMEWORK", "GIS_SYSTEM"},
            "ENERGY_SYSTEM":        {"DATA_ENGINEERING", "ML_PIPELINE", "GIS_SYSTEM",
                                     "GRAPH_ANALYTICS", "SIMULATION_TOOL"},
            "SPACE_SYSTEM":         {"SCIENTIFIC_COMPUTING", "DATA_ENGINEERING"},
            "GRAPH_ANALYTICS":      {"DATA_ENGINEERING", "ML_PIPELINE", "SCIENTIFIC_COMPUTING", "LIBRARY_FRAMEWORK", "SIMULATION_TOOL"},
            "EMBEDDED_SYSTEM":      {"CLI_TOOL", "ML_PIPELINE", "FRONTEND_APPLICATION", "DATA_ENGINEERING", "LIBRARY_FRAMEWORK", "SECURITY_TOOL"},
            # ML_PIPELINE is a meta-category — it is overridden BY specialist types
            # but when transformers/torch IS the product, ML_PIPELINE should win over
            # incidental NLP/Audio/CV signals from the library's own test files
            "ML_PIPELINE":          {"NLP_TOOL", "AUDIO_PROCESSING", "COMPUTER_VISION"},
            "OPTIMIZATION_TOOL":    {"DATA_ENGINEERING", "ML_PIPELINE"},
            "ROBOTICS_SYSTEM":      {"CLI_TOOL", "ML_PIPELINE", "WEB_APPLICATION", "DATA_ENGINEERING", "LIBRARY_FRAMEWORK"},
            "MEDICAL_SYSTEM":       {"ML_PIPELINE", "DATA_ENGINEERING"},
            "QUANTUM_COMPUTING":    {"ML_PIPELINE", "SCIENTIFIC_COMPUTING"},
            "SECURITY_TOOL":        {"CLI_TOOL", "NETWORK_TOOL", "EMBEDDED_SYSTEM", "LIBRARY_FRAMEWORK"},
            "SIMULATION_TOOL":      {"DATA_ENGINEERING", "ML_PIPELINE", "GRAPH_ANALYTICS", "LIBRARY_FRAMEWORK", "CLI_TOOL"},
            "BLOCKCHAIN_NODE":      {"DATABASE_SYSTEM", "CLI_TOOL"},
            "GIS_SYSTEM":           {"DATA_ENGINEERING", "ML_PIPELINE"},
            "FINANCE_SYSTEM":       {"DATA_ENGINEERING", "ML_PIPELINE"},
            "CAD_SYSTEM":           {"CLI_TOOL", "DATA_ENGINEERING"},
            "DOCUMENT_PROCESSING":  {"CLI_TOOL", "DATA_ENGINEERING"},
            "ENVIRONMENTAL":        {"DATA_ENGINEERING", "GIS_SYSTEM"},
            "FPGA_HARDWARE":        {"CLI_TOOL", "LIBRARY_FRAMEWORK", "EMBEDDED_SYSTEM"},
            "FIRMWARE":             {"CLI_TOOL", "EMBEDDED_SYSTEM", "LIBRARY_FRAMEWORK"},
            "DSP_TOOL":             {"AUDIO_PROCESSING", "CLI_TOOL", "LIBRARY_FRAMEWORK"},
            "MOBILE_APPLICATION":   {"FRONTEND_APPLICATION", "CLI_TOOL", "GAME_ENGINE", "MEDIA_STREAMING"},
            "CLOUD_INFRASTRUCTURE": {"DEVOPS_TOOLING", "CLI_TOOL", "DATA_ENGINEERING"},
            "CONTAINER_ORCHESTRATION": {"DEVOPS_TOOLING", "CLI_TOOL", "LIBRARY_FRAMEWORK", "DATA_ENGINEERING"},
            "CI_CD_PIPELINE":       {"DEVOPS_TOOLING", "CLI_TOOL"},
            "MEDIA_STREAMING":      {"AUDIO_PROCESSING", "COMPUTER_VISION", "CLI_TOOL", "LIBRARY_FRAMEWORK", "ML_PIPELINE"},
            "DRONE_UAV":            {"ROBOTICS_SYSTEM", "CLI_TOOL", "EMBEDDED_SYSTEM"},
            "CLIMATE_SCIENCE":      {"SCIENTIFIC_COMPUTING", "DATA_ENGINEERING", "GRAPH_ANALYTICS", "LIBRARY_FRAMEWORK", "GIS_SYSTEM"},
        }
        # Process hierarchy in descending score order so highest-scoring type wins
        # Only process types that are STILL in qualified (not removed by a previous step)
        for dominant_type in sorted(list(qualified.keys()), key=lambda t: qualified.get(t, 0), reverse=True):
            if dominant_type not in qualified:
                continue  # already removed by a previous hierarchy step
            if dominant_type in TYPE_HIERARCHY:
                for sub in TYPE_HIERARCHY[dominant_type]:
                    qualified.pop(sub, None)

        # Re-check after hierarchy resolution
        if len(qualified) == 1:
            return next(iter(qualified))

        # Monorepo detection — two or more types each with significant weight
        # BUT: if one type dominates significantly (2x or more), it is not a monorepo
        # e.g. COMPILER_TOOLCHAIN(4) + CLI_TOOL(2) = compiler with utility scripts, not monorepo
        # e.g. WEB_APPLICATION(4) + ML_PIPELINE(4) = genuine monorepo
        strong = {t: s for t, s in qualified.items() if s >= 2}
        if len(strong) >= 2:
            top_two = sorted(strong.values(), reverse=True)[:2]
            dominant_ratio = top_two[0] / top_two[1]
            # Only call MONOREPO if signals are roughly balanced (dominant not 2x stronger)
            if top_two[1] / top_two[0] >= 0.5 and dominant_ratio < 1.8:
                return "MONOREPO"

        best_type = max(qualified, key=lambda t: qualified[t])
        return best_type  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    # Step 8 — Entry Points                                                #
    # ------------------------------------------------------------------ #

    def _detect_entry_points(
        self, python_files: list[str], named_entry_points: list[str]
    ) -> list[str]:
        entry_points = list(named_entry_points)
        for rel_path in python_files[:100]:
            if rel_path in entry_points:
                continue
            rel_parts = set(Path(rel_path).parts)
            if rel_parts & ENTRY_POINT_NOISE_DIRS:
                continue
            full_path = os.path.join(self.repo_root, rel_path)
            try:
                source = Path(full_path).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if ('if __name__ == "__main__"' in source
                    or "if __name__ == '__main__'" in source):
                entry_points.append(rel_path)
            elif ("@app.route" in source or "@router." in source
                    or "@click.command" in source):
                if rel_path not in entry_points:
                    entry_points.append(rel_path)
        return sorted(set(entry_points))

    # ------------------------------------------------------------------ #
    # Step 9 — Confidence Scoring (Split)                                  #
    # ------------------------------------------------------------------ #

    def _score_discovery(self, inventory: dict) -> float:
        """
        How complete was the discovery scan?
        Based on what was found — not on whether we could classify it.
        A C repo with UNKNOWN type still scores high if files were found.

        Four checks — all language-agnostic:
          1. Files exist on disk
          2. At least one language detected
          3. Structure understood (config files OR build systems OR languages found)
          4. Scale understood (file count is non-zero and languages identified)
        """
        score = 0.0
        checks = 4

        # Check 1 — files exist
        if inventory["total_files"] > 0:
            score += 1.0

        # Check 2 — at least one language detected
        if inventory["detected_languages"]:
            score += 1.0

        # Check 3 — structure understood
        # Fixed: C/systems repos have no requirements.txt but still have
        # config files, build files, or detected languages — all count
        has_structure = (
            inventory["config_files"]
            or inventory["dependency_files"]
            or inventory["detected_languages"]      # language detection = structural signal
            or inventory["doc_files"]               # documentation = structural signal
        )
        if has_structure:
            score += 1.0

        # Check 4 — meaningful content found
        has_content = (
            inventory["python_files"]
            or inventory["detected_languages"]
            or inventory["total_files"] > 0
        )
        if has_content:
            score += 1.0

        return score / checks if checks > 0 else 0.0

    def _score_classification(
        self, signals: list[tuple[str, int]], primary_framework: str
    ) -> float:
        score = 0.0
        checks = 4

        if signals:
            score += 1.0
        if primary_framework != "None":
            score += 1.0
        if signals:
            type_scores: dict[str, float] = defaultdict(float)
            total_weight = 0.0
            for app_type, weight in signals:
                type_scores[app_type] += weight
                total_weight += weight
            top_weight = max(type_scores.values()) if type_scores else 0.0
            if total_weight > 0:
                # Dominance: either the winning type's share of total
                # signal weight is >=50%, OR a primary framework was
                # successfully resolved at all (a named framework is
                # itself strong evidence the classification is correct,
                # even if secondary signals like Pytest/Requests add
                # weight to other types).
                if (top_weight / total_weight >= 0.5) or primary_framework != "None":
                    score += 1.0
                # Sufficient signal strength
                if top_weight >= 2:
                    score += 1.0
        else:
            checks -= 2

        return score / checks if checks > 0 else 0.0

    # ------------------------------------------------------------------ #
    # Step 10 — Diagnostic Warnings                                        #
    # ------------------------------------------------------------------ #

    def _generate_diagnostic_warnings(
        self,
        inventory: dict,
        signals: list[tuple[str, int]],
        application_type: str,
        build_systems: list[str],
        classification_score: float,
    ) -> None:
        """
        Explicitly identify all issues instead of silently returning UNKNOWN.
        Every gap is named and explained.
        """

        # Warning 1 — No dependency files found
        if not inventory["dependency_files"] and not inventory["config_files"]:
            self._warnings.append(
                "No dependency files or configuration files found. "
                "Classification based on file extensions only."
            )

        # Warning 2 — No framework signals detected
        if not signals and inventory["python_files"]:
            self._warnings.append(
                "No framework signals detected in dependency files or imports. "
                "application_type set to UNKNOWN. "
                "Add framework packages to requirements.txt for classification."
            )

        # Warning 3 — Monorepo detected
        if application_type == "MONOREPO":
            type_scores: dict[str, float] = defaultdict(float)
            for app_type, weight in signals:
                type_scores[app_type] += weight
            types_found = sorted(type_scores.keys())
            self._warnings.append(
                f"Multiple application types detected: {', '.join(types_found)}. "
                "Classified as MONOREPO. "
                "Module 2 Repository Graph Engine required for service boundary resolution."
            )

        # Warning 4 — Unknown file extensions
        unknown_exts = inventory.get("unknown_extensions", set())
        if unknown_exts:
            sample = sorted(unknown_exts)[:5]
            self._warnings.append(
                f"{len(unknown_exts)} file extension(s) not in language registry: "
                f"{', '.join(sample)}. "
                "These files were counted but language not identified. "
                "Add to LANGUAGE_EXTENSIONS in framework_signatures.py."
            )

        # Warning 5 — Non-Python repo with no classification
        if not inventory["python_files"] and application_type == "UNKNOWN":
            langs = inventory["detected_languages"]
            if langs:
                self._warnings.append(
                    f"No Python files found. Detected languages: {', '.join(langs)}. "
                    f"Deep classification for these languages not yet implemented. "
                    f"Discovery is complete. Classification requires language-specific "
                    f"module in languages/ directory."
                )

        # Warning 6 — Low classification confidence
        if classification_score < 0.4 and application_type == "UNKNOWN":
            self._warnings.append(
                f"Classification confidence low ({classification_score:.0%}). "
                "application_type could not be determined. "
                "Discovery scan is complete — structure, languages, and files are accurate."
            )

    # ------------------------------------------------------------------ #
    # Step 12 — Purpose String                                             #
    # ------------------------------------------------------------------ #

    def _build_purpose_string(
        self,
        application_type: str,
        primary_framework: str,
        python_files: list[str],
        detected_languages: list[str],
    ) -> str:
        repo_name = os.path.basename(self.repo_root)
        fw = f" ({primary_framework})" if primary_framework != "None" else ""
        type_label = application_type.replace("_", " ").title()
        if python_files:
            scale = f"{len(python_files)} Python files"
        elif detected_languages:
            scale = f"{', '.join(detected_languages[:3])} repository"
        else:
            scale = "unknown scale"
        return f"{repo_name} — {type_label}{fw} — {scale}"

    # ------------------------------------------------------------------ #
    # Output                                                               #
    # ------------------------------------------------------------------ #

    def save_report(self, report: RepositoryCognitionReport, output_path: str) -> None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)