"""
CodeTruth Agent V2.1
V2 Orchestrator

Purpose:
Central orchestration layer for V2.1.

This version is READ-ONLY.

Pipeline:

    Repository Scan
      -> Repository Graph
      -> Decision Orchestrator (Semantic + Behavioral + Fusion + Risk)
           on real function pairs derived from the graph
      -> Governance Analysis
      -> V1 Analysis
      -> Fallback Routing
      -> Memory Update
      -> Reporting

No repository modifications occur.

V2.1 change vs V2:
    The Decision Orchestrator now runs on REAL function pairs
    extracted from the repository graph, with REAL behavioral
    signatures from AST analysis. The V2 orchestrator no longer
    analyzes a single hardcoded demo pair.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ai.repository_graph_engine import (
    RepositoryGraphEngine,
)
from ai.governance_wiring import (
    run_governance_on_scan,
    report_to_dict,
)
from ai.v1_adapter import V1Adapter
from ai.fallback_orchestrator import route_to_v1
from ai.decision_orchestrator import DecisionOrchestrator


from memory.memory_store_v2 import MemoryStoreV2
from reporting.report_generator import ReportGenerator


# =========================================================
# CONFIGURATION
# =========================================================

# Cap on how many function pairs to run through the decision
# pipeline per orchestrator run. The decision pipeline loads
# an embedding model and is the slowest stage, so we cap to
# keep total runtime predictable. 25 pairs ~ 30-60 seconds.

DECISION_PIPELINE_MAX_PAIRS = 25


# =========================================================
# V2 ORCHESTRATOR
# =========================================================

class V2Orchestrator:

    def __init__(self, repo_root):
        self.repo_root = str(repo_root)

        self.memory = MemoryStoreV2()
        self.decision_orchestrator = DecisionOrchestrator()

        self.report = {
            "repository_files": 0,

            "governance_findings": 0,
            "safe": 0,
            "review": 0,
            "block": 0,

            "v1_findings": 0,

            "decision_pipeline_pairs_analyzed": 0,
            "decision_pipeline_safe": 0,
            "decision_pipeline_review": 0,
            "decision_pipeline_block": 0,
            "decision_pipeline_results": [],
            "decision_pipeline_errors": 0,

            "fallback_triggered": 0,

            "memory_updated": False,

            "status": "INITIALIZED",
        }

    # --------------------------------------------------
    # STEP 1 - REPOSITORY GRAPH
    # --------------------------------------------------

    def build_repository_graph(self):
        print("\n[STEP 1]")
        print("Building Repository Graph")

        engine = RepositoryGraphEngine(self.repo_root)
        graph = engine.build_graph()

        self.report["repository_files"] = len(graph.files)
        return graph

    # --------------------------------------------------
    # STEP 2 - DECISION PIPELINE ON REAL FUNCTION PAIRS
    # --------------------------------------------------

    def run_decision_pipeline(self, graph, v1_findings=None) -> None:
        """
        V2.2 change:
            Candidate pairs come from V1's duplicate-detection findings.
            V1 has already filtered out decorator-family and obvious-noise
            pairs by applying its structural similarity threshold.
            If V1 returns nothing, fall back to graph-based token-overlap
            so the pipeline still produces output.

        For each pair, run the real decision pipeline:
            Semantic -> Behavioral -> Fusion -> Risk
        """

        print("\n[STEP 2]")
        print("Running Decision Pipeline on V1-Identified Pairs")

        # V2.2: primary candidate source is V1's findings
        candidate_pairs = []
        if v1_findings:
            candidate_pairs = self._collect_function_pairs_from_v1(v1_findings)
            if candidate_pairs:
                print(
                    f"  Sourced {len(candidate_pairs)} candidate "
                    f"pair(s) from V1 findings."
                )

        # V2.2: fallback to legacy graph-based extraction if V1 returned
        # nothing usable (greenfield codebase, no duplicates, etc.)
        if not candidate_pairs:
            print(
                "  V1 found no usable candidate pairs; falling back "
                "to graph-based token-overlap extraction."
            )
            candidate_pairs = self._collect_function_pairs_from_graph(graph)

        if not candidate_pairs:
            print("  No candidate function pairs found.")
            return

        # Cap to keep runtime bounded
        capped_pairs = candidate_pairs[:DECISION_PIPELINE_MAX_PAIRS]

        print(
            f"  Analyzing {len(capped_pairs)} function pair(s) "
            f"(capped from {len(candidate_pairs)})"
        )

        for index, pair in enumerate(capped_pairs, start=1):
            file_path = pair["file_path"]
            func_a = pair["function_a"]
            func_b = pair["function_b"]
            # V2.2: cross-file pair support — file_path_b is None for
            # intra-file pairs, set to function_b's file for cross-file.
            file_path_b = pair.get("file_path_b")

            try:
                result = self.decision_orchestrator.analyze_function_pair(
                    file_path=file_path,
                    function_a=func_a,
                    function_b=func_b,
                    file_path_b=file_path_b,
                )
            except Exception as exc:
                self.report["decision_pipeline_errors"] += 1
                print(
                    f"  [{index}] ERROR {func_a} <-> {func_b}: {exc}"
                )
                continue

            # Tally
            self.report["decision_pipeline_pairs_analyzed"] += 1

            decision = result.fusion_decision
            if decision == "SAFE":
                self.report["decision_pipeline_safe"] += 1
            elif decision == "REVIEW":
                self.report["decision_pipeline_review"] += 1
            elif decision == "BLOCK":
                self.report["decision_pipeline_block"] += 1

            # Store summary for the report (cap full details)
            self.report["decision_pipeline_results"].append({
                "file_path": file_path,
                "file_path_b": file_path_b,
                "function_a": func_a,
                "function_b": func_b,
                "semantic_decision": result.semantic_decision,
                "semantic_score": result.semantic_score,
                "behavioral_tags_a": result.behavioral_tags_a,
                "behavioral_tags_b": result.behavioral_tags_b,
                "behavioral_risk_a": result.behavioral_risk_a,
                "behavioral_risk_b": result.behavioral_risk_b,
                "fusion_decision": result.fusion_decision,
                "fusion_risk_score": result.fusion_risk_score,
                "fusion_risk_level": result.fusion_risk_level,
                "fusion_opposing_detected": (
                    result.fusion_opposing_detected
                ),
                "governance_action": result.governance_action,
                "pipeline_complete": result.pipeline_complete,
            })

            print(
                f"  [{index}] {func_a} <-> {func_b}: "
                f"{decision} ({result.fusion_risk_level})"
            )

    # --------------------------------------------------
    # STEP 3 - GOVERNANCE SCAN
    # --------------------------------------------------

    def run_governance(self, graph):
        print("\n[STEP 3]")
        print("Running Governance Scan")

        governance_report = run_governance_on_scan(
            graph=graph,
            ignored_calls=set(),
            repo_root=self.repo_root,
        )

        findings = report_to_dict(governance_report)

        self.report["governance_findings"] = findings.get(
            "total_findings", 0
        )

        severity_summary = findings.get(
            "findings_by_severity", {}
        )

        self.report["safe"] = severity_summary.get("SAFE", 0)
        self.report["review"] = severity_summary.get("REVIEW", 0)
        self.report["block"] = severity_summary.get("BLOCK", 0)

        return findings

    # --------------------------------------------------
    # STEP 4 - V1 ANALYSIS
    # --------------------------------------------------

    def run_v1_analysis(self) -> List[Dict]:
        print("\n[STEP 4]")
        print("Running V1 Adapter")

        try:
            adapter = V1Adapter(
                project_path=self.repo_root,
                max_files=25,
            )
            summary = adapter.get_summary()
            findings = summary.get("findings", [])

            self.report["v1_findings"] = len(findings)
            return findings
        except Exception as exc:
            print(f"  V1 Adapter Error: {exc}")
            return []

    # --------------------------------------------------
    # STEP 5 - FALLBACK ROUTING
    # --------------------------------------------------

    def process_fallbacks(self, governance_findings):
        print("\n[STEP 5]")
        print("Evaluating Fallback Routing")

        for file_data in governance_findings.get(
            "per_file", {}
        ).values():
            for finding in file_data.get("findings", []):
                result = route_to_v1(
                    finding=finding,
                    confidence_score=0.40,
                    v1_handler=None,
                )
                if result.get("fallback"):
                    self.report["fallback_triggered"] += 1

    # --------------------------------------------------
    # STEP 6 - MEMORY
    # --------------------------------------------------

    def update_memory(self):
        print("\n[STEP 6]")
        print("Updating Memory")

        self.memory.store_approved_decision({
            "decision": "V2.1 Orchestrator Run",
            "risk_level": "LOW",
        })

        self.report["memory_updated"] = True

    # --------------------------------------------------
    # STEP 7 - REPORT
    # --------------------------------------------------

    def generate_report(self):
        print("\n[STEP 7]")
        print("Generating Report")

        self.report["status"] = "PASSED"

        ReportGenerator.generate_console_report(self.report)

        output_folder = Path("tests/output/v2")
        output_folder.mkdir(parents=True, exist_ok=True)

        report_file = (
            output_folder / "v2_orchestrator_report.json"
        )

        with open(
            report_file, "w", encoding="utf-8"
        ) as file:
            json.dump(self.report, file, indent=4)

        print(f"\nReport Saved:\n{report_file}")

    # --------------------------------------------------
    # MAIN ENTRY POINT
    # --------------------------------------------------

    def run(self):
        print("\n" + "=" * 70)
        print("CODETRUTH V2 ORCHESTRATOR")
        print("=" * 70)

        graph = self.build_repository_graph()

        # V2.2: V1 analysis runs first so the decision pipeline
        # can use V1's findings as its candidate-pair source.
        # V1 has already filtered out decorator-family noise by
        # applying its structural similarity threshold.
        v1_findings = self.run_v1_analysis()

        # V2.2: decision pipeline now uses V1's findings as the
        # primary candidate source. Falls back to graph-based
        # token-overlap if V1 returns nothing.
        self.run_decision_pipeline(graph, v1_findings)

        governance_findings = self.run_governance(graph)

        self.process_fallbacks(governance_findings)
        self.update_memory()
        self.generate_report()

        return self.report

    # ======================================================
    # INTERNAL: CANDIDATE PAIR EXTRACTION (V2.2)
    # ======================================================

    def _collect_function_pairs_from_v1(
        self, v1_findings: List[Dict]
    ) -> List[Dict]:
        """
        V2.2 PRIMARY candidate extraction.

        Use V1's duplicate-detection findings as the candidate pair
        source. V1 has already filtered out trivial structural noise
        (decorator families, factory wrappers, naming-only similarity)
        by applying its own structural similarity threshold.

        Each V1 finding represents a pair V1 considered structurally
        similar enough to be a potential duplicate. The V2 decision
        pipeline then adds semantic + behavioral analysis on top.

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

        V2.2: Cross-file pairs (file_1 != file_2) are fully supported.
        The decision orchestrator's analyze_function_pair() accepts an
        optional file_path_b parameter. When file_1 != file_2, this
        method emits file_path_b so the behavioral engine reads each
        function from its own file.

        Returns a list of dicts with keys:
            file_path, function_a, function_b
            file_path_b (only set when V1 reports a cross-file pair)
        """

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

            # Convert function_a's file to absolute path
            file_a_obj = Path(file_a)
            if not file_a_obj.is_absolute():
                file_a_obj = Path(self.repo_root) / file_a
            absolute_file_a = str(file_a_obj)

            # Determine whether this is a cross-file pair
            is_cross_file = bool(file_b) and file_a != file_b
            absolute_file_b: Optional[str] = None

            if is_cross_file:
                cross_file_count += 1
                file_b_obj = Path(file_b)
                if not file_b_obj.is_absolute():
                    file_b_obj = Path(self.repo_root) / file_b
                absolute_file_b = str(file_b_obj)

            key = (
                absolute_file_a,
                absolute_file_b,
                func_a,
                func_b,
            )
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

        if cross_file_count > 0:
            print(
                f"  Note: {cross_file_count} V1 finding(s) are "
                f"cross-file pairs; behavioral engine will read each "
                f"function from its own file (V2.2 cross-file support)."
            )

        return pairs

    # ======================================================
    # INTERNAL: CANDIDATE PAIR EXTRACTION (FALLBACK)
    # ======================================================

    def _collect_function_pairs_from_graph(self, graph) -> List[Dict]:
        """
        Legacy V2 candidate extraction (token-overlap pre-filter).

        Used as a FALLBACK in V2.2 when V1 returns no findings — for
        example on greenfield codebases with no duplicates yet, or
        on repositories where V1's threshold rejects everything.

        Retained for completeness so the pipeline always produces
        some output. The token-overlap heuristic is documented as
        noisier than V1-driven extraction (the basis for the
        future calibration work in V2.2).

        Returns a list of dicts with keys:
            file_path, function_a, function_b
        """

        pairs: List[Dict] = []
        
        # Substrings that indicate backup/archive files
        skip_patterns = (
            ".bak",
            "_old",
            "_backup",
            " - Copy",
            "_pre_",
            ".pre_",
            "_archive",
        )

        for file_node in graph.files.values():
            file_path = file_node.file_path
            
            # Skip backup/archive files
            if any(pattern in file_path for pattern in skip_patterns):
                continue

            # Use function names only (not class methods for now)
            function_names = [
                f.name for f in file_node.functions
                if "." not in f.name
            ]

            if len(function_names) < 2:
                continue

            # Brute force pairwise comparison limited per file
            seen = set()
            for i in range(len(function_names)):
                for j in range(i + 1, len(function_names)):
                    a = function_names[i]
                    b = function_names[j]

                    if not self._names_likely_related(a, b):
                        continue

                    key = (file_path, a, b)
                    if key in seen:
                        continue
                    seen.add(key)
                    
                    absolute_path = str(Path(self.repo_root) / file_path)

                    pairs.append({
                        "file_path": absolute_path,       # ← absolute, will work
                        "function_a": a,
                        "function_b": b,
                    })

                    if len(pairs) >= DECISION_PIPELINE_MAX_PAIRS:
                        return pairs

        return pairs
    
    def _names_likely_related(self, a: str, b: str) -> bool:
        """
        Cheap pre-filter: are these two function names likely
        to be semantically similar enough to warrant running the
        full embedding pipeline?

        Heuristic:
            - At least one shared meaningful token (split on underscore)
            - Tokens must be non-empty and longer than 2 characters
            - Not identical names
        """

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

        # Filter out trivial tokens that don't carry meaning:
        # - empty strings (from leading underscores like _foo)
        # - short tokens (is, to, of, in, etc.)
        trivial = {"a", "b", "the", "to", "of", "in", "for", "is", "as", ""}
        tokens_a = {t for t in tokens_a if t and len(t) > 2 and t not in trivial}
        tokens_b = {t for t in tokens_b if t and len(t) > 2 and t not in trivial}

        if not tokens_a or not tokens_b:
            return False

        return len(tokens_a & tokens_b) >= 1

# =========================================================
# STANDALONE EXECUTION
# =========================================================

if __name__ == "__main__":
    repo_root = Path.cwd()
    orchestrator = V2Orchestrator(repo_root)
    orchestrator.run()
