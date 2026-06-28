"""
========================================================================
signal_analyzer.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITIES:
    - Package Signals   (requirements.txt, pyproject.toml, package.json)
    - Import Signals    (top-level import names from .py files, sampled)
    - Content Signals   (keywords from filenames and folder names)

Used by classification_reason.py to build evidence for why a
particular domain was detected.

TRUTH BOUNDARY:
    Signals are evidence — not conclusions.
    A signal score of 0 means "no evidence found", not "wrong domain".
========================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import re


# ---------------------------------------------------------------------------
# Domain keyword maps
# ---------------------------------------------------------------------------

_PACKAGE_SIGNALS: dict[str, list[str]] = {
    "Finance":          ["pandas", "sqlalchemy", "ccxt", "plaid", "stripe",
                         "quickbooks", "sagemaker-groundtruth"],
    "ML":               ["torch", "tensorflow", "sklearn", "transformers",
                         "keras", "xgboost", "lightgbm", "onnx"],
    "ComputerVision":   ["opencv-python", "ultralytics", "pillow",
                         "albumentations", "torchvision"],
    "NLP":              ["transformers", "spacy", "nltk", "gensim",
                         "sentence-transformers"],
    "Robotics":         ["rclpy", "rospy", "ros2", "pyserial", "robotframework", "ament", "colcon"],
    "Scientific":       ["scipy", "numpy", "matplotlib", "sympy",
                         "astropy", "metpy"],
    "Medical":          ["pydicom", "nibabel", "SimpleITK", "hl7",
                         "fhir.resources"],
    "Web":              ["flask", "django", "fastapi", "starlette",
                         "tornado", "aiohttp"],
    "Data":             ["pyspark", "airflow", "dbt", "great-expectations",
                         "prefect"],
    "DevOps":           ["ansible", "paramiko", "fabric", "boto3",
                         "azure-sdk"],
}

_CONTENT_SIGNALS: dict[str, list[str]] = {
    "Finance":   ["invoice", "payment", "vendor", "billing", "accounting",
                  "finance", "tax", "vat", "ledger", "budget", "payroll",
                  "erp", "crm", "trading", "exchange"],
    "Medical":   ["patient", "diagnosis", "prescription", "clinical",
                  "medical", "drug", "health", "dicom", "radiology"],
    "Aerospace": ["flight", "sensor", "navigation", "autopilot",
                  "aerospace", "avionics", "telemetry", "mission"],
    "ML":        ["model", "train", "dataset", "inference", "embedding",
                  "features", "loss", "optimizer"],
    "Robotics":  ["robot", "actuator", "servo", "ros", "kinematics",
                  "lidar", "slam"],
    "Energy":    ["scada", "plc", "sensor", "alarm", "shutdown",
                  "pressure", "valve", "pipeline"],
    "Web":       ["route", "view", "template", "middleware", "request",
                  "response", "session", "auth"],
}


@dataclass
class SignalResult:
    package_signals:    dict[str, list[str]]   # domain -> matched packages
    import_signals:     dict[str, list[str]]   # domain -> matched imports
    content_signals:    dict[str, list[str]]   # domain -> matched keywords
    domain_scores:      dict[str, int]         # domain -> total signal count
    top_domain:         str                    # highest scoring domain
    top_score:          int


class SignalAnalyzer:
    """
    Collects package, import, and content signals without reading
    full file contents — uses filenames, folder names, and the first
    10 lines of requirements.txt / package.json for package signals.
    """

    IMPORT_SAMPLE_LINES = 30   # read only first N lines per .py file
    MAX_PY_FILES        = 50   # sample at most N .py files for imports

    def analyze(self, repo_path: str) -> SignalResult:
        root = Path(repo_path)

        pkg_hits:     dict[str, list[str]] = {d: [] for d in _PACKAGE_SIGNALS}
        import_hits:  dict[str, list[str]] = {d: [] for d in _PACKAGE_SIGNALS}
        content_hits: dict[str, list[str]] = {d: [] for d in _CONTENT_SIGNALS}

        # -- Package signals ------------------------------------------------
        pkg_file = self._find_package_file(root)
        if pkg_file:
            raw = pkg_file.read_text(encoding="utf-8", errors="ignore").lower()
            for domain, pkgs in _PACKAGE_SIGNALS.items():
                for pkg in pkgs:
                    if pkg.lower() in raw:
                        pkg_hits[domain].append(pkg)

        # -- Import signals (sampled) ---------------------------------------
        py_files = list(root.rglob("*.py"))[:self.MAX_PY_FILES]
        for py in py_files:
            try:
                lines = py.read_text(
                    encoding="utf-8", errors="ignore"
                ).splitlines()[:self.IMPORT_SAMPLE_LINES]
                for line in lines:
                    for domain, pkgs in _PACKAGE_SIGNALS.items():
                        for pkg in pkgs:
                            if re.search(
                                r"\b" + re.escape(pkg.replace("-", "_")) + r"\b",
                                line.lower()
                            ):
                                if pkg not in import_hits[domain]:
                                    import_hits[domain].append(pkg)
            except Exception:
                continue

        # -- Content signals (filenames + folder names) ----------------------
        try:
            all_names = [
                p.name.lower()
                for p in root.rglob("*")
                if len(p.relative_to(root).parts) <= 4
            ]
        except Exception:
            all_names = []

        combined = " ".join(all_names)
        for domain, keywords in _CONTENT_SIGNALS.items():
            for kw in keywords:
                if kw in combined:
                    content_hits[domain].append(kw)

        # -- Aggregate scores -----------------------------------------------
        all_domains = set(list(_PACKAGE_SIGNALS.keys()) +
                          list(_CONTENT_SIGNALS.keys()))
        scores: dict[str, int] = {}
        for d in all_domains:
            scores[d] = (
                len(pkg_hits.get(d, []))
                + len(import_hits.get(d, []))
                + len(content_hits.get(d, []))
            )

        # Core Business Domains that should be preferred over infrastructure on a tie
        CORE_PREFERENCE = {
            "Finance", "Medical", "Aerospace", "Robotics", "Energy",
            "Manufacturing", "Scientific", "FPGA", "Defense", "Automotive",
            "Telecom", "SAP",
        }

        top_domain = "UNKNOWN"
        top_score  = 0

        # First pass: find highest score
        for d, s in scores.items():
            if s > top_score:
                top_score  = s
                top_domain = d

        # Tie-break: if multiple domains share the top score, prefer Core Business Domain
        if top_score > 0:
            tied = [d for d, s in scores.items() if s == top_score]
            if len(tied) > 1:
                core_tied = [d for d in tied if d in CORE_PREFERENCE]
                if core_tied:
                    top_domain = core_tied[0]  # prefer core domain over infrastructure

        if top_score == 0:
            top_domain = "UNKNOWN"

        return SignalResult(
            package_signals=pkg_hits,
            import_signals=import_hits,
            content_signals=content_hits,
            domain_scores=scores,
            top_domain=top_domain,
            top_score=top_score,
        )

    # -----------------------------------------------------------------------

    def _find_package_file(self, root: Path) -> "Path | None":
        for name in ["requirements.txt", "pyproject.toml",
                     "setup.py", "package.json", "Cargo.toml", "go.mod"]:
            p = root / name
            if p.exists():
                return p
        return None