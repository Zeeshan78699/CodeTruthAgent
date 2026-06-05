"""
CodeTruth Agent V2
Governance Wiring Layer

Purpose:
    Bridge between RepositoryGraphEngine (scanner output) and the existing
    governance rule modules (TC_V2_001 through TC_V2_014's hand-input rules).

    The scanner produces a RepositoryGraph; this module walks that graph,
    identifies risk-relevant patterns, and produces governance findings
    per file in the form the existing rules expect.

    Active checks (V2):
      Check 1: Mutation of named-global state
      Check 2: Dangerous API calls (delete/network/etc.)

    Retired pending V3:
      Check 3: Undefined-name references
        - Implemented and validated on Flask tutorial; produced 1 finding
          with defensible precision.
        - On click (17 files) produced 70 findings dominated by package
          re-export and relative-import patterns the scanner does not
          fully resolve.
        - Three rounds of calibration could not push precision above
          ~10-15% on click without proper import-tree / type tracking.
        - Decision: retire from V2, re-introduce in V3 alongside
          type/scope tracking.

    Checks 4-6 (fan-in, execution-chain depth, per-file aggregation) are
    deferred to a follow-up module.

Integration notes:
    The functions called below as _existing_rule_* are placeholders for
    the actual governance functions used in TC_V2_001 through TC_V2_014.
    Replace the placeholder bodies with imports of your real rule modules.
    Marked clearly with "TODO: WIRE TO EXISTING RULE".

Change log (this revision):
    - Fixed _lookup_dangerous_api: bare-name table entries (eval, exec)
      now only match bare-name calls. Method-style calls like
      'model.eval' (PyTorch evaluation-mode toggle, not Python's eval)
      no longer trigger DYNAMIC_EXEC/BLOCK. Multi-segment entries
      ('os.remove', 'subprocess.run') match unchanged.
      Bug fix; no API or signature change.

Previous revisions (kept for reference):
    - Check 3 (undefined_reference) removed from the active pipeline.
      The function check_undefined_references and its helpers remain in
      this module for reference and for future V3 work, but they are no
      longer invoked by run_governance_on_scan.
    - imported_names extraction code retained: it is harmless if unused
      and will be needed again when Check 3 is reactivated.
    - Checks 1 and 2 preserved verbatim.
    - report_to_dict and all dataclasses unchanged.
    - No external API change: run_governance_on_scan still takes the same
      arguments and returns the same GovernanceReport type.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set

from ai.repository_graph_engine import (
    RepositoryGraph,
    FileNode,
    FunctionNode,
)

# =========================================================
# CONFIGURATION
# =========================================================

GLOBAL_STATE_NAME_PATTERNS = {
    "DATABASE", "DB", "CACHE", "STATE", "REGISTRY",
    "_REGISTRY", "_CACHE", "_STATE", "STORE", "_STORE",
}

DANGEROUS_API_TABLE = {
    "os.remove":      ("DELETE_OPERATION",  "REVIEW"),
    "os.unlink":      ("DELETE_OPERATION",  "REVIEW"),
    "shutil.rmtree":  ("DELETE_OPERATION",  "BLOCK"),
    "requests.get":   ("NETWORK_OPERATION", "REVIEW"),
    "requests.post":  ("NETWORK_OPERATION", "REVIEW"),
    "subprocess.run": ("PROCESS_OPERATION", "REVIEW"),
    "subprocess.Popen": ("PROCESS_OPERATION", "REVIEW"),
    "eval":           ("DYNAMIC_EXEC",      "BLOCK"),
    "exec":           ("DYNAMIC_EXEC",      "BLOCK"),
}

# Retained for the dormant undefined_reference check (kept for V3).
KNOWN_EXTERNAL_PREFIXES = {
    "os", "sys", "re", "json", "math", "time", "datetime", "pathlib",
    "shutil", "subprocess", "hashlib", "functools", "itertools",
    "collections", "typing", "logging", "warnings", "argparse",
    "requests", "flask", "fastapi", "starlette", "pydantic",
    "click", "rich", "httpx", "anyio", "trio", "asyncio",
    "numpy", "pandas", "torch", "tensorflow", "sklearn",
    "pytest", "unittest", "mock",
}


# =========================================================
# FINDING DATA STRUCTURES
# =========================================================

@dataclass
class GovernanceFinding:
    """One specific risk-relevant observation about one location."""
    file_path: str
    function_name: Optional[str]
    line_number: int
    check_name: str
    category: str
    severity: str
    detail: str
    evidence: str


@dataclass
class FileFindings:
    """All findings for a single file."""
    file_path: str
    findings: List[GovernanceFinding] = field(default_factory=list)


@dataclass
class GovernanceReport:
    """Complete output of the wiring layer for a scanned repository."""
    repo_root: str
    files_scanned: int
    files_with_findings: int
    total_findings: int
    findings_by_check: Dict[str, int] = field(default_factory=dict)
    findings_by_severity: Dict[str, int] = field(default_factory=dict)
    per_file: Dict[str, FileFindings] = field(default_factory=dict)


# =========================================================
# IMPORT NAME EXTRACTION (retained for V3)
# =========================================================

def _build_imported_names_for_file(file_node: FileNode) -> Set[str]:
    """
    Build the set of names imported into this file.
    Currently unused -- retained for V3 when Check 3 is reactivated with
    proper type/scope tracking.
    """
    imported: Set[str] = set()

    for entry in file_node.imports:
        if not entry:
            continue
        first_segment = entry.split(".")[0]
        imported.add(first_segment)
        imported.add(entry)

    for entry in file_node.from_imports:
        if not entry:
            continue
        last_segment = entry.split(".")[-1]
        imported.add(last_segment)
        first_segment = entry.split(".")[0]
        imported.add(first_segment)

    return imported


# =========================================================
# CHECK 1 -- GLOBAL STATE MUTATION (active)
# =========================================================

def check_global_state_mutation(
    file_node: FileNode,
    raw_source: str,
) -> List[GovernanceFinding]:
    """
    Detect assignments to module-level names matching GLOBAL_STATE_NAME_PATTERNS
    that happen INSIDE a function body.

    TODO: WIRE TO EXISTING RULE -- if you already have a mutation-detection
    function from TC_V2_010, import and call it here instead.
    """
    findings: List[GovernanceFinding] = []

    if not raw_source:
        return findings

    source_lines = raw_source.splitlines()

    for function in file_node.functions:
        start = function.line_number - 1
        end = _approximate_function_end(source_lines, start)

        for offset, line in enumerate(source_lines[start:end], start=start):
            stripped = line.strip()
            for global_name in GLOBAL_STATE_NAME_PATTERNS:
                pattern = rf"^\s*{re.escape(global_name)}(\[[^\]]*\]|\.\w+)?\s*="
                if re.match(pattern, line):
                    findings.append(GovernanceFinding(
                        file_path=file_node.file_path,
                        function_name=function.name,
                        line_number=offset + 1,
                        check_name="global_state_mutation",
                        category="GLOBAL_MUTATION",
                        severity="REVIEW",
                        detail=(
                            f"Function {function.name!r} mutates module-level "
                            f"name {global_name!r}."
                        ),
                        evidence=stripped,
                    ))

    return findings


# =========================================================
# CHECK 2 -- DANGEROUS API CALLS (active)
# =========================================================

def check_dangerous_api_calls(
    file_node: FileNode,
) -> List[GovernanceFinding]:
    """
    Scan each function's calls and method_calls for matches against the
    DANGEROUS_API_TABLE.

    TODO: WIRE TO EXISTING RULE -- TC_V2_011 has a hardcoded 4-entry
    classifier. Consider importing that table here or removing the
    duplicate from TC_V2_011 to avoid drift.
    """
    findings: List[GovernanceFinding] = []

    for function in file_node.functions:
        all_calls = list(function.calls) + list(function.method_calls)

        for call in all_calls:
            match = _lookup_dangerous_api(call)
            if match is None:
                continue

            category, severity = match
            findings.append(GovernanceFinding(
                file_path=file_node.file_path,
                function_name=function.name,
                line_number=function.line_number,
                check_name="dangerous_api_call",
                category=category,
                severity=severity,
                detail=(
                    f"Function {function.name!r} calls {call!r}, classified "
                    f"as {category}."
                ),
                evidence=call,
            ))

    return findings


def _lookup_dangerous_api(call_name: str):
    """Match a call name against DANGEROUS_API_TABLE by full name or suffix.

    Bare-name table entries (no dot in the key, e.g. 'eval', 'exec') only
    match when the call is itself a bare name. This prevents method-style
    calls like 'model.eval' (PyTorch evaluation mode) or 'tensor.exec' from
    being misclassified as DYNAMIC_EXEC.

    Multi-segment entries (e.g. 'os.remove', 'subprocess.run') continue to
    match by full name or by trailing suffix as before.
    """
    # Exact match handles both bare names ('eval') and qualified names
    # ('os.remove'). This path is unchanged.
    if call_name in DANGEROUS_API_TABLE:
        return DANGEROUS_API_TABLE[call_name]

    # Suffix match: only for table entries that contain a dot. This is the
    # behavior fix. Previously 'model.eval' suffix-matched the bare 'eval'
    # entry and was wrongly flagged. Now only multi-segment suffixes (e.g.
    # 'mymodule.os.remove' suffix-matching 'os.remove') trigger.
    parts = call_name.split(".")
    for i in range(1, len(parts)):
        candidate = ".".join(parts[i:])
        if "." in candidate and candidate in DANGEROUS_API_TABLE:
            return DANGEROUS_API_TABLE[candidate]

    return None


# =========================================================
# CHECK 3 -- UNDEFINED-NAME REFERENCES (RETIRED, kept for V3)
# =========================================================

def check_undefined_references(
    file_node: FileNode,
    graph: RepositoryGraph,
    ignored_calls: Set[str],
    imported_names: Set[str],
) -> List[GovernanceFinding]:
    """
    RETIRED FROM V2. Kept in this file for reference and future V3 work.

    Flag BARE-NAME calls that:
      - are NOT in ignored_calls
      - are NOT imported into this file
      - do NOT resolve to any function or class in the repository

    Validated on Flask tutorial (1 finding, defensible). On click (17 files)
    produced 70 findings dominated by package re-export and relative-import
    patterns the scanner does not fully resolve. Three calibration rounds
    could not push precision above ~10-15% on click without proper import-
    tree / type tracking. Re-introduce in V3.

    This function is NOT called by run_governance_on_scan in V2.
    """
    findings: List[GovernanceFinding] = []

    for function in file_node.functions:
        for call in function.calls:
            if "." in call:
                continue
            if _is_external_or_ignored(call, ignored_calls, imported_names):
                continue
            if _resolves_anywhere(call, graph):
                continue

            findings.append(GovernanceFinding(
                file_path=file_node.file_path,
                function_name=function.name,
                line_number=function.line_number,
                check_name="undefined_reference",
                category="UNDEFINED_NAME",
                severity="REVIEW",
                detail=(
                    f"Function {function.name!r} references bare name {call!r}."
                ),
                evidence=call,
            ))

    return findings


def _is_external_or_ignored(
    call: str,
    ignored_calls: Set[str],
    imported_names: Set[str],
) -> bool:
    """True if the call should not be flagged as undefined.
    Helper for the retired check_undefined_references; retained for V3."""
    if call in ignored_calls:
        return True
    suffix = call.split(".")[-1]
    if suffix in ignored_calls:
        return True

    if call in imported_names:
        return True
    if suffix in imported_names:
        return True
    first_segment = call.split(".")[0]
    if first_segment in imported_names:
        return True

    if first_segment in KNOWN_EXTERNAL_PREFIXES:
        return True

    return False


def _resolves_anywhere(call: str, graph: RepositoryGraph) -> bool:
    """True if the call name (or its suffix) matches anything in the indexes.
    Helper for the retired check_undefined_references; retained for V3."""
    suffix = call.split(".")[-1]
    return (
        call in graph.function_index
        or suffix in graph.function_index
        or call in graph.class_index
        or suffix in graph.class_index
    )


# =========================================================
# ORCHESTRATION
# =========================================================

def run_governance_on_scan(
    graph: RepositoryGraph,
    ignored_calls: Set[str],
    repo_root: str,
) -> GovernanceReport:
    """
    Walk every file in the scan, run the ACTIVE checks (1 and 2), and
    aggregate findings into a GovernanceReport.

    Check 3 (undefined_reference) is retired in V2 and not invoked here.
    Its function is kept in this module for future V3 work.
    """
    per_file: Dict[str, FileFindings] = {}
    findings_by_check: Dict[str, int] = {}
    findings_by_severity: Dict[str, int] = {}
    total = 0

    for file_path, file_node in graph.files.items():
        raw_source = _read_source(repo_root, file_path)

        file_findings = FileFindings(file_path=file_path)

        # Check 1: global state mutation (active)
        file_findings.findings.extend(
            check_global_state_mutation(file_node, raw_source)
        )

        # Check 2: dangerous API calls (active)
        file_findings.findings.extend(
            check_dangerous_api_calls(file_node)
        )

        # Check 3 retired in V2 -- intentionally not called here.

        if file_findings.findings:
            per_file[file_path] = file_findings
            for f in file_findings.findings:
                findings_by_check[f.check_name] = findings_by_check.get(f.check_name, 0) + 1
                findings_by_severity[f.severity] = findings_by_severity.get(f.severity, 0) + 1
                total += 1

    return GovernanceReport(
        repo_root=repo_root,
        files_scanned=len(graph.files),
        files_with_findings=len(per_file),
        total_findings=total,
        findings_by_check=findings_by_check,
        findings_by_severity=findings_by_severity,
        per_file=per_file,
    )


# =========================================================
# HELPERS
# =========================================================

def _read_source(repo_root: str, relative_path: str) -> str:
    full = Path(repo_root) / relative_path
    try:
        return full.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _approximate_function_end(source_lines: List[str], start_index: int) -> int:
    """Find the next top-level def/class after start_index, or end of file."""
    for i in range(start_index + 1, len(source_lines)):
        line = source_lines[i]
        if re.match(r"^(def|class|async def)\s", line):
            return i
    return len(source_lines)


def report_to_dict(report: GovernanceReport) -> dict:
    """Serializable form of the report (for JSON output)."""
    return {
        "repo_root": report.repo_root,
        "files_scanned": report.files_scanned,
        "files_with_findings": report.files_with_findings,
        "total_findings": report.total_findings,
        "findings_by_check": report.findings_by_check,
        "findings_by_severity": report.findings_by_severity,
        "per_file": {
            fp: {
                "file_path": ff.file_path,
                "findings": [asdict(f) for f in ff.findings],
            }
            for fp, ff in report.per_file.items()
        },
    }
