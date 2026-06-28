"""
========================================================================
MODULE 1 EXTENSIONS — Package Init
CodeTruth Agent V3

Enhances Module 1 Repository Cognition without modifying the core.
Core module (cognition_engine.py, cognition_report.py) stays frozen.

All extensions are purely deterministic — no LLM, no probabilistic
guessing. Every finding is evidence-based and traceable.

SCOPE CORRECTIONS (applied throughout this package):
  - domain_knowledge_discovery.py : document POINTERS only, not
    extractor. Rule extraction routes through V3-108.
  - repository_risk_discovery.py  : Critical Component Identification
    only. Blast Radius is Module 5 (V3-017-021).
  - evidence_traceability.py      : Document->Code pointers only.
    Requirement->Code mapping is Module 9 (V3-106).
========================================================================
"""

from .repository_identity import RepositoryIdentityClassifier
from .architecture_detector import ArchitectureDetector
from .boundary_detector import BoundaryDetector
from .signal_analyzer import SignalAnalyzer
from .classification_reason import ClassificationReasonBuilder
from .gate_validator import GateValidator
from .domain_knowledge_discovery import DomainKnowledgeDiscovery
from .assumption_discovery import AssumptionDiscovery
from .constraint_discovery import ConstraintDiscovery
from .decision_discovery import DecisionDiscovery
from .knowledge_loss_detector import KnowledgeLossDetector
from .evidence_traceability import EvidenceTraceability
from .repository_risk_discovery import RepositoryRiskDiscovery
from .enhanced_report_builder import EnhancedReportBuilder
from .domain_signatures import get_enhanced_application_type, detect_domain_from_signatures

__all__ = [
    "RepositoryIdentityClassifier",
    "ArchitectureDetector",
    "BoundaryDetector",
    "SignalAnalyzer",
    "ClassificationReasonBuilder",
    "GateValidator",
    "DomainKnowledgeDiscovery",
    "AssumptionDiscovery",
    "ConstraintDiscovery",
    "DecisionDiscovery",
    "KnowledgeLossDetector",
    "EvidenceTraceability",
    "RepositoryRiskDiscovery",
    "EnhancedReportBuilder",
]