"""
========================================================================
knowledge_loss_detector.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITIES:
    - Single Point Of Failure Detection
    - Undocumented Logic Detection
    - Knowledge Risk Analysis

Identifies critical logic that exists in only one place, has no
documentation, and represents a knowledge risk if that file or
developer is unavailable.

TRUTH BOUNDARY:
    Risk is structural — based on file centrality and lack of comments.
    Does not claim business criticality without domain context.
========================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class KnowledgeRisk:
    risk_type:    str       # "SINGLE_POINT_OF_FAILURE" | "UNDOCUMENTED_LOGIC" | "NO_TESTS"
    severity:     str       # "HIGH" | "MEDIUM" | "LOW"
    source_file:  str
    description:  str
    evidence:     str


@dataclass
class KnowledgeLossResult:
    risks:             list[KnowledgeRisk]
    high_severity:     list[KnowledgeRisk]
    spof_files:        list[str]       # files with no test coverage and high import count
    undocumented:      list[str]       # files with functions but no docstrings
    total_risks:       int
    overall_severity:  str
    notes:             list[str]


class KnowledgeLossDetector:
    """
    Structural knowledge risk analysis — no content interpretation.
    """

    MAX_FILES      = 300
    SPOF_THRESHOLD = 5    # imported by >= N other files = potential SPOF

    def detect(self, repo_path: str) -> KnowledgeLossResult:
        root = Path(repo_path)
        risks:        list[KnowledgeRisk] = []
        spof_files:   list[str]           = []
        undocumented: list[str]           = []
        notes:        list[str]           = []

        if not root.exists():
            return KnowledgeLossResult(
                risks=[], high_severity=[], spof_files=[],
                undocumented=[], total_risks=0,
                overall_severity="NONE",
                notes=["Repository path does not exist"],
            )

        py_files = list(root.rglob("*.py"))[:self.MAX_FILES]

        # -- Import frequency map ------------------------------------------
        import_counts: dict[str, int] = {}
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in re.finditer(r"from\s+([\w.]+)\s+import|import\s+([\w.]+)", content):
                mod = (m.group(1) or m.group(2) or "").split(".")[0]
                if mod:
                    import_counts[mod] = import_counts.get(mod, 0) + 1

        # -- Scan each file --------------------------------------------------
        test_files = {f.name for f in py_files if f.name.startswith("test_")}

        for py_file in py_files:
            rel = str(py_file.relative_to(root))
            stem = py_file.stem

            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                lines   = content.splitlines()
            except Exception:
                continue

            # SPOF check — heavily imported but no test file
            import_freq = import_counts.get(stem, 0)
            has_test    = f"test_{stem}.py" in test_files
            if import_freq >= self.SPOF_THRESHOLD and not has_test:
                spof_files.append(rel)
                risks.append(KnowledgeRisk(
                    risk_type="SINGLE_POINT_OF_FAILURE",
                    severity="HIGH" if import_freq >= 10 else "MEDIUM",
                    source_file=rel,
                    description=(
                        f"Imported by ~{import_freq} files but has no test file. "
                        "Loss of this file has wide structural impact."
                    ),
                    evidence=f"import_count={import_freq}, test_file=None",
                ))

            # Undocumented logic check
            func_count    = len(re.findall(r"^\s*def\s+\w+", content, re.MULTILINE))
            docstring_count = content.count('"""') + content.count("'''")
            if func_count >= 3 and docstring_count == 0:
                undocumented.append(rel)
                risks.append(KnowledgeRisk(
                    risk_type="UNDOCUMENTED_LOGIC",
                    severity="MEDIUM" if func_count >= 5 else "LOW",
                    source_file=rel,
                    description=(
                        f"{func_count} functions with no docstrings. "
                        "Business logic may be implicit knowledge only."
                    ),
                    evidence=f"function_count={func_count}, docstrings=0",
                ))

        high_sev = [r for r in risks if r.severity == "HIGH"]
        total    = len(risks)

        if len(high_sev) >= 3:
            overall = "HIGH"
        elif len(high_sev) >= 1 or total >= 5:
            overall = "MEDIUM"
        elif total >= 1:
            overall = "LOW"
        else:
            overall = "NONE"

        notes.append(
            "Knowledge risk is structural — based on import frequency and "
            "absence of tests/documentation. Business criticality requires "
            "domain expert confirmation."
        )

        return KnowledgeLossResult(
            risks=risks,
            high_severity=high_sev,
            spof_files=spof_files,
            undocumented=undocumented,
            total_risks=total,
            overall_severity=overall,
            notes=notes,
        )
