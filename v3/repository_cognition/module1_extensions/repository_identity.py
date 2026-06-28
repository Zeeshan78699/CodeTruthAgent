"""
========================================================================
repository_identity.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITIES:
    - Repository Identity Classification
    - Domain Classification

Derives a clean identity record from the existing CognitionReport.
No re-scanning — reads the already-produced report fields only.

TRUTH BOUNDARY:
    If application_type is absent or empty, identity = UNKNOWN.
    No guessing. No fabricated labels.
========================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Domain normalisation map
# application_type strings → human-readable domain labels
# ---------------------------------------------------------------------------

_DOMAIN_MAP: dict[str, str] = {
    "FINANCE_SYSTEM":        "Finance",
    "ERP_SYSTEM":            "ERP",
    "MEDICAL_SYSTEM":        "Medical",
    "AEROSPACE_SYSTEM":      "Aerospace",
    "AI_ML_SYSTEM":          "AI/ML",
    "ML_SYSTEM":             "Machine Learning",
    "NLP_SYSTEM":            "NLP",
    "COMPUTER_VISION_SYSTEM":"Computer Vision",
    "ROBOTICS_SYSTEM":       "Robotics",
    "ENERGY_SYSTEM":         "Energy",
    "MANUFACTURING_SYSTEM":  "Manufacturing",
    "SAP_SYSTEM":            "SAP",
    "TELECOM_SYSTEM":        "Telecom",
    "AUTOMOTIVE_SYSTEM":     "Automotive",
    "DEFENSE_SYSTEM":        "Defense",
    "SCIENTIFIC_SYSTEM":     "Scientific Computing",
    "WEB_APPLICATION":       "Web",
    "API_SERVICE":           "API",
    "CLI_TOOL":              "CLI",
    "DATA_PIPELINE":         "Data Engineering",
    "DEVOPS_SYSTEM":         "DevOps",
    "SECURITY_SYSTEM":       "Security",
}




# ---------------------------------------------------------------------------
# Framework priority — utility libraries yield to primary frameworks
# ---------------------------------------------------------------------------

FRAMEWORK_PRIORITY: list[str] = [
    # ML / AI
    "torch", "pytorch", "tensorflow", "keras", "jax",
    "sklearn", "scikit-learn", "xgboost", "lightgbm",
    "transformers",
    # Web
    "fastapi", "django", "flask", "starlette", "tornado", "aiohttp",
    # Domain-specific — before pandas/numpy (they use pandas internally)
    "welleng", "lasio", "welly", "striplog",
    "pynastran", "openmdao", "pyreservoir",
    "pandapower", "pypsa", "poliastro",
    "biopython", "pydicom", "obspy",
    "cantools", "qiskit", "gnuradio",
    "ccxt", "zipline", "pymodbus",
    # Scientific utilities — LOW priority (used by all domains)
    "pandas", "numpy", "scipy",
    "networkx",   # lowest priority — utility
]

LOW_PRIORITY_FRAMEWORKS: set[str] = {
    "networkx", "requests", "urllib3", "certifi",
    "six", "attrs", "typing-extensions",
}


def _find_best_framework(repo_path: str) -> "str | None":
    """Scans dependency files for highest-priority framework."""
    root = Path(repo_path)
    dep_files = [
        root / "requirements.txt",
        root / "pyproject.toml",
        root / "setup.py",
        root / "setup.cfg",
        root / "Pipfile",
    ]
    content = ""
    for dep_file in dep_files:
        if dep_file.exists():
            try:
                content += dep_file.read_text(encoding="utf-8", errors="ignore").lower()
            except Exception:
                continue

    display_map = {
        # ML
        "torch": "PyTorch", "pytorch": "PyTorch",
        "tensorflow": "TensorFlow", "keras": "Keras",
        "jax": "JAX", "sklearn": "scikit-learn",
        "scikit-learn": "scikit-learn", "xgboost": "XGBoost",
        "lightgbm": "LightGBM", "transformers": "Transformers",
        # Web
        "fastapi": "FastAPI", "django": "Django",
        "flask": "Flask",
        # Domain-specific
        "welleng": "welleng", "lasio": "lasio",
        "welly": "welly", "striplog": "striplog",
        "pynastran": "pyNastran", "openmdao": "OpenMDAO",
        "pyreservoir": "pyreservoir", "pandapower": "pandapower",
        "pypsa": "PyPSA", "poliastro": "poliastro",
        "biopython": "BioPython", "pydicom": "PyDICOM",
        "obspy": "ObsPy", "cantools": "cantools",
        "qiskit": "Qiskit", "gnuradio": "GNURadio",
        "ccxt": "CCXT", "zipline": "Zipline",
        "pymodbus": "pymodbus",
        # Scientific utilities
        "pandas": "Pandas", "numpy": "NumPy",
        "networkx": "NetworkX",
    }

    # Check repo folder name and top-level package dirs
    # e.g. pytorch repo folder = "pytorch" → return PyTorch
    try:
        root_p = Path(repo_path)
        root_name = root_p.name.lower()
        for fw in FRAMEWORK_PRIORITY:
            if fw in root_name:
                return display_map.get(fw, fw.title())
        # Check top-level package directories
        for item in root_p.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                item_name = item.name.lower().replace("-", "_")
                for fw in FRAMEWORK_PRIORITY:
                    if fw == item_name or item_name.startswith(fw):
                        return display_map.get(fw, fw.title())
    except Exception:
        pass

    for fw in FRAMEWORK_PRIORITY:
        if fw in content:
            return display_map.get(fw, fw.title())
    return None

def validate_framework(
    detected_framework: str,
    repo_path: str,
) -> "str | None":
    """
    Cross-checks the detected framework name against the repo's
    actual dependency files.

    Prevents false-positive framework detection where the framework
    name appears in code comments or scientific naming patterns
    but is not actually a project dependency.

    Returns the framework name if confirmed, None if not found.

    Example of false positive prevented:
        fluids repo → core detects 'Astropy' from scientific signals
        → Astropy not in fluids requirements.txt
        → returns None (correct: fluids has no Astropy dependency)
    """
    if not detected_framework:
        return None

    root = Path(repo_path)
    name_lower = detected_framework.lower()

    # Check dependency files
    dep_files = [
        root / "requirements.txt",
        root / "pyproject.toml",
        root / "setup.py",
        root / "setup.cfg",
        root / "Pipfile",
        root / "conda.yml",
        root / "environment.yml",
    ]

    for dep_file in dep_files:
        if dep_file.exists():
            try:
                content = dep_file.read_text(
                    encoding="utf-8", errors="ignore"
                ).lower()
                if name_lower in content:
                    return detected_framework
            except Exception:
                continue

    # Also check if framework name appears in the package source itself
    # (e.g. the package IS the framework)
    try:
        for item in root.iterdir():
            if item.is_dir() and item.name.lower() == name_lower:
                return detected_framework
    except Exception:
        pass

    return None


@dataclass
class RepositoryIdentity:
    repository_name:     str
    application_type:    str
    domain:              str            # human-readable, e.g. "Finance"
    primary_framework:   str
    project_purpose:     str
    classification_source: str          # "COGNITION_ENGINE" | "HUMAN_OVERRIDE"
    confidence:          Optional[float]
    is_known:            bool           # False if UNKNOWN


@dataclass
class RepositoryIdentityClassifier:
    """
    Derives a RepositoryIdentity from an existing CognitionReport.
    Does not re-scan. Does not guess.
    """

    def classify(self, report: object, repo_path: str) -> RepositoryIdentity:
        """
        Parameters
        ----------
        report    : CognitionReport object produced by Module 1 core
        repo_path : original repository path (for name derivation)
        """
        import os

        repo_name     = os.path.basename(str(repo_path).rstrip("/\\"))
        app_type      = str(getattr(report, "application_type", "") or "")
        framework     = str(getattr(report, "primary_framework", "") or "")
        # Normalize string "None" to empty — core sometimes returns literal "None"
        if framework.lower() in ("none", "null", "n/a", "unknown"):
            framework = ""
        purpose       = str(getattr(report, "project_purpose",   "") or "")
        confidence    = getattr(report, "confidence_score", None)

        is_known = bool(app_type and app_type.upper() != "UNKNOWN")
        domain   = _DOMAIN_MAP.get(app_type.upper(), app_type) if is_known else "UNKNOWN"

        # Validate framework — prevents false positives from scientific
        # signal overlap (e.g. fluids detecting Astropy)
        # Validate framework — also upgrades low-priority utility libs
        if framework and framework.lower() in LOW_PRIORITY_FRAMEWORKS:
            # Detected framework is a utility lib — find the real one
            validated_framework = _find_best_framework(repo_path)
        else:
            validated_framework = validate_framework(framework, repo_path) if framework else None

        # Final framework — do not fall back to low-priority utility lib
        final_framework = validated_framework
        if not final_framework and framework:
            if framework.lower() not in LOW_PRIORITY_FRAMEWORKS:
                final_framework = framework

        # Last resort: repo folder name = the framework
        # e.g. lasio repo → "Lasio", welleng → "Welleng"
        if not final_framework:
            folder = Path(repo_path).name
            if folder and not folder.startswith("."):
                final_framework = folder.replace("-", " ").replace("_", " ").title()

        return RepositoryIdentity(
            repository_name=repo_name,
            application_type=app_type if is_known else "UNKNOWN",
            domain=domain,
            primary_framework=final_framework or "",
            project_purpose=purpose,
            classification_source="COGNITION_ENGINE",
            confidence=float(confidence) if confidence is not None else None,
            is_known=is_known,
        )

    def apply_human_override(
        self,
        identity: RepositoryIdentity,
        selected_domain: str,
        operator: str = "HUMAN",
    ) -> RepositoryIdentity:
        """
        Human selection = Approved Working Baseline, NOT Truth.
        Audit record marks source as HUMAN_OVERRIDE and confidence
        as UNVERIFIED so no downstream module treats this as proven.
        """
        identity.application_type      = selected_domain
        identity.domain                = _DOMAIN_MAP.get(
                                             selected_domain.upper(),
                                             selected_domain
                                         )
        identity.classification_source = f"HUMAN_OVERRIDE:{operator}"
        identity.confidence            = None   # UNVERIFIED — never fabricate
        identity.is_known              = True
        return identity