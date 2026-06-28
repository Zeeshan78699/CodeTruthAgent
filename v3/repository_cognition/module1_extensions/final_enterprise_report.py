"""
final_enterprise_report.py
CodeTruth Agent V3 — Module 1 Extension

PURPOSE:
    Enterprise-grade repository cognition report.
    Adds domain conflict resolution, warnings, and hypotheses
    on top of the existing EnhancedModule1Report.

DESIGN NOTE — PASS_WITH_WARNINGS governance state:
    This module uses "PASS_WITH_WARNINGS" in its formatted output.
    This state is NOT yet defined in V3-038-040 (SAFE/REVIEW/BLOCK/FREEZE_PATCH).
    It is a reporting convenience only — it does NOT override gate_decision
    from GateValidator. Before Module 7 is built, this needs a formal decision
    record: adopt as a fifth governance state or map to REVIEW_REQUIRED.

SCOPE NOTE:
    Does not touch Module 1 Core.
    Domain subsumption logic delegated to domain_weights.py.
"""

from __future__ import annotations

try:
    from .domain_weights import evaluate_domain_hierarchy
except ImportError:
    # Fallback if used standalone
    def evaluate_domain_hierarchy(primary, secondary):
        if primary.upper() == secondary.upper():
            return "NONE", False
        return "DOMAIN_CONFLICT_DETECTED", True

# Generic domain classification sets — used for conflict resolution
# and domain-aware warnings. No per-domain special cases.
CORE_DOMAINS = {
    "finance", "medical", "robotics", "climate", "fpga",
    "erp", "ai_ml", "aerospace", "energy", "manufacturing",
    "scientific", "defense", "automotive", "telecom", "sap",
}

INFRA_DOMAINS = {
    "web", "data", "network", "api", "devops",
    "cli", "library", "web_protocol", "network_io",
}


class FinalEnterpriseReportBuilder:
    """
    Builds the enterprise report from an EnhancedModule1Report.

    Domain conflict resolution is now fully generic via domain_weights.py.
    No repository-specific or domain-specific special cases here.
    """

    def build(self, r) -> str:

        sep = "=" * 80
        div = "-" * 80

        warnings   = []
        hypotheses = []

        primary_domain   = str(getattr(r.identity, "domain",     "UNKNOWN"))
        secondary_domain = str(getattr(r.signals,  "top_domain", "UNKNOWN"))

        # ------------------------------------------------------------------
        # Generic domain conflict resolution
        # Uses domain_weights.py + explicit CORE_DOMAINS/INFRA_DOMAINS sets
        # No per-domain special cases anywhere in this file
        # ------------------------------------------------------------------
        p_lower = primary_domain.lower()
        s_lower = secondary_domain.lower()

        if p_lower == s_lower or not secondary_domain or secondary_domain == "UNKNOWN":
            conflict_status       = "NONE"
            trigger_domain_warning = False
        elif p_lower in CORE_DOMAINS and s_lower in INFRA_DOMAINS:
            conflict_status       = "RESOLVED_BY_SUBSUMPTION"
            trigger_domain_warning = False
        elif s_lower in CORE_DOMAINS and p_lower in INFRA_DOMAINS:
            conflict_status       = "RESOLVED_BY_SUBSUMPTION"
            trigger_domain_warning = False
        else:
            # Fall back to domain_weights for any unhandled pairing
            conflict_status, trigger_domain_warning = evaluate_domain_hierarchy(
                primary_domain, secondary_domain
            )

        if trigger_domain_warning:
            warnings.append((
                "DOMAIN_CONFLICT_DETECTED",
                f"Primary domain ({primary_domain}) and secondary domain "
                f"({secondary_domain}) disagree. Human review recommended.",
            ))

        # ------------------------------------------------------------------
        # Business rules check — domain-aware (Option B)
        # Protocol libraries/frameworks: INFORMATIONAL
        # Core business domain repos with no business rules: REVIEW_RECOMMENDED
        # ------------------------------------------------------------------
        biz_rule_count = len(getattr(r.knowledge_index, "business_rule_docs", []))
        is_core_domain = p_lower in CORE_DOMAINS

        # Repos that are libraries/frameworks are NOT expected to have
        # business rule documents regardless of domain
        arch_pattern = str(getattr(r.architecture, "pattern", "")).upper()
        is_library   = "LIBRARY" in arch_pattern or "FRAMEWORK" in arch_pattern

        if biz_rule_count == 0:
            if is_core_domain and not is_library:
                # Real business application in a core domain with no docs
                # → worth flagging as a governance concern
                warnings.append((
                    "NO_BUSINESS_RULE_DOCS_FOUND",
                    f"Domain is {primary_domain} but no business rule documents "
                    f"were found. For a business application this is a governance "
                    f"concern. Verify that rules are documented.",
                ))
            else:
                # Protocol library, framework, or non-core domain → informational
                hypotheses.append((
                    "No Business Rule Documents Found",
                    "Expected for protocol libraries, frameworks, and toolkits. "
                    "Not a governance concern for this repository type.",
                    "INFORMATIONAL",
                ))

        # ------------------------------------------------------------------
        # Traceability warnings
        # ------------------------------------------------------------------
        coverage_note = getattr(r.traceability, "coverage_note", "")

        if "CENTRALIZED_TEST_HARNESS_DETECTED" in coverage_note:
            # Evidence confirmed — no warning needed
            pass
        elif "LOW_COVERAGE_DETECTED" in coverage_note:
            warnings.append((
                "LOW_TEST_COVERAGE",
                f"{coverage_note} — no centralized harness evidence found.",
            ))
        elif "0.0%" in coverage_note:
            warnings.append((
                "TEST_COVERAGE_METRIC_UNRELIABLE",
                coverage_note,
            ))

        # ------------------------------------------------------------------
        # Hypotheses
        # ------------------------------------------------------------------
        if getattr(r.boundary, "is_monorepo", False):
            hypotheses.append((
                "Large Scale Repository Profile",
                "Repository exhibits monorepo characteristics.",
                "SUSPECTED",
            ))

        if conflict_status == "DOMAIN_CONFLICT_DETECTED":
            hypotheses.append((
                "Behavioural Domain Partitioning",
                "Repository may contain multiple domain responsibilities.",
                "SUSPECTED",
            ))

        if "CENTRALIZED_TEST_HARNESS_DETECTED" in coverage_note:
            hypotheses.append((
                "Centralized Test Architecture",
                "Shared test execution infrastructure detected — physical "
                "evidence found.",
                "VERIFIED",
            ))
        elif "LOW_COVERAGE_DETECTED" in coverage_note:
            hypotheses.append((
                "Centralized Test Architecture",
                "Low coverage detected but no physical harness evidence found.",
                "SUSPECTED",
            ))

        # ------------------------------------------------------------------
        # Format report
        # ------------------------------------------------------------------
        lines = [
            sep,
            "CODETRUTH AGENT V3",
            "Module 1 Enterprise Repository Cognition",
            sep,
            "",
            "[FACTS]",
            div,
            f"Repository Name      : {r.identity.repository_name}",
            f"Primary Domain       : {primary_domain}",
            f"Secondary Domain     : {secondary_domain}",
            f"Conflict Status      : {conflict_status}",
            f"Framework            : {r.identity.primary_framework}",
            f"Architecture         : {r.architecture.pattern}",
            f"Boundary Detected    : {str(r.boundary.boundary_detected).upper()}",
            "",
            "Repository Statistics",
            "---------------------",
            f"Total Files          : {r.boundary.total_files}",
            f"Directories          : {r.boundary.total_dirs}",
            "",
            "Signal Analysis",
            "---------------",
            f"Top Domain           : {r.signals.top_domain}",
            f"Top Score            : {r.signals.top_score}",
            "",
            "Domain Knowledge Discovery",
            "--------------------------",
            f"README Files         : {len(r.knowledge_index.readme_files)}",
            f"Business Rules       : {len(r.knowledge_index.business_rule_docs)}",
            f"Architecture Docs    : {len(r.knowledge_index.architecture_docs)}",
            f"Functional Specs     : {len(r.knowledge_index.functional_specs)}",
            "",
            "Decision Discovery",
            "------------------",
            f"ADR Files            : {len(r.decisions.adr_files)}",
            f"Framework Decisions  : {len(r.decisions.framework_decisions)}",
            f"Total Decisions      : {r.decisions.total_found}",
            "",
            "Evidence Traceability",
            "---------------------",
            f"Document-Code Links  : {r.traceability.total_doc_links}",
            f"Coverage             : {coverage_note}",
            "",
        ]

        # Warnings block
        lines += ["[WARNINGS]", div]
        if warnings:
            for code, detail in warnings:
                lines += [f"  {code}", f"  {detail}", ""]
        else:
            lines += ["  None", ""]

        # Hypotheses block
        lines += ["", "[HYPOTHESES]", div]
        if hypotheses:
            for title, basis, status in hypotheses:
                lines += [
                    f"  {title}",
                    f"  Basis  : {basis}",
                    f"  Status : {status}",
                    "",
                ]
        else:
            lines += ["  None", ""]

        # Governance block
        gate_display = (
            "PASS_WITH_WARNINGS"
            if warnings and r.gate.gate_passed
            else r.gate.gate_decision
        )
        lines += [
            "",
            "[GOVERNANCE]",
            div,
            f"Gate Passed : {str(r.gate.gate_passed).upper()}",
            f"Decision    : {gate_display}",
            f"Approved For: {r.gate.approved_for}",
            "",
            "Confidence",
            "----------",
            f"Confidence Score : {getattr(r.core_report, 'confidence_score', 'N/A')}",
            f"Status           : {getattr(r.core_report, 'cognition_status', 'N/A')}",
            "",
            sep,
        ]

        return "\n".join(lines)