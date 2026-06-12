# report_writer.py
# Human-Readable Scan Report Generator
# CodeTruth Agent V3 — Module 1
#
# Takes a RepositoryCognitionReport and produces:
#   - Console output (formatted terminal)
#   - .txt file (plain text, shareable)
#   - .md file (Markdown, publishable)
#
# Anyone can read this report — developer, manager, researcher.

import os
from datetime import datetime
from pathlib import Path

from .cognition_report import RepositoryCognitionReport


class ReportWriter:
    """
    Converts a RepositoryCognitionReport into human-readable formats.

    Usage:
        writer = ReportWriter(report)
        writer.print_console()
        writer.save_txt("output/scan_report.txt")
        writer.save_markdown("output/scan_report.md")
    """

    def __init__(self, report: RepositoryCognitionReport):
        self.report = report

    # ------------------------------------------------------------------ #
    # Console Output                                                        #
    # ------------------------------------------------------------------ #

    def print_console(self) -> None:
        print(self._build_text())

    # ------------------------------------------------------------------ #
    # File Output                                                           #
    # ------------------------------------------------------------------ #

    def save_txt(self, output_path: str) -> None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(self._build_text(), encoding="utf-8")

    def save_markdown(self, output_path: str) -> None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(self._build_markdown(), encoding="utf-8")

    # ------------------------------------------------------------------ #
    # Plain Text Builder                                                    #
    # ------------------------------------------------------------------ #

    def _build_text(self) -> str:
        r = self.report
        repo_name = os.path.basename(r.repository_root)
        lines = []

        def div(): lines.append("─" * 60)
        def hdiv(): lines.append("═" * 60)
        def section(title): div(); lines.append(f"  {title}"); div()
        def field(label, value): lines.append(f"  {label:<22} {value}")
        def blank(): lines.append("")

        # Header
        hdiv()
        lines.append("  CODETRUTH AGENT V3 — REPOSITORY SCAN REPORT")
        lines.append("  Module 1 — Universal Repository Discovery Engine")
        hdiv()
        blank()

        # Identity
        section("REPOSITORY IDENTITY")
        field("Name:",          repo_name)
        field("Path:",          r.repository_root)
        field("Scanned At:",    r.scan_timestamp[:19].replace("T", " ") + " UTC")
        field("Scan Status:",   r.cognition_status)
        field("Purpose:",       r.project_purpose)
        blank()

        # Classification
        section("CLASSIFICATION")
        field("Application Type:", r.application_type.replace("_", " ").title())
        field("Primary Framework:",
              "No Framework Detected" if r.primary_framework == "None" else r.primary_framework)
        if r.secondary_frameworks:
            field("Secondary:",    ", ".join(r.secondary_frameworks))
        field("Discovery Score:",  f"{r.discovery_score * 100:.0f}%")
        field("Classification:",   f"{r.classification_score * 100:.0f}%")
        blank()

        # Scale
        section("REPOSITORY SCALE")
        field("Total Files:",      str(r.total_files_scanned))
        field("Python Files:",     str(r.total_python_files))
        field("Test Suites:",      ", ".join(r.test_directories) if r.test_directories else "None detected")
        blank()

        # Three-tier asset taxonomy
        section("DISCOVERED ASSETS")
        lines.append(f"  {'Languages (Code):':<22} " + (
            "  ·  ".join(r.detected_languages) if r.detected_languages else "None"
        ))
        lines.append(f"  {'File Types (Docs):':<22} " + (
            "  ·  ".join(r.detected_file_types) if r.detected_file_types else "None"
        ))
        lines.append(f"  {'ML Models:':<22} " + (
            "  ·  ".join(r.detected_model_files) if r.detected_model_files else "None"
        ))
        if r.total_model_files > 0:
            lines.append(f"  {'Total Model Files:':<22} {r.total_model_files}")
        blank()

        # Build Systems
        section("BUILD SYSTEMS")
        if r.build_systems:
            lines.append("  " + "  ·  ".join(r.build_systems))
        else:
            lines.append("  None detected")
        blank()

        # Technology Stack
        section("TECHNOLOGY STACK")
        if r.technology_stack:
            lines.append("  " + "  ·  ".join(r.technology_stack))
        else:
            lines.append("  None detected")
        blank()

        # Entry Points
        section(f"ENTRY POINTS  ({len(r.entry_points)} found)")
        if r.entry_points:
            for ep in r.entry_points[:10]:
                lines.append(f"    {ep}")
            if len(r.entry_points) > 10:
                lines.append(f"    ... and {len(r.entry_points) - 10} more")
        else:
            lines.append("  None detected")
        blank()

        # Configuration Files
        section(f"CONFIGURATION FILES  ({len(r.configuration_files)} found)")
        if r.configuration_files:
            for cf in r.configuration_files:
                lines.append(f"    {cf}")
        else:
            lines.append("  None detected")
        blank()

        # Documentation
        section(f"DOCUMENTATION  ({len(r.documentation_files)} found)")
        if r.documentation_files:
            lines.append("  " + "  ·  ".join(
                os.path.basename(f) for f in r.documentation_files
            ))
        else:
            lines.append("  None detected")
        blank()

        # Warnings
        section("WARNINGS & DIAGNOSTICS")
        if r.warnings:
            for i, w in enumerate(r.warnings, 1):
                lines.append(f"  [{i}] {w}")
        else:
            lines.append("  None — scan completed without issues")
        if r.unknown_file_extensions:
            blank()
            lines.append(f"  UNKNOWN EXTENSIONS ({len(r.unknown_file_extensions)} found — not yet in registry):")
            lines.append("  " + "  ".join(r.unknown_file_extensions[:20]))
            lines.append("  → Add to LANGUAGE_EXTENSIONS in framework_signatures.py")
        blank()

        # Governance Gate
        section("GOVERNANCE GATE — V3-003")
        if r.cognition_status == "COMPLETE":
            lines.append("  Status   : APPROVED")
            lines.append("  Decision : Pipeline may proceed to Module 2")
            lines.append("  Rule     : Repository understanding is complete")
        elif r.cognition_status == "PARTIAL":
            lines.append("  Status   : PROCEED WITH CAUTION")
            lines.append("  Decision : Pipeline may proceed — discovery incomplete")
            lines.append("  Rule     : Some files or signals may have been missed")
        else:
            lines.append("  Status   : BLOCKED")
            lines.append("  Decision : Pipeline must not proceed")
            lines.append(f"  Reason   : {r.error_message}")
        blank()

        # Error
        if r.error_message:
            section("ERROR")
            lines.append(f"  {r.error_message}")
            blank()

        hdiv()
        lines.append("  Generated by CodeTruth Agent V3 — Module 1")
        lines.append("  github.com/Zeeshan78699/CodeTruthAgent")
        hdiv()

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Markdown Builder                                                      #
    # ------------------------------------------------------------------ #

    def _build_markdown(self) -> str:
        r = self.report
        repo_name = os.path.basename(r.repository_root)
        lines = []

        lines.append(f"# Repository Scan Report — {repo_name}")
        lines.append("")
        lines.append("**Generated by:** CodeTruth Agent V3 — Module 1 — Universal Repository Discovery Engine  ")
        lines.append(f"**Scanned At:** {r.scan_timestamp[:19].replace('T', ' ')} UTC  ")
        lines.append(f"**Scan Status:** `{r.cognition_status}`  ")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## Repository Identity")
        lines.append("")
        lines.append(f"| Field | Value |")
        lines.append(f"|---|---|")
        lines.append(f"| Name | {repo_name} |")
        lines.append(f"| Path | `{r.repository_root}` |")
        lines.append(f"| Purpose | {r.project_purpose} |")
        lines.append(f"| Application Type | **{r.application_type.replace('_', ' ').title()}** |")
        _fw_display = "No Framework Detected" if r.primary_framework == "None" else r.primary_framework
        lines.append(f"| Primary Framework | {_fw_display} |")
        if r.secondary_frameworks:
            lines.append(f"| Secondary Frameworks | {', '.join(r.secondary_frameworks)} |")
        lines.append("")

        lines.append("## Confidence")
        lines.append("")
        lines.append(f"| Score | Value |")
        lines.append(f"|---|---|")
        lines.append(f"| Discovery Score | {r.discovery_score * 100:.0f}% |")
        lines.append(f"| Classification Score | {r.classification_score * 100:.0f}% |")
        lines.append(f"| Overall | {r.confidence_score * 100:.0f}% |")
        lines.append("")

        lines.append("## Repository Scale")
        lines.append("")
        lines.append(f"| Metric | Count |")
        lines.append(f"|---|---|")
        lines.append(f"| Total Files Scanned | {r.total_files_scanned} |")
        lines.append(f"| Python Files | {r.total_python_files} |")
        lines.append(f"| Test Directories | {len(r.test_directories)} |")
        lines.append(f"| Entry Points | {len(r.entry_points)} |")
        lines.append(f"| Config Files | {len(r.configuration_files)} |")
        lines.append(f"| Doc Files | {len(r.documentation_files)} |")
        lines.append("")

        lines.append("## Discovered Assets")
        lines.append("")
        lines.append("### Languages (Executable Source Code)")
        lines.append("")
        if r.detected_languages:
            for lang in r.detected_languages:
                lines.append(f"- {lang}")
        else:
            lines.append("- None detected")
        lines.append("")
        lines.append("### File Types (Documents & Data)")
        lines.append("")
        if r.detected_file_types:
            for ft in r.detected_file_types:
                lines.append(f"- {ft}")
        else:
            lines.append("- None detected")
        lines.append("")
        lines.append("### ML Models & Neural Network Weights")
        lines.append("")
        if r.detected_model_files:
            for mf in r.detected_model_files:
                lines.append(f"- {mf}")
            lines.append(f"")
            lines.append(f"**Total model files: {r.total_model_files}**")
        else:
            lines.append("- None detected")
        lines.append("")

        lines.append("## Build Systems")
        lines.append("")
        if r.build_systems:
            for bs in r.build_systems:
                lines.append(f"- {bs}")
        else:
            lines.append("- None detected")
        lines.append("")

        lines.append("## Technology Stack")
        lines.append("")
        if r.technology_stack:
            for tech in r.technology_stack:
                lines.append(f"- {tech}")
        else:
            lines.append("- None detected")
        lines.append("")

        lines.append("## Entry Points")
        lines.append("")
        if r.entry_points:
            for ep in r.entry_points[:20]:
                lines.append(f"- `{ep}`")
            if len(r.entry_points) > 20:
                lines.append(f"- *... and {len(r.entry_points) - 20} more*")
        else:
            lines.append("- None detected")
        lines.append("")

        lines.append("## Configuration Files")
        lines.append("")
        if r.configuration_files:
            for cf in r.configuration_files:
                lines.append(f"- `{cf}`")
        else:
            lines.append("- None detected")
        lines.append("")

        lines.append("## Documentation")
        lines.append("")
        if r.documentation_files:
            for df in r.documentation_files:
                lines.append(f"- `{df}`")
        else:
            lines.append("- None detected")
        lines.append("")

        lines.append("## Test Directories")
        lines.append("")
        if r.test_directories:
            for td in r.test_directories:
                lines.append(f"- `{td}`")
        else:
            lines.append("- None detected")
        lines.append("")

        lines.append("## Warnings & Diagnostics")
        lines.append("")
        if r.warnings:
            for i, w in enumerate(r.warnings, 1):
                lines.append(f"{i}. {w}")
        else:
            lines.append("✅ None — scan completed without issues")
        if r.unknown_file_extensions:
            lines.append("")
            lines.append(f"**Unknown Extensions** ({len(r.unknown_file_extensions)} not yet in registry):")
            for ext in r.unknown_file_extensions[:20]:
                lines.append(f"- `{ext}` — add to `LANGUAGE_EXTENSIONS` for future support")
        lines.append("")

        lines.append("## Governance Gate — V3-003")
        lines.append("")
        if r.cognition_status == "COMPLETE":
            lines.append("✅ **APPROVED** — Repository understanding complete. Pipeline may proceed.")
        elif r.cognition_status == "PARTIAL":
            lines.append("⚠️ **PROCEED WITH CAUTION** — Discovery incomplete. Pipeline may proceed with warnings.")
        else:
            lines.append(f"❌ **BLOCKED** — Pipeline must not proceed. Error: {r.error_message}")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*Generated by [CodeTruth Agent V3](https://github.com/Zeeshan78699/CodeTruthAgent)*  ")
        lines.append(f"*Module 1 — Universal Repository Discovery Engine*  ")
        lines.append(f"*Scan timestamp: {r.scan_timestamp}*")

        return "\n".join(lines)