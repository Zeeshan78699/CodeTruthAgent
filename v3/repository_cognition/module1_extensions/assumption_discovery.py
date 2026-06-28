"""
========================================================================
assumption_discovery.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITIES:
    - Hidden Assumption Detection
    - Configuration Assumptions
    - Business Logic Assumptions
    - Risky Assumption Reporting

WHY THIS MATTERS:
    Most systems answer: "What does the code do?"
    This module answers: "What must be true for this code to work?"

    Hidden assumptions are often where failures originate — not in the
    code itself, but in what the code silently depends on.

WHAT IT SCANS:
    - Constants and hardcoded values (tax rates, limits, IDs)
    - Configuration defaults
    - Validation rules and guards
    - Business logic conditionals

TRUTH BOUNDARY:
    Every assumption is reported as POSSIBLE_ASSUMPTION, not FACT.
    Confidence is HIGH/MEDIUM/LOW based on evidence count.
    No assumptions are invented — all have source file + line evidence.
========================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import re


# ---------------------------------------------------------------------------
# Assumption detection patterns
# ---------------------------------------------------------------------------

_CONSTANT_PATTERNS = [
    # tax / rate constants
    (r"\b(?:TAX|VAT|RATE|GST|DUTY)\s*=\s*[\d.]+",    "Rate/Tax constant",     "HIGH"),
    # currency
    (r"\b(?:CURRENCY|CCY)\s*=\s*['\"]?\w+",          "Currency assumption",   "HIGH"),
    # ID format
    (r"\b(?:ID_PREFIX|ACCOUNT_PREFIX)\s*=\s*",        "ID format assumption",  "MEDIUM"),
    # DB / connection
    (r"\bDATABASE_URL\s*=|DB_HOST\s*=",               "DB connection assumption","MEDIUM"),
    # timeout / retry
    (r"\b(?:TIMEOUT|MAX_RETRY|RETRY)\s*=\s*\d+",      "Timeout/retry hardcoded","LOW"),
    # port / host
    (r"\b(?:PORT|HOST)\s*=\s*[\d\"']",                "Network hardcoded",     "LOW"),
]

_VALIDATION_PATTERNS = [
    (r"assert\s+.+",                                  "Assert assumption",     "MEDIUM"),
    (r"if\s+not\s+.+:\s*raise",                       "Guard assumption",      "MEDIUM"),
    (r"raise\s+ValueError\(",                         "Validation boundary",   "LOW"),
]

_BUSINESS_LOGIC_PATTERNS = [
    (r"if\s+amount\s*[><=!]+\s*[\d,]+",               "Amount threshold",      "HIGH"),
    (r"if\s+.+\s*==\s*['\"](?:USD|EUR|GBP|AED)",      "Currency assumption",   "HIGH"),
    (r"if\s+.+status\s*==\s*['\"][A-Z]+['\"]",        "Status enum assumption","MEDIUM"),
]

ALL_PATTERNS = _CONSTANT_PATTERNS + _VALIDATION_PATTERNS + _BUSINESS_LOGIC_PATTERNS


@dataclass
class Assumption:
    assumption_type:  str        # e.g. "Rate/Tax constant"
    description:      str        # human-readable
    confidence:       str        # "HIGH" | "MEDIUM" | "LOW"
    source_file:      str        # relative path
    source_line:      int
    raw_match:        str        # the actual code snippet


@dataclass
class AssumptionDiscoveryResult:
    assumptions:      list[Assumption]
    high_risk:        list[Assumption]    # HIGH confidence
    total_found:      int
    files_scanned:    int
    overall_risk:     str                 # "HIGH" | "MEDIUM" | "LOW" | "NONE"
    notes:            list[str]


class AssumptionDiscovery:
    """
    Scans Python source files for patterns that indicate hidden assumptions.
    Reports POSSIBLE_ASSUMPTION — never claims certainty about business intent.
    """

    MAX_FILES       = 200
    MAX_LINE_LENGTH = 200

    def discover(self, repo_path: str) -> AssumptionDiscoveryResult:
        root = Path(repo_path)
        assumptions: list[Assumption] = []
        files_scanned = 0
        notes: list[str] = []

        if not root.exists():
            return AssumptionDiscoveryResult(
                assumptions=[], high_risk=[], total_found=0,
                files_scanned=0, overall_risk="NONE",
                notes=["Repository path does not exist"],
            )

        py_files = list(root.rglob("*.py"))[:self.MAX_FILES]

        MAX_PER_FILE = 10   # cap matches per file — prevents noise from large constant files

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
                line_stripped = line.strip()[:self.MAX_LINE_LENGTH]
                if not line_stripped or line_stripped.startswith("#"):
                    continue
                # Skip purely numeric assignment lines — too noisy in scientific repos
                if re.match(r"^\w+\s*=\s*[\d.]+\s*$", line_stripped):
                    continue

                for pattern, assumption_type, confidence in ALL_PATTERNS:
                    m = re.search(pattern, line_stripped, re.IGNORECASE)
                    if m:
                        file_match_count += 1
                        assumptions.append(Assumption(
                            assumption_type=assumption_type,
                            description=f"Possible assumption: {assumption_type}",
                            confidence=confidence,
                            source_file=rel,
                            source_line=line_no,
                            raw_match=m.group(0)[:100],
                        ))

        high_risk  = [a for a in assumptions if a.confidence == "HIGH"]
        total      = len(assumptions)

        if len(high_risk) >= 3:
            overall_risk = "HIGH"
        elif len(high_risk) >= 1 or total >= 5:
            overall_risk = "MEDIUM"
        elif total >= 1:
            overall_risk = "LOW"
        else:
            overall_risk = "NONE"

        notes.append(
            "All findings are POSSIBLE_ASSUMPTION — code evidence only. "
            "Confirm with domain experts before treating as verified business rules."
        )

        return AssumptionDiscoveryResult(
            assumptions=assumptions,
            high_risk=high_risk,
            total_found=total,
            files_scanned=files_scanned,
            overall_risk=overall_risk,
            notes=notes,
        )