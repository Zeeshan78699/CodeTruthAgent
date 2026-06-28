"""
========================================================================
repository_risk_discovery.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITIES:
    - Critical Component Detection
    - High Impact Module Detection
    - Repository Risk Scoring

SCOPE CORRECTION (critical):
    Blast Radius Estimation = Module 5 (V3-017-021, Impact Analysis).
    This module identifies which components LOOK high-risk based on
    structural signals only — centrality, naming, size, import frequency.
    Actual blast radius requires Module 5's call-graph traversal.

TRUTH BOUNDARY:
    Risk score is structural. Business criticality requires domain context.
    "HIGH_RISK" means structurally central and poorly covered — not
    "this module will definitely cause an outage."
========================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import re


# Name patterns that suggest criticality
_CRITICAL_NAME_SIGNALS = [
    "engine", "core", "main", "gateway", "orchestrat",
    "process", "workflow", "manager", "dispatcher",
    "payment", "invoice", "approval", "auth", "security",
    "transaction", "ledger", "safety", "shutdown",
]


@dataclass
class CriticalComponent:
    source_file:     str
    risk_level:      str      # "HIGH" | "MEDIUM" | "LOW"
    risk_reasons:    list[str]
    import_count:    int      # how many files import this
    function_count:  int
    has_tests:       bool
    risk_score:      int      # composite 0-10


@dataclass
class RepositoryRiskResult:
    critical_components:   list[CriticalComponent]
    high_risk_count:       int
    repository_risk_score: int      # 0-10 composite
    top_risk_files:        list[str]
    notes:                 list[str]


class RepositoryRiskDiscovery:
    """
    Identifies structurally high-risk components.
    Does NOT calculate blast radius — that is Module 5's job.
    """

    MAX_FILES = 300

    def discover(self, repo_path: str) -> RepositoryRiskResult:
        root = Path(repo_path)
        notes: list[str] = []

        if not root.exists():
            return RepositoryRiskResult(
                critical_components=[], high_risk_count=0,
                repository_risk_score=0, top_risk_files=[],
                notes=["Repository path does not exist"],
            )

        py_files   = list(root.rglob("*.py"))[:self.MAX_FILES]
        test_names = {f.name for f in py_files if f.name.startswith("test_")}

        # Build import frequency map
        import_counts: dict[str, int] = {}
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in re.finditer(
                r"from\s+([\w.]+)\s+import|import\s+([\w.]+)", content
            ):
                mod = (m.group(1) or m.group(2) or "").split(".")[0]
                if mod:
                    import_counts[mod] = import_counts.get(mod, 0) + 1

        components: list[CriticalComponent] = []

        for py_file in py_files:
            if py_file.name.startswith("test_"):
                continue

            rel  = str(py_file.relative_to(root))
            stem = py_file.stem

            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            import_freq   = import_counts.get(stem, 0)
            func_count    = len(re.findall(r"^\s*def\s+\w+", content, re.MULTILINE))
            has_test      = f"test_{py_file.name}" in test_names
            name_lower    = stem.lower()

            risk_reasons: list[str] = []
            score = 0

            # Signal: heavily imported
            if import_freq >= 10:
                risk_reasons.append(f"Imported by ~{import_freq} files")
                score += 3
            elif import_freq >= 5:
                risk_reasons.append(f"Imported by ~{import_freq} files")
                score += 2

            # Signal: critical name pattern
            if any(sig in name_lower for sig in _CRITICAL_NAME_SIGNALS):
                matched = [s for s in _CRITICAL_NAME_SIGNALS if s in name_lower]
                risk_reasons.append(f"Critical name signals: {', '.join(matched)}")
                score += 2

            # Signal: large file (many functions)
            if func_count >= 15:
                risk_reasons.append(f"Large file: {func_count} functions")
                score += 2
            elif func_count >= 8:
                risk_reasons.append(f"Medium file: {func_count} functions")
                score += 1

            # Signal: no test coverage
            if not has_test:
                risk_reasons.append("No test file found")
                score += 2

            if score == 0:
                continue

            risk_level = "HIGH" if score >= 6 else ("MEDIUM" if score >= 3 else "LOW")

            components.append(CriticalComponent(
                source_file=rel,
                risk_level=risk_level,
                risk_reasons=risk_reasons,
                import_count=import_freq,
                function_count=func_count,
                has_tests=has_test,
                risk_score=min(score, 10),
            ))

        components.sort(key=lambda c: c.risk_score, reverse=True)
        high_risk  = [c for c in components if c.risk_level == "HIGH"]
        top_files  = [c.source_file for c in components[:5]]

        # Actual Python file count in the full repo (not capped by MAX_FILES)
        try:
            actual_py_count = sum(1 for _ in root.rglob("*.py"))
        except Exception:
            actual_py_count = len(py_files)

        raw_score = min(len(high_risk) * 2 + len(components), 10)

        # Calibration 1: polyglot repos — large file count drives score
        if actual_py_count > 500 and raw_score >= 8:
            raw_score = 7
            notes.append(
                f"POLYGLOT_CALIBRATION_APPLIED: capped at 7 "
                f"(actual_py_count={actual_py_count})."
            )

        # Calibration 2: zero HIGH risk but score 10 is internally inconsistent
        if len(high_risk) == 0 and raw_score >= 10:
            raw_score = 7
            notes.append(
                "SECONDARY_CALIBRATION_APPLIED: capped at 7 — "
                "zero HIGH risk components with score 10 is inconsistent."
            )

        repo_score = raw_score

        notes.append(
            "SCOPE NOTE: This module identifies structurally high-risk "
            "components. Actual blast radius requires Module 5 (V3-017-021). "
            "Risk score is structural — business criticality requires domain context."
        )

        return RepositoryRiskResult(
            critical_components=components,
            high_risk_count=len(high_risk),
            repository_risk_score=repo_score,
            top_risk_files=top_files,
            notes=notes,
        )