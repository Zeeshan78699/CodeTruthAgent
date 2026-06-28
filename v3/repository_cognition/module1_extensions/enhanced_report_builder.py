"""
========================================================================
enhanced_report_builder.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITY:
    Unified Enhanced Module 1 Report

Produces the standard enhanced text output format for Module 1.
Core CognitionReport is passed in — never modified.

TRUTH BOUNDARY — UNKNOWN case:
    Candidate domains are listed without percentages.
    Percentage confidence on unresolved candidates = guess dressed
    as precision. Violates the Truth Boundary.
    Candidates are listed; selection belongs to the human.
========================================================================
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .repository_identity        import RepositoryIdentityClassifier, RepositoryIdentity
from .architecture_detector      import ArchitectureDetector, ArchitectureDetectionResult
from .boundary_detector          import BoundaryDetector, BoundaryDetectionResult
from .signal_analyzer            import SignalAnalyzer, SignalResult
from .classification_reason      import ClassificationReasonBuilder, ClassificationEvidence
from .gate_validator             import GateValidator, GateValidationResult
from .domain_knowledge_discovery import DomainKnowledgeDiscovery, KnowledgeIndex
from .assumption_discovery       import AssumptionDiscovery, AssumptionDiscoveryResult
from .constraint_discovery       import ConstraintDiscovery, ConstraintDiscoveryResult
from .decision_discovery         import DecisionDiscovery, DecisionDiscoveryResult
from .knowledge_loss_detector    import KnowledgeLossDetector, KnowledgeLossResult
from .evidence_traceability      import EvidenceTraceability, TraceabilityResult
from .repository_risk_discovery  import RepositoryRiskDiscovery, RepositoryRiskResult
from .domain_signatures          import get_enhanced_application_type


@dataclass
class EnhancedModule1Report:
    core_report:           object
    identity:              RepositoryIdentity
    architecture:          ArchitectureDetectionResult
    boundary:              BoundaryDetectionResult
    signals:               SignalResult
    classification_reason: ClassificationEvidence
    gate:                  GateValidationResult
    knowledge_index:       KnowledgeIndex
    assumptions:           AssumptionDiscoveryResult
    constraints:           ConstraintDiscoveryResult
    decisions:             DecisionDiscoveryResult
    knowledge_loss:        KnowledgeLossResult
    traceability:          TraceabilityResult
    risk:                  RepositoryRiskResult


class EnhancedReportBuilder:

    def build(self, core_report: object, repo_path: str) -> EnhancedModule1Report:
        identity  = RepositoryIdentityClassifier().classify(core_report, repo_path)

        # Apply domain signature enhancement for specialized engineering repos
        # Overrides generic types (DATA_ENGINEERING, GRAPH_ANALYTICS, etc.)
        # with more specific domain classifications when evidence exists.
        # Core-specific types (FINANCE_SYSTEM, ENERGY_SYSTEM) are preserved.
        enhanced_type = get_enhanced_application_type(
            identity.application_type, repo_path
        )
        if enhanced_type != identity.application_type:
            identity.application_type = enhanced_type
            identity.domain = enhanced_type
        arch      = ArchitectureDetector().detect(repo_path)
        boundary  = BoundaryDetector().detect(repo_path)
        signals   = SignalAnalyzer().analyze(repo_path)
        reason    = ClassificationReasonBuilder().build(signals, identity.domain)
        gate      = GateValidator().validate(core_report, identity, boundary)
        ki        = DomainKnowledgeDiscovery().discover(repo_path)
        assum     = AssumptionDiscovery().discover(repo_path)
        const     = ConstraintDiscovery().discover(repo_path)
        decisions = DecisionDiscovery().discover(repo_path)
        kl        = KnowledgeLossDetector().detect(repo_path)
        trace     = EvidenceTraceability().trace(repo_path)
        risk      = RepositoryRiskDiscovery().discover(repo_path)

        return EnhancedModule1Report(
            core_report=core_report,
            identity=identity,
            architecture=arch,
            boundary=boundary,
            signals=signals,
            classification_reason=reason,
            gate=gate,
            knowledge_index=ki,
            assumptions=assum,
            constraints=const,
            decisions=decisions,
            knowledge_loss=kl,
            traceability=trace,
            risk=risk,
        )

    # ------------------------------------------------------------------
    # Text formatter
    # ------------------------------------------------------------------

    def format_text(self, r: EnhancedModule1Report) -> str:
        sep  = "=" * 80
        sep2 = "-" * 40

        is_unknown = not r.identity.is_known

        if is_unknown:
            return self._format_unknown(r, sep, sep2)
        return self._format_known(r, sep, sep2)

    # ------------------------------------------------------------------

    def _format_known(self, r: EnhancedModule1Report, sep: str, sep2: str) -> str:
        L = []

        # -- Header --------------------------------------------------------
        L += [sep,
              "CODETRUTH AGENT V3",
              "Module 1 Enhanced Repository Cognition",
              sep, ""]

        # -- Repository Identity -------------------------------------------
        L += ["Repository Identity", sep2]
        L += [f"  Repository Name      : {r.identity.repository_name}"]
        L += [f"  Domain               : {r.identity.application_type}"]
        L += [f"  Framework            : {r.identity.primary_framework}"]
        L += [f"  Architecture         : {r.architecture.pattern}"]
        L += [f"  Boundary Detected    : {str(r.boundary.boundary_detected).upper()}", ""]

        # -- Repository Statistics -----------------------------------------
        # Count Python files specifically
        from pathlib import Path
        root = Path(str(getattr(r.core_report, '_repo_path',
               getattr(r.boundary, 'root_path', ''))))
        py_count = 0
        try:
            py_count = sum(1 for _ in root.rglob("*.py"))
        except Exception:
            py_count = r.boundary.total_files

        L += ["Repository Statistics", sep2]
        L += [f"  Total Files          : {r.boundary.total_files}"]
        L += [f"  Python Files         : {py_count}"]
        L += [f"  Directories          : {r.boundary.total_dirs}", ""]

        # -- Signal Analysis -----------------------------------------------
        pkg_hits    = [s for sigs in r.signals.package_signals.values() for s in sigs]
        import_hits = [s for sigs in r.signals.import_signals.values()  for s in sigs]
        content_hits= [s for sigs in r.signals.content_signals.values() for s in sigs]

        L += ["Signal Analysis", sep2]
        L += [f"  Package Signals      : {', '.join(pkg_hits[:5]) or 'none'}"]
        L += [f"  Import Signals       : {', '.join(import_hits[:5]) or 'none'}"]
        L += [f"  Content Signals      : {', '.join(content_hits[:5]) or 'none'}", ""]

        # -- Classification Evidence ---------------------------------------
        scores = r.signals.domain_scores
        top3   = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]

        L += ["Classification Evidence", sep2]
        for domain, score in top3:
            L += [f"  {domain:<20} : {score}"]
        L += [""]
        L += [f"  Winning Reason:"]
        L += [f"  {r.classification_reason.winning_reason}", ""]

        # -- Domain Knowledge Discovery ------------------------------------
        L += ["Domain Knowledge Discovery", sep2]
        L += [f"  README Files         : {len(r.knowledge_index.readme_files)}"]
        L += [f"  Business Rules       : {len(r.knowledge_index.business_rule_docs)}"]
        L += [f"  Architecture Docs    : {len(r.knowledge_index.architecture_docs)}"]
        L += [f"  Functional Specs     : {len(r.knowledge_index.functional_specs)}"]
        L += [""]
        purpose = str(getattr(r.core_report, 'project_purpose', ''))
        if purpose:
            L += [f"  Knowledge Summary:"]
            L += [f"  {purpose}", ""]

        # -- Assumption Discovery ------------------------------------------
        L += ["Assumption Discovery", sep2]
        for i, a in enumerate(r.assumptions.high_risk[:3], 1):
            L += [f"  Assumption {i}:"]
            L += [f"  {a.raw_match[:60]}", ""]
        L += [f"  Assumption Risk:"]
        L += [f"  {r.assumptions.overall_risk}", ""]

        # -- Constraint Discovery ------------------------------------------
        L += ["Constraint Discovery", sep2]
        all_constraints = r.constraints.constraints[:3]
        for c in all_constraints:
            L += [f"  Constraint:"]
            L += [f"  {c.constraint_type} — {c.raw_match[:60]}", ""]

        # -- Decision Discovery --------------------------------------------
        L += ["Decision Discovery", sep2]
        for d in r.decisions.decisions[:2]:
            L += [f"  Decision:"]
            L += [f"  {d.description[:80]}"]
            L += [f"  Evidence:"]
            L += [f"  {d.evidence[:80]}", ""]

        # -- Knowledge Loss Detection --------------------------------------
        L += ["Knowledge Loss Detection", sep2]
        for risk in r.knowledge_loss.high_severity[:2]:
            L += [f"  Risk:"]
            L += [f"  {risk.description[:100]}"]
            L += [f"  Severity:"]
            L += [f"  {risk.severity}", ""]
        if not r.knowledge_loss.high_severity:
            L += [f"  No high severity knowledge risks detected.", ""]

        # -- Evidence Traceability -----------------------------------------
        L += ["Evidence Traceability", sep2]
        L += ["  Business Rule"]
        L += ["        |"]
        L += ["        v"]
        L += ["  Implementation"]
        L += ["        |"]
        L += ["        v"]
        L += ["  Tests", ""]
        status = "COMPLETE" if r.traceability.total_test_links > 0 else "PARTIAL"
        L += [f"  Traceability:"]
        L += [f"  {status}"]
        L += [f"  {r.traceability.coverage_note}", ""]

        # -- Repository Risk Discovery -------------------------------------
        L += ["Repository Risk Discovery", sep2]
        L += ["  Critical Modules:"]
        for f_ in r.risk.top_risk_files[:3]:
            from pathlib import Path
            L += [f"  {Path(f_).name}"]
        L += [""]
        score = r.risk.repository_risk_score
        risk_label = "HIGH" if score >= 8 else ("MEDIUM" if score >= 5 else "LOW")
        L += [f"  Risk Score:"]
        L += [f"  {risk_label}", ""]

        # -- Governance Gate -----------------------------------------------
        L += ["Governance Gate", sep2]
        L += [f"  Gate Passed : {str(r.gate.gate_passed).upper()}"]
        L += [f"  Decision    : {r.gate.gate_decision}", ""]

        # -- Confidence ----------------------------------------------------
        L += ["Confidence", sep2]
        conf   = getattr(r.core_report, 'confidence_score', 'N/A')
        status = getattr(r.core_report, 'cognition_status', 'N/A')
        L += [f"  Confidence Score : {conf}"]
        L += [f"  Status           : {status}", ""]

        # -- Footer --------------------------------------------------------
        approved = r.gate.approved_for == "MODULE_2"
        L += [sep]
        L += ["PASS" if r.gate.gate_passed else "REVIEW REQUIRED"]
        L += ["Module 1 Repository Understanding Successful" if r.gate.gate_passed
              else "Module 1 Repository Understanding Incomplete"]
        L += ["Approved For Module 2" if approved
              else (r.gate.blocking_reason or "Not approved")]
        L += [sep]

        return "\n".join(L)

    # ------------------------------------------------------------------

    def _format_unknown(self, r: EnhancedModule1Report, sep: str, sep2: str) -> str:
        """
        UNKNOWN case output.

        TRUTH BOUNDARY: candidate domains listed WITHOUT percentages.
        Percentages on unresolved guesses = fabricated precision.
        Human selects; selection stored as HUMAN_OVERRIDE, not as Truth.
        """
        L = [sep,
             "CODETRUTH AGENT V3",
             "Module 1 Enhanced Repository Cognition",
             sep, ""]

        L += ["Status : UNKNOWN", ""]

        L += ["Signal Analysis:", sep2]
        if r.classification_reason.evidence_strength == "NONE":
            L += ["  Insufficient evidence to classify domain.", ""]
        else:
            L += [f"  Strength : {r.classification_reason.evidence_strength}",
                  f"  Top Signal : {r.signals.top_domain} (score={r.signals.top_score})", ""]

        L += ["Documentation Discovery:", sep2]
        if not r.knowledge_index.business_rule_docs:
            L += ["  No business rule documents found.", ""]
        else:
            L += [f"  {len(r.knowledge_index.business_rule_docs)} business rule doc(s) found.", ""]

        L += ["Assumption Discovery:", sep2]
        if r.assumptions.total_found == 0:
            L += ["  Not enough evidence to identify assumptions.", ""]
        else:
            L += [f"  {r.assumptions.total_found} possible assumption(s) found.", ""]

        L += ["Governance Gate:", sep2]
        L += [f"  {r.gate.gate_decision}", ""]

        # Candidate domains — NO percentages (Truth Boundary)
        scores  = r.signals.domain_scores
        top_candidates = sorted(
            [(d, s) for d, s in scores.items() if s > 0],
            key=lambda x: x[1],
            reverse=True
        )[:3]

        if top_candidates:
            L += ["Suggested Domains  [ranked by signal count — no percentages]:", sep2]
            for domain, score in top_candidates:
                L += [f"  {domain}  (signals found: {score})"]
            L += [""]
            L += ["  NOTE: These are structural signal rankings, not confidence scores."]
            L += ["  Attaching percentages to unresolved candidates would be fabricated"]
            L += ["  precision — a Truth Boundary violation. Human selects; selection"]
            L += ["  stored as HUMAN_OVERRIDE, confidence = UNVERIFIED.", ""]
        else:
            L += ["Suggested Domains:", sep2]
            L += ["  No domain signals found. Manual inspection required.", ""]

        L += ["Action:", sep2]
        L += ["  Human Review Required"]
        L += ["  Select domain from candidates above."]
        L += ["  System will re-scan after HUMAN_OVERRIDE is applied.", ""]

        L += [sep,
              "REVIEW REQUIRED",
              "Insufficient evidence for automatic classification.",
              "Human review required before Module 2 proceeds.",
              sep]

        return "\n".join(L)