"""
========================================================================
architecture_detector.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITY:
    Architecture Pattern Recognition (basic)

Fixes TC_M1_001 gap: architecture_pattern field missing from report.

SCOPE:
    Basic structural pattern detection only — MVC, Layered, Microservices,
    Event-Driven, Pipeline, Library, Monolith, etc.
    Deep architecture redesign and violation detection = Module 9.

TRUTH BOUNDARY:
    Returns UNKNOWN if no pattern signals found.
    Confidence attached to every detection.
    No guessing.
========================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import re


# ---------------------------------------------------------------------------
# Pattern signatures
# ---------------------------------------------------------------------------

_PATTERNS: list[dict] = [
    {
        "name": "MVC",
        "signals": ["models", "views", "controllers", "templates"],
        "min_signals": 2,
    },
    {
        "name": "LAYERED",
        "signals": ["service", "repository", "controller", "domain",
                    "infrastructure", "application", "presentation"],
        "min_signals": 2,
    },
    {
        "name": "MICROSERVICES",
        "signals": ["docker-compose", "kubernetes", "k8s", "service",
                    "gateway", "api-gateway", "helm"],
        "min_signals": 2,
    },
    {
        "name": "EVENT_DRIVEN",
        "signals": ["event", "listener", "handler", "subscriber",
                    "publisher", "queue", "broker", "consumer"],
        "min_signals": 2,
    },
    {
        "name": "PIPELINE",
        "signals": ["pipeline", "stage", "step", "transform",
                    "processor", "etl", "ingestion"],
        "min_signals": 2,
    },
    {
        "name": "LIBRARY",
        "signals": ["setup.py", "pyproject.toml", "setup.cfg",
                    "__init__.py", "src"],
        "min_signals": 2,
    },
    {
        "name": "MONOLITH",
        "signals": ["manage.py", "app.py", "main.py", "wsgi.py",
                    "asgi.py", "server.py"],
        "min_signals": 1,
    },
]


@dataclass
class ArchitectureDetectionResult:
    pattern:     str               # e.g. "LAYERED", "MVC", "UNKNOWN"
    confidence:  str               # "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN"
    evidence:    list[str]         # folder/file names that triggered detection
    all_scores:  dict[str, int]    # pattern -> signal match count


class ArchitectureDetector:
    """
    Detects basic architecture patterns by scanning folder/file names.
    Does not read file contents — structure only.
    """

    def detect(self, repo_path: str) -> ArchitectureDetectionResult:
        root = Path(repo_path)
        if not root.exists():
            return ArchitectureDetectionResult(
                pattern="UNKNOWN", confidence="UNKNOWN",
                evidence=[], all_scores={}
            )

        # Collect all folder and file names (lowercase) up to depth 3
        names: set[str] = set()
        try:
            for item in root.rglob("*"):
                depth = len(item.relative_to(root).parts)
                if depth <= 3:
                    names.add(item.name.lower())
        except Exception:
            pass

        scores: dict[str, int]        = {}
        matched_evidence: dict[str, list[str]] = {}

        for pattern in _PATTERNS:
            hits = [s for s in pattern["signals"] if s in names]
            scores[pattern["name"]]        = len(hits)
            matched_evidence[pattern["name"]] = hits

        # Select winner: highest score that meets min_signals threshold
        winner      = None
        winner_hits: list[str] = []
        best_score  = 0

        for pattern in _PATTERNS:
            n     = pattern["name"]
            score = scores[n]
            if score >= pattern["min_signals"] and score > best_score:
                best_score  = score
                winner      = n
                winner_hits = matched_evidence[n]

        if winner is None:
            return ArchitectureDetectionResult(
                pattern="UNKNOWN", confidence="UNKNOWN",
                evidence=[], all_scores=scores
            )

        confidence = "HIGH" if best_score >= 3 else ("MEDIUM" if best_score == 2 else "LOW")

        return ArchitectureDetectionResult(
            pattern=winner,
            confidence=confidence,
            evidence=winner_hits,
            all_scores=scores,
        )
