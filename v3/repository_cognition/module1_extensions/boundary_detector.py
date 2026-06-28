"""
========================================================================
boundary_detector.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITY:
    Repository Boundary Detection

Fixes TC_M1_001 gap: boundary detection was implicit (no crash =
boundary respected). Now produces a discrete, reported field.

DETECTS:
    - Whether the path is a valid, accessible repository root
    - Whether it is a monorepo (multiple sub-projects)
    - Sub-project boundaries within a monorepo
    - Whether scan scope is complete or partial

TRUTH BOUNDARY:
    Returns boundary_detected = False if root is inaccessible.
    Reports partial = True if scan was interrupted.
========================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path


# Markers that indicate a sub-project root
_SUBPROJECT_MARKERS = {
    # Standard Python package markers
    "setup.py", "pyproject.toml", "package.json",
    "go.mod", "Cargo.toml", "pom.xml", "build.gradle",
    "CMakeLists.txt",
    # ERP / Odoo style module markers
    "__manifest__.py", "__openerp__.py",
    # Plugin / addon registries
    "plugin.json", "addon.xml", "module.json",
}


@dataclass
class BoundaryDetectionResult:
    boundary_detected:  bool
    root_path:          str
    is_monorepo:        bool
    sub_projects:       list[str]   # relative paths of detected sub-roots
    total_files:        int
    total_dirs:         int
    scan_complete:      bool
    notes:              list[str]


class BoundaryDetector:
    """
    Detects the repository boundary and identifies sub-project structure.
    Scans folder names and marker files only — does not read file contents.
    """

    MAX_DEPTH = 5   # increased from 4 — ERP module markers are often at depth 3-4
    MONOREPO_THRESHOLD = 3  # minimum sub-projects to call it a monorepo

    def detect(self, repo_path: str) -> BoundaryDetectionResult:
        root = Path(repo_path)
        notes: list[str] = []

        if not root.exists():
            return BoundaryDetectionResult(
                boundary_detected=False,
                root_path=str(repo_path),
                is_monorepo=False,
                sub_projects=[],
                total_files=0,
                total_dirs=0,
                scan_complete=False,
                notes=["Root path does not exist"],
            )

        if not root.is_dir():
            return BoundaryDetectionResult(
                boundary_detected=False,
                root_path=str(repo_path),
                is_monorepo=False,
                sub_projects=[],
                total_files=0,
                total_dirs=0,
                scan_complete=False,
                notes=["Path is not a directory"],
            )

        total_files = 0
        total_dirs  = 0
        sub_roots: list[str] = []
        scan_complete = True

        try:
            for item in root.rglob("*"):
                depth = len(item.relative_to(root).parts)
                if item.is_file():
                    total_files += 1
                    # Check for sub-project marker at depth 2+
                    if depth >= 2 and depth <= self.MAX_DEPTH:
                        if item.name in _SUBPROJECT_MARKERS:
                            sub_root = str(item.parent.relative_to(root))
                            if sub_root not in sub_roots:
                                sub_roots.append(sub_root)
                elif item.is_dir():
                    total_dirs += 1
        except PermissionError as e:
            scan_complete = False
            notes.append(f"Permission error during scan: {e}")
        except Exception as e:
            scan_complete = False
            notes.append(f"Scan interrupted: {e}")

        is_monorepo = len(sub_roots) >= self.MONOREPO_THRESHOLD
        if is_monorepo:
            notes.append(f"Monorepo detected: {len(sub_roots)} sub-projects found")

        return BoundaryDetectionResult(
            boundary_detected=True,
            root_path=str(root.resolve()),
            is_monorepo=is_monorepo,
            sub_projects=sub_roots,
            total_files=total_files,
            total_dirs=total_dirs,
            scan_complete=scan_complete,
            notes=notes,
        )