"""
========================================================================
constraint_discovery.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITIES:
    - Business Constraints
    - Technical Constraints
    - Compliance Constraints
    - Safety Constraints

Answers: "What can never change in this repository?"

TRUTH BOUNDARY:
    Every constraint is INFERRED from code evidence — not extracted
    from documents (that requires V3-108).
    Confidence reflects evidence strength, not business verification.
========================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import re


_CONSTRAINT_PATTERNS: list[tuple[str, str, str, str]] = [
    # (regex, constraint_type, category, confidence)

    # Business
    (r"(?:must|shall|required|mandatory|obligatory)\s+\w+",
     "Mandatory condition",        "BUSINESS",    "MEDIUM"),
    (r"raise\s+\w*(?:Forbidden|Unauthorized|NotAllowed)\(",
     "Access constraint",          "BUSINESS",    "HIGH"),
    (r"only\s+(?:one|single|unique)\s+\w+",
     "Uniqueness constraint",      "BUSINESS",    "MEDIUM"),

    # Technical
    (r"MAX_\w+\s*=\s*\d+",
     "Maximum limit",              "TECHNICAL",   "HIGH"),
    (r"MIN_\w+\s*=\s*\d+",
     "Minimum limit",              "TECHNICAL",   "HIGH"),
    (r"@deprecated|TODO.*remove|FIXME.*legacy",
     "Deprecated constraint",      "TECHNICAL",   "LOW"),

    # Compliance
    (r"(?:gdpr|hipaa|pci|sox|vat|ifrs|gaap|iso\s*\d+)",
     "Regulatory reference",       "COMPLIANCE",  "HIGH"),
    (r"audit(?:_log|_trail|_record)",
     "Audit requirement",          "COMPLIANCE",  "HIGH"),
    (r"(?:encrypt|hash|sign)\s*\(",
     "Encryption requirement",     "COMPLIANCE",  "MEDIUM"),

    # Safety
    (r"emergency|failsafe|fail_safe|shutdown|kill_switch",
     "Safety mechanism",           "SAFETY",      "HIGH"),
    (r"assert\s+\w+\s+is\s+not\s+None",
     "Null-safety constraint",     "SAFETY",      "LOW"),
    (r"timeout\s*=\s*\d+",
     "Timeout constraint",         "SAFETY",      "LOW"),
]


@dataclass
class Constraint:
    constraint_type:  str
    category:         str    # BUSINESS | TECHNICAL | COMPLIANCE | SAFETY
    confidence:       str
    source_file:      str
    source_line:      int
    raw_match:        str


@dataclass
class ConstraintDiscoveryResult:
    constraints:       list[Constraint]
    by_category:       dict[str, list[Constraint]]
    total_found:       int
    files_scanned:     int
    notes:             list[str]


class ConstraintDiscovery:

    MAX_FILES = 200

    def discover(self, repo_path: str) -> ConstraintDiscoveryResult:
        root = Path(repo_path)
        constraints: list[Constraint] = []
        files_scanned = 0
        notes: list[str] = []

        if not root.exists():
            return ConstraintDiscoveryResult(
                constraints=[], by_category={}, total_found=0,
                files_scanned=0, notes=["Repository path does not exist"],
            )

        py_files = list(root.rglob("*.py"))[:self.MAX_FILES]

        MAX_PER_FILE = 8   # cap per file — prevents noise from large constant/config files

        for py_file in py_files:
            files_scanned += 1
            try:
                lines = py_file.read_text(
                    encoding="utf-8", errors="ignore"
                ).splitlines()
            except Exception:
                continue

            rel = str(py_file.relative_to(root))
            file_match_count = 0

            for line_no, line in enumerate(lines, start=1):
                if file_match_count >= MAX_PER_FILE:
                    break
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                for pattern, ctype, category, confidence in _CONSTRAINT_PATTERNS:
                    m = re.search(pattern, stripped, re.IGNORECASE)
                    if m:
                        file_match_count += 1
                        constraints.append(Constraint(
                            constraint_type=ctype,
                            category=category,
                            confidence=confidence,
                            source_file=rel,
                            source_line=line_no,
                            raw_match=m.group(0)[:100],
                        ))

        by_category: dict[str, list[Constraint]] = {
            "BUSINESS": [], "TECHNICAL": [], "COMPLIANCE": [], "SAFETY": []
        }
        for c in constraints:
            by_category.setdefault(c.category, []).append(c)

        notes.append(
            "Constraints are INFERRED from code patterns. "
            "Verify with domain experts and policy documents."
        )

        return ConstraintDiscoveryResult(
            constraints=constraints,
            by_category=by_category,
            total_found=len(constraints),
            files_scanned=files_scanned,
            notes=notes,
        )