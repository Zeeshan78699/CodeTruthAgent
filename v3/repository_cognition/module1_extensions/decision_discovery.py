"""
========================================================================
decision_discovery.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITIES:
    - Design Decision Detection
    - Architecture Decision Discovery
    - Decision Evidence Mapping

Answers: "Why was this design chosen?"

Detects ADR files, TODO/DECISION comments, framework choices,
and technology selection evidence.

TRUTH BOUNDARY:
    Decisions are INFERRED from structural evidence.
    No claim is made about WHY a decision was made without evidence.
========================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import re


_ADR_PATTERNS = {"adr", "decision", "decisions", "architecture-decision"}

_DECISION_COMMENT_PATTERNS = [
    (r"#\s*(?:DECISION|CHOSEN|SELECTED|REASON|WHY)[\s:]+(.+)", "EXPLICIT_COMMENT"),
    (r"#\s*(?:TODO|FIXME|NOTE|HACK)[\s:]+(.+)",                "IMPLICIT_NOTE"),
]

_FRAMEWORK_CHOICE_SIGNALS = {
    "redis":       "Redis chosen (likely for caching/session/queue)",
    "celery":      "Celery chosen (async task queue over sync processing)",
    "kafka":       "Kafka chosen (event streaming over direct calls)",
    "rabbitmq":    "RabbitMQ chosen (message broker)",
    "graphql":     "GraphQL chosen over REST",
    "grpc":        "gRPC chosen (likely for inter-service communication)",
    "mongodb":     "MongoDB chosen (document store over relational)",
    "postgresql":  "PostgreSQL chosen as primary database",
    "elasticsearch":"Elasticsearch chosen (full-text search)",
}


@dataclass
class Decision:
    decision_type:  str     # "ADR_FILE" | "FRAMEWORK_CHOICE" | "EXPLICIT_COMMENT" | "IMPLICIT_NOTE"
    description:    str
    evidence:       str     # file path or matched text
    source_file:    str
    source_line:    int


@dataclass
class DecisionDiscoveryResult:
    decisions:       list[Decision]
    adr_files:       list[str]
    framework_decisions: list[Decision]
    total_found:     int
    notes:           list[str]


class DecisionDiscovery:

    MAX_FILES = 200

    def discover(self, repo_path: str) -> DecisionDiscoveryResult:
        root = Path(repo_path)
        decisions:    list[Decision] = []
        adr_files:    list[str]      = []
        notes:        list[str]      = []

        if not root.exists():
            return DecisionDiscoveryResult(
                decisions=[], adr_files=[], framework_decisions=[],
                total_found=0, notes=["Repository path does not exist"],
            )

        # -- ADR files -------------------------------------------------------
        for item in root.rglob("*"):
            if not item.is_file():
                continue
            depth = len(item.relative_to(root).parts)
            if depth > 5:
                continue
            name_lower = item.name.lower()
            parent_lower = item.parent.name.lower()
            if any(p in name_lower or p in parent_lower for p in _ADR_PATTERNS):
                rel = str(item.relative_to(root))
                adr_files.append(rel)
                decisions.append(Decision(
                    decision_type="ADR_FILE",
                    description=f"Architecture Decision Record found: {item.name}",
                    evidence=rel,
                    source_file=rel,
                    source_line=0,
                ))

        # -- Framework choices from requirements / imports -------------------
        pkg_file = self._find_package_file(root)
        if pkg_file:
            raw = pkg_file.read_text(encoding="utf-8", errors="ignore").lower()
            for lib, description in _FRAMEWORK_CHOICE_SIGNALS.items():
                if lib in raw:
                    decisions.append(Decision(
                        decision_type="FRAMEWORK_CHOICE",
                        description=description,
                        evidence=f"Found '{lib}' in {pkg_file.name}",
                        source_file=str(pkg_file.relative_to(root)),
                        source_line=0,
                    ))

        # -- Decision comments in source files -------------------------------
        py_files = list(root.rglob("*.py"))[:self.MAX_FILES]
        for py_file in py_files:
            try:
                lines = py_file.read_text(
                    encoding="utf-8", errors="ignore"
                ).splitlines()
            except Exception:
                continue
            rel = str(py_file.relative_to(root))
            for line_no, line in enumerate(lines, start=1):
                for pattern, dtype in _DECISION_COMMENT_PATTERNS:
                    m = re.search(pattern, line, re.IGNORECASE)
                    if m:
                        decisions.append(Decision(
                            decision_type=dtype,
                            description=m.group(0)[:120],
                            evidence=line.strip()[:120],
                            source_file=rel,
                            source_line=line_no,
                        ))

        framework_decisions = [d for d in decisions if d.decision_type == "FRAMEWORK_CHOICE"]

        notes.append(
            "Decisions are INFERRED from structural evidence (ADR files, "
            "dependency choices, decision comments). "
            "Original decision rationale may require document review."
        )

        return DecisionDiscoveryResult(
            decisions=decisions,
            adr_files=adr_files,
            framework_decisions=framework_decisions,
            total_found=len(decisions),
            notes=notes,
        )

    def _find_package_file(self, root: Path) -> "Path | None":
        for name in ["requirements.txt", "pyproject.toml", "package.json"]:
            p = root / name
            if p.exists():
                return p
        return None
