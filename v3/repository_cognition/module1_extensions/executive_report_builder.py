"""
executive_report_builder.py

CodeTruth Agent V3
Module 1 Extension

## Purpose

Convert EnhancedModule1Report into an
enterprise-grade executive repository report.

This module does NOT add intelligence.

It formats existing Module 1 outputs into a
human-readable governance report.
"""

from dataclasses import asdict

# File

# executive_report_builder.py

class ExecutiveReportBuilder:

    def build(self, r):

        sep = "=" * 80
        sep2 = "-" * 40

        lines = [
            sep,
            "CODETRUTH AGENT V3",
            "Module 1 Enhanced Repository Cognition",
            sep,
            "",
            "Repository Identity",
            sep2,
            f"Repository Name      : {r.identity.repository_name}",
            f"Domain               : {r.identity.domain}",
            f"Framework            : {r.identity.primary_framework}",
            f"Architecture         : {r.architecture.pattern}",
            f"Boundary Detected    : {str(r.boundary.boundary_detected).upper()}",
            "",
            "Repository Statistics",
            sep2,
            f"Total Files          : {r.boundary.total_files}",
            f"Directories          : {r.boundary.total_dirs}",
            "",
            "Signal Analysis",
            sep2,
            f"Top Domain           : {r.signals.top_domain}",
            f"Top Score            : {r.signals.top_score}",
            "",
            "Classification Evidence",
            sep2,
            f"Winning Reason       : {r.classification_reason.winning_reason}",
            f"Evidence Strength    : {r.classification_reason.evidence_strength}",
            "",
            "Domain Knowledge Discovery",
            sep2,
            f"README Files         : {len(r.knowledge_index.readme_files)}",
            f"Business Rules       : {len(r.knowledge_index.business_rule_docs)}",
            f"Architecture Docs    : {len(r.knowledge_index.architecture_docs)}",
            f"Functional Specs     : {len(r.knowledge_index.functional_specs)}",
            "",
            "Assumption Discovery",
            sep2,
            f"Total Assumptions    : {r.assumptions.total_found}",
            f"High Risk            : {len(r.assumptions.high_risk)}",
            f"Overall Risk         : {r.assumptions.overall_risk}",
            "",
            "Constraint Discovery",
            sep2,
            f"Total Constraints    : {r.constraints.total_found}",
            "",
            "Decision Discovery",
            sep2,
            f"ADR Files            : {len(r.decisions.adr_files)}",
            f"Framework Choices    : {len(r.decisions.framework_decisions)}",
            f"Total Decisions      : {r.decisions.total_found}",
            "",
            "Knowledge Loss Detection",
            sep2,
            f"Total Risks          : {r.knowledge_loss.total_risks}",
            f"SPOF Candidates      : {len(r.knowledge_loss.spof_files)}",
            f"Undocumented         : {len(r.knowledge_loss.undocumented)}",
            f"Overall Severity     : {r.knowledge_loss.overall_severity}",
            "",
            "Evidence Traceability",
            sep2,
            f"Document-Code Links  : {r.traceability.total_doc_links}",
            f"{r.traceability.coverage_note}",
            "",
            "Repository Risk Discovery",
            sep2,
            f"Critical Components  : {len(r.risk.critical_components)}",
            f"High Risk Count      : {r.risk.high_risk_count}",
            f"Risk Score           : {r.risk.repository_risk_score}/10",
            "",
            "Governance Gate",
            sep2,
            f"Gate Passed          : {str(r.gate.gate_passed).upper()}",
            f"Decision             : {r.gate.gate_decision}",
            f"Approved For         : {r.gate.approved_for}",
            "",
            "Confidence",
            sep2,
            f"Confidence Score     : {getattr(r.core_report, 'confidence_score', 'N/A')}",
            f"Status               : {getattr(r.core_report, 'cognition_status', 'N/A')}",
            "",
            sep,
        ]

        if r.gate.gate_passed:
            lines.append("PASS")
            lines.append(
                "Module 1 Repository Understanding Successful"
            )
            lines.append(
                f"Approved For {r.gate.approved_for}"
            )
        else:
            lines.append("REVIEW REQUIRED")

        lines.append(sep)

        return "\n".join(lines)