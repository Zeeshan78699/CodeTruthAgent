"""
TC_V2_047 - V2 Single-Repository Evaluation (V2.2 wiring)

Objective:
Run the V2 pipeline (semantic + behavioral + fusion + governance + V1)
on a single external repository. Capture results separately for:

    1. V2 baseline (rule-based governance findings)
    2. V2 decision pipeline (V2.2 wiring: V1-driven candidates with
       cross-file pair support; token-overlap fallback)
    3. V1 ground truth (duplicate detection findings)

Usage:
    python -m tests.intelligence.fusion_tests.tc_v2_047_repo_evaluation <repo_path> [pair_cap]

Examples:
    # Flask tutorial (validation run)
    python -m tests.intelligence.fusion_tests.tc_v2_047_repo_evaluation C:\\repos\\flask-tutorial 25

    # Django (full run with higher pair cap)
    python -m tests.intelligence.fusion_tests.tc_v2_047_repo_evaluation C:\\repos\\django 100

Output:
    tests/output/v2/v2_1_repo_evaluation/<repo_name>_report.json

Honest scope:
- This test does NOT hand-verify true positives. That's manual work.
- It captures raw findings for later precision audit.
- Use it to scale V2 evaluation across 8 repos efficiently.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Dict, List

# =========================================================
# PATH SETUP
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =========================================================
# IMPORTS
# =========================================================

from ai.repository_graph_engine import RepositoryGraphEngine
from ai.governance_wiring import (
    run_governance_on_scan,
    report_to_dict,
)
from ai.v1_adapter import V1Adapter
from ai.decision_orchestrator import DecisionOrchestrator


# =========================================================
# OUTPUT PATHS
# =========================================================

OUTPUT_DIR = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "v2_1_repo_evaluation"
)


# =========================================================
# CONFIGURATION
# =========================================================

# Default pair cap for the decision pipeline. Override via CLI.
DEFAULT_PAIR_CAP = 25

# Cap V1 file analysis per repo (V1 risk_analyze takes ~5s per pair)
V1_MAX_FILES = 25


# =========================================================
# PAIR EXTRACTION (same heuristic as v2_orchestrator)
# =========================================================

def collect_function_pairs(graph, repo_root: str, pair_cap: int):
    """
    Extract candidate function pairs from the repository graph.
    Uses the same heuristic as v2_orchestrator: skip backups,
    share at least one meaningful token, exclude trivial tokens.
    """

    skip_patterns = (
        ".bak",
        "_old",
        "_backup",
        " - Copy",
        "_pre_",
        ".pre_",
        "_archive",
    )

    trivial = {"a", "b", "the", "to", "of", "in", "for", "is", "as", ""}

    def names_likely_related(a: str, b: str) -> bool:
        if a == b:
            return False
        # Skip pairs where EITHER side is a test function.
        # Catches both `test_X` (public test) and `_test_X` (internal
        # test helper) prefixes. V2 governs production-code merges;
        # pairing tests with implementation or with each other
        # produces governance noise.
        if (
            a.startswith("test_") or b.startswith("test_")
            or a.startswith("_test_") or b.startswith("_test_")
        ):
            return False
        tokens_a = set(a.lower().split("_"))
        tokens_b = set(b.lower().split("_"))
        tokens_a = {
            t for t in tokens_a
            if t and len(t) > 2 and t not in trivial
        }
        tokens_b = {
            t for t in tokens_b
            if t and len(t) > 2 and t not in trivial
        }
        if not tokens_a or not tokens_b:
            return False
        return len(tokens_a & tokens_b) >= 1

    pairs: List[Dict] = []
    repo_path = Path(repo_root)

    for file_node in graph.files.values():
        file_path = file_node.file_path

        if any(p in file_path for p in skip_patterns):
            continue

        function_names = [
            f.name for f in file_node.functions
            if "." not in f.name
        ]

        if len(function_names) < 2:
            continue

        absolute_path = str(repo_path / file_path)

        seen = set()
        for i in range(len(function_names)):
            for j in range(i + 1, len(function_names)):
                a = function_names[i]
                b = function_names[j]

                if not names_likely_related(a, b):
                    continue

                key = (absolute_path, a, b)
                if key in seen:
                    continue
                seen.add(key)

                pairs.append({
                    "file_path": absolute_path,
                    "function_a": a,
                    "function_b": b,
                })

                if len(pairs) >= pair_cap:
                    return pairs

    return pairs


# =========================================================
# V2.2 V1-DRIVEN CANDIDATE EXTRACTION
# =========================================================

def collect_pairs_from_v1(
    v1_findings: List[Dict],
    repo_root: str,
    pair_cap: int,
) -> List[Dict]:
    """
    V2.2 PRIMARY candidate extraction for evaluation.

    Use V1's duplicate-detection findings as the candidate-pair source.
    V1 has already filtered out trivial structural noise (decorator
    families, factory wrappers, naming-only similarity) by applying
    its own structural similarity threshold.

    Cross-file pairs (file_1 != file_2) are fully supported.

    V1 finding format (from v1_adapter.py):
        {
            "function_1": str,
            "function_2": str,
            "file_1": str,       # function_1's file
            "file_2": str,       # function_2's file (may differ)
            "similarity": float,
            "duplicate_type": str,
            "risk_level": str,
            ...
        }

    Returns a list of dicts with keys:
        file_path, function_a, function_b
        file_path_b (only set when V1 reports a cross-file pair)
    """

    repo_path = Path(repo_root)
    pairs: List[Dict] = []
    seen = set()
    cross_file_count = 0

    for finding in v1_findings:
        func_a = finding.get("function_1")
        func_b = finding.get("function_2")
        file_a = finding.get("file_1")
        file_b = finding.get("file_2")

        if not (func_a and func_b and file_a):
            continue

        if func_a == func_b and file_a == file_b:
            # Trivial self-match; skip
            continue

        # Resolve function_a's file to absolute
        file_a_obj = Path(file_a)
        if not file_a_obj.is_absolute():
            file_a_obj = repo_path / file_a
        absolute_file_a = str(file_a_obj)

        # Detect cross-file pair
        is_cross_file = bool(file_b) and file_a != file_b
        absolute_file_b = None

        if is_cross_file:
            cross_file_count += 1
            file_b_obj = Path(file_b)
            if not file_b_obj.is_absolute():
                file_b_obj = repo_path / file_b
            absolute_file_b = str(file_b_obj)

        key = (absolute_file_a, absolute_file_b, func_a, func_b)
        if key in seen:
            continue
        seen.add(key)

        pair_record: Dict = {
            "file_path": absolute_file_a,
            "function_a": func_a,
            "function_b": func_b,
        }
        if absolute_file_b:
            pair_record["file_path_b"] = absolute_file_b

        pairs.append(pair_record)

        if len(pairs) >= pair_cap:
            break

    if cross_file_count > 0:
        print(
            f"  Note: {cross_file_count} V1 finding(s) are "
            f"cross-file pairs; behavioral engine will read each "
            f"function from its own file (V2.2 cross-file support)."
        )

    return pairs


# =========================================================
# MAIN EVALUATION
# =========================================================

def evaluate_repo(repo_path: str, pair_cap: int = DEFAULT_PAIR_CAP) -> Dict:
    """
    Run V2 pipeline (V2.2 wiring) on a single repository.
    Return consolidated report.
    """

    repo = Path(repo_path).resolve()
    repo_name = repo.name

    print("=" * 90)
    print(f"TC_V2_047 - V2 EVALUATION ON {repo_name}")
    print(f"Repository: {repo}")
    print(f"Pair cap: {pair_cap}")
    print("=" * 90)

    if not repo.exists():
        raise FileNotFoundError(f"Repository not found: {repo}")

    start_time = time.time()

    # -------------------------------------------------
    # STEP 1 - REPOSITORY GRAPH
    # -------------------------------------------------

    print("\n[STEP 1] Building Repository Graph...")
    step_start = time.time()

    graph_engine = RepositoryGraphEngine(str(repo))
    graph = graph_engine.build_graph()
    repository_files = len(graph.files)

    print(f"  Files scanned: {repository_files}")
    print(f"  Step time: {time.time() - step_start:.1f}s")

    # -------------------------------------------------
    # STEP 2 - V2 BASELINE: GOVERNANCE SCAN (rule-based)
    # -------------------------------------------------

    print("\n[STEP 2] Running Governance Scan (V2 baseline)...")
    step_start = time.time()

    governance_report = run_governance_on_scan(
        graph=graph,
        ignored_calls=set(),
        repo_root=str(repo),
    )
    governance_findings = report_to_dict(governance_report)

    gov_total = governance_findings.get("total_findings", 0)
    gov_severity = governance_findings.get("findings_by_severity", {})
    gov_safe = gov_severity.get("SAFE", 0)
    gov_review = gov_severity.get("REVIEW", 0)
    gov_block = gov_severity.get("BLOCK", 0)

    print(f"  Governance findings: {gov_total}")
    print(f"  SAFE: {gov_safe} / REVIEW: {gov_review} / BLOCK: {gov_block}")
    print(f"  Step time: {time.time() - step_start:.1f}s")

    # -------------------------------------------------
    # STEP 3 - V1 GROUND TRUTH: DUPLICATE DETECTION
    # (V2.2: V1 runs BEFORE the decision pipeline so its
    # findings can drive candidate-pair extraction.)
    # -------------------------------------------------

    print("\n[STEP 3] Running V1 Adapter (ground truth + candidate source)...")
    step_start = time.time()

    try:
        adapter = V1Adapter(
            project_path=str(repo),
            max_files=V1_MAX_FILES,
        )
        v1_summary = adapter.get_summary()
        v1_findings = v1_summary.get("findings", [])
        v1_count = len(v1_findings)
        print(f"  V1 findings: {v1_count}")
    except Exception as exc:
        print(f"  V1 Adapter Error: {exc}")
        v1_findings = []
        v1_count = 0

    print(f"  Step time: {time.time() - step_start:.1f}s")

    # -------------------------------------------------
    # STEP 4 - V2 CONTRIBUTION: DECISION PIPELINE
    # (V2.2: candidates come from V1 findings; falls back
    # to token-overlap extraction if V1 returns nothing.)
    # -------------------------------------------------

    print("\n[STEP 4] Running V2 Decision Pipeline (V2.2 V1-driven)...")
    step_start = time.time()

    print("  Loading DecisionOrchestrator (embedding model)...")
    decision_orchestrator = DecisionOrchestrator()

    # V2.2: try V1-driven extraction first
    candidate_source = "v1-driven"
    pairs: List[Dict] = []
    if v1_findings:
        pairs = collect_pairs_from_v1(
            v1_findings, str(repo), pair_cap
        )

    # V2.2: fallback to token-overlap if V1 returned nothing usable
    if not pairs:
        candidate_source = "token-overlap-fallback"
        print(
            "  V1 returned no usable candidates; "
            "falling back to token-overlap extraction."
        )
        pairs = collect_function_pairs(graph, str(repo), pair_cap)

    print(f"  Candidate source: {candidate_source}")
    print(f"  Candidate pairs: {len(pairs)}")

    decision_results = []
    decision_safe = 0
    decision_review = 0
    decision_block = 0
    decision_errors = 0
    decision_opposing = 0

    for index, pair in enumerate(pairs, start=1):
        # V2.2: file_path_b is None for intra-file pairs,
        # set when V1 reports a cross-file duplicate.
        file_path_b = pair.get("file_path_b")

        try:
            result = decision_orchestrator.analyze_function_pair(
                file_path=pair["file_path"],
                function_a=pair["function_a"],
                function_b=pair["function_b"],
                file_path_b=file_path_b,
            )
        except Exception as exc:
            decision_errors += 1
            print(
                f"    [{index}/{len(pairs)}] ERROR "
                f"{pair['function_a']} <-> {pair['function_b']}: {exc}"
            )
            continue

        if result.fusion_decision == "SAFE":
            decision_safe += 1
        elif result.fusion_decision == "REVIEW":
            decision_review += 1
        elif result.fusion_decision == "BLOCK":
            decision_block += 1

        if result.fusion_opposing_detected:
            decision_opposing += 1

        decision_results.append({
            "file_path": pair["file_path"],
            "file_path_b": file_path_b,
            "function_a": pair["function_a"],
            "function_b": pair["function_b"],
            "semantic_decision": result.semantic_decision,
            "semantic_score": result.semantic_score,
            "behavioral_tags_a": result.behavioral_tags_a,
            "behavioral_tags_b": result.behavioral_tags_b,
            "behavioral_risk_a": result.behavioral_risk_a,
            "behavioral_risk_b": result.behavioral_risk_b,
            "fusion_decision": result.fusion_decision,
            "fusion_risk_score": result.fusion_risk_score,
            "fusion_risk_level": result.fusion_risk_level,
            "fusion_opposing_detected": result.fusion_opposing_detected,
            "governance_action": result.governance_action,
            "pipeline_complete": result.pipeline_complete,
        })

        print(
            f"    [{index}/{len(pairs)}] "
            f"{pair['function_a']} <-> {pair['function_b']}: "
            f"{result.fusion_decision} ({result.fusion_risk_level})"
        )

    print(f"  V2 pairs analyzed: {len(decision_results)}")
    print(
        f"  SAFE: {decision_safe} / REVIEW: {decision_review} / "
        f"BLOCK: {decision_block} / OPPOSING: {decision_opposing} / "
        f"ERRORS: {decision_errors}"
    )
    print(f"  Step time: {time.time() - step_start:.1f}s")

    # -------------------------------------------------
    # ASSEMBLE REPORT
    # -------------------------------------------------

    total_time = time.time() - start_time

    report = {
        "test_case": "TC_V2_047",
        "repository_name": repo_name,
        "repository_path": str(repo),
        "pair_cap": pair_cap,
        "v1_max_files": V1_MAX_FILES,

        # V2 baseline
        "repository_files": repository_files,
        "governance_findings_total": gov_total,
        "governance_safe": gov_safe,
        "governance_review": gov_review,
        "governance_block": gov_block,
        "governance_per_file": governance_findings.get("per_file", {}),

        # V2 contribution (V2.2 wiring)
        "decision_pipeline_candidate_source": candidate_source,
        "decision_pipeline_candidates": len(pairs),
        "decision_pipeline_analyzed": len(decision_results),
        "decision_pipeline_safe": decision_safe,
        "decision_pipeline_review": decision_review,
        "decision_pipeline_block": decision_block,
        "decision_pipeline_opposing_detected": decision_opposing,
        "decision_pipeline_errors": decision_errors,
        "decision_pipeline_results": decision_results,

        # V1 ground truth
        "v1_findings_count": v1_count,
        "v1_findings": v1_findings,

        # Diagnostics
        "total_runtime_seconds": round(total_time, 1),
        "status": (
            "PASSED" if decision_errors == 0 else "PARTIAL"
        ),
    }

    # -------------------------------------------------
    # SAVE
    # -------------------------------------------------

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_file = OUTPUT_DIR / f"{repo_name}_report.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    # -------------------------------------------------
    # SUMMARY
    # -------------------------------------------------

    print("\n" + "=" * 90)
    print(f"SUMMARY for {repo_name}")
    print("=" * 90)
    print(f"  Repository files       : {repository_files}")
    print(f"  Governance (V2)        : {gov_total} findings "
          f"({gov_review} REVIEW, {gov_block} BLOCK)")
    print(f"  Decision pipeline (V2): {len(decision_results)} pairs "
          f"({decision_safe} SAFE, {decision_review} REVIEW, "
          f"{decision_block} BLOCK, {decision_opposing} OPPOSING)")
    print(f"  V1 ground truth        : {v1_count} duplicates")
    print(f"  Total runtime          : {total_time:.1f}s")
    print(f"  Status                 : {report['status']}")
    print(f"  Report saved           : {report_file}")
    print("=" * 90)

    return report


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage:")
        print(
            "  python -m tests.intelligence.fusion_tests."
            "tc_v2_047_repo_evaluation <repo_path> [pair_cap]"
        )
        print("\nExample:")
        print(
            "  python -m tests.intelligence.fusion_tests."
            "tc_v2_047_repo_evaluation C:\\repos\\flask-tutorial 25"
        )
        sys.exit(1)

    repo_path = sys.argv[1]

    pair_cap = DEFAULT_PAIR_CAP
    if len(sys.argv) >= 3:
        try:
            pair_cap = int(sys.argv[2])
        except ValueError:
            print(
                f"Invalid pair cap: {sys.argv[2]}. "
                f"Using default {DEFAULT_PAIR_CAP}."
            )

    evaluate_repo(repo_path, pair_cap)
