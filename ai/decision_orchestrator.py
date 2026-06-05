"""
CodeTruth Agent V2.1
Decision Pipeline Orchestrator

Objective:
Provide a single entry point that chains the V2.1 rule-based engines:

    Semantic Decision Engine
      -> Behavioral Signature Engine
      -> Fusion Engine
      -> Risk Classification Engine

This module is the production integration point between the
repository graph and the governance layer.

Two public methods:

    analyze_function_pair(file_path, func_a, func_b)
        - REAL integration entry point.
        - Runs the behavioral engine on the file (real AST analysis).
        - Runs the semantic engine on the function names + extracted code.
        - Fuses the real outputs.
        - Use this for production pipeline integration.

    analyze_signals(func_a, func_b, behavior_a_tags, behavior_b_tags, ...)
        - Lower-level building block.
        - Takes pre-computed signals as input.
        - Useful for unit testing fusion logic in isolation.
        - Do NOT use this as the production entry point.

Honest scope:
- This is rule-based signal fusion, not AI reasoning.
- The behavioral engine uses keyword-table lookup on AST output.
- The semantic engine uses embedding similarity + lexical + purpose.
- The fusion engine combines these signals deterministically.
- No LLM dependency.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from ai.semantic_decision_engine import (
    SemanticDecisionEngine,
)
from ai.behavioral_signature_engine import (
    BehavioralSignatureEngine,
)
from ai.fusion_engine import (
    FusionEngine,
)
from ai.risk_classification_engine import (
    RiskClassificationEngine,
)


# =========================================================
# OUTPUT MODEL
# =========================================================

@dataclass
class PipelineResult:
    """
    Output of the chained decision pipeline.
    Includes every intermediate signal for full traceability.
    """

    # Inputs
    function_a: str
    function_b: str

    # Semantic stage
    semantic_decision: str
    semantic_score: float
    semantic_confidence: float
    semantic_lexical_score: float
    semantic_reasoning: List[str]

    # Behavioral stage
    behavioral_tags_a: List[str]
    behavioral_tags_b: List[str]
    behavioral_risk_a: str
    behavioral_risk_b: str
    behavioral_signatures_extracted: bool

    # Fusion stage
    fusion_decision: str
    fusion_risk_score: int
    fusion_risk_level: str
    fusion_opposing_detected: bool
    fusion_shared_tags: List[str]
    fusion_reasoning: List[str]

    # Risk classification stage
    governance_action: str

    # Diagnostic
    pipeline_complete: bool = True
    pipeline_errors: List[str] = field(default_factory=list)


# =========================================================
# DECISION ORCHESTRATOR
# =========================================================

class DecisionOrchestrator:
    """
    Production orchestrator chaining V2.1 rule-based engines.

    Designed to be instantiated once and called many times.
    Engine instances are cached because the semantic engine
    loads an embedding model on init (~1 second).
    """

    def __init__(self) -> None:
        self.semantic_engine = SemanticDecisionEngine()
        self.behavioral_engine = BehavioralSignatureEngine()
        self.fusion_engine = FusionEngine()
        self.risk_engine = RiskClassificationEngine()

    # =====================================================
    # REAL INTEGRATION ENTRY POINT
    # =====================================================

    def analyze_function_pair(
        self,
        file_path: str,
        function_a: str,
        function_b: str,
        file_path_b: str = None,
    ) -> PipelineResult:
        """
        Production entry point.

        Runs the FULL chain on real code:
            1. Behavioral engine parses the file via AST and extracts
               signatures for every function in the file.
            2. Semantic engine analyzes function name pair + extracted
               code bodies for the two functions of interest.
            3. Fusion engine combines real semantic + behavioral signals.
            4. Risk engine classifies the fusion score.

        V2.2: Optional file_path_b parameter supports cross-file pairs
        (e.g., V1 duplicate findings where function_1 is in file_1 and
        function_2 is in file_2). When file_path_b is omitted or equal
        to file_path, behavior is identical to V2.1 (intra-file pairs).

        Arguments:
            file_path:   absolute path to function_a's source file
            function_a:  name of the first function
            function_b:  name of the second function
            file_path_b: (V2.2) optional path to function_b's source file
                         if it differs from file_path. Defaults to
                         file_path (intra-file pair).
        """

        errors: List[str] = []

        # -------------------------------------------------
        # STAGE 1 - BEHAVIORAL ANALYSIS (REAL AST)
        # -------------------------------------------------

        # Determine the effective file for function_b: cross-file pair
        # uses file_path_b, intra-file pair uses file_path.
        effective_file_b = file_path_b if file_path_b else file_path
        is_cross_file = (
            file_path_b is not None
            and file_path_b != file_path
        )

        try:
            signatures_a = self.behavioral_engine.analyze_file(file_path)
        except Exception as exc:
            errors.append(
                f"behavioral_engine.analyze_file failed on "
                f"file_path={file_path}: {exc}"
            )
            signatures_a = []

        # V2.2: read function_b's signatures from its own file when
        # cross-file. Reuse signatures_a for intra-file pairs (no
        # duplicate file read).
        if is_cross_file:
            try:
                signatures_b = self.behavioral_engine.analyze_file(
                    effective_file_b
                )
            except Exception as exc:
                errors.append(
                    f"behavioral_engine.analyze_file failed on "
                    f"file_path_b={effective_file_b}: {exc}"
                )
                signatures_b = []
        else:
            signatures_b = signatures_a

        sig_a = self._find_signature(signatures_a, function_a)
        sig_b = self._find_signature(signatures_b, function_b)

        if sig_a is None:
            errors.append(
                f"No behavioral signature found for "
                f"function_a={function_a!r} in {file_path}"
            )

        if sig_b is None:
            errors.append(
                f"No behavioral signature found for "
                f"function_b={function_b!r} in {effective_file_b}"
            )

        tags_a = sig_a.behavioral_tags if sig_a else []
        tags_b = sig_b.behavioral_tags if sig_b else []
        risk_a = sig_a.risk_level if sig_a else "LOW"
        risk_b = sig_b.risk_level if sig_b else "LOW"

        # -------------------------------------------------
        # STAGE 2 - EXTRACT CODE BODIES FOR SEMANTIC ENGINE
        # -------------------------------------------------

        # V2.2: extract function_b's code from its own file when
        # cross-file. function_a always comes from file_path.
        code_a = self._extract_function_code(file_path, function_a)
        code_b = self._extract_function_code(
            effective_file_b, function_b
        )

        if not code_a:
            errors.append(
                f"Could not extract code body for {function_a} "
                f"in {file_path}"
            )
        if not code_b:
            errors.append(
                f"Could not extract code body for {function_b} "
                f"in {effective_file_b}"
            )

        # -------------------------------------------------
        # STAGE 3 - SEMANTIC ANALYSIS (REAL CODE)
        # -------------------------------------------------

        semantic_result = self.semantic_engine.analyze_change(
            function_a=function_a,
            function_b=function_b,
            code_a=code_a,
            code_b=code_b,
        )

        # -------------------------------------------------
        # STAGE 4 - FUSION (REAL SIGNALS)
        # -------------------------------------------------

        fusion_result = self.fusion_engine.fuse(
            semantic_score=semantic_result["embedding_score"],
            semantic_decision=semantic_result["decision"],
            behavior_a_tags=tags_a,
            behavior_b_tags=tags_b,
            behavior_a_risk=risk_a,
            behavior_b_risk=risk_b,
        )

        # -------------------------------------------------
        # STAGE 5 - RISK CLASSIFICATION
        # -------------------------------------------------

        risk_result = self.risk_engine.classify_risk(
            fusion_result.fusion_risk_score
        )
        
        # Item 2 fix: respect fusion decision, don't let low-score
        # REVIEW or BLOCK decisions get AUTO_APPLY action.
        governance_action = self._reconcile_action(
        fusion_decision=fusion_result.fusion_decision,
        raw_action=risk_result.action,
        )

        # -------------------------------------------------
        # ASSEMBLE RESULT
        # -------------------------------------------------

        return PipelineResult(
            function_a=function_a,
            function_b=function_b,

            semantic_decision=semantic_result["decision"],
            semantic_score=semantic_result["embedding_score"],
            semantic_confidence=semantic_result["confidence"],
            semantic_lexical_score=semantic_result["lexical_score"],
            semantic_reasoning=semantic_result["reasoning"],

            behavioral_tags_a=tags_a,
            behavioral_tags_b=tags_b,
            behavioral_risk_a=risk_a,
            behavioral_risk_b=risk_b,
            behavioral_signatures_extracted=(
                sig_a is not None and sig_b is not None
            ),

            fusion_decision=fusion_result.fusion_decision,
            fusion_risk_score=fusion_result.fusion_risk_score,
            fusion_risk_level=fusion_result.fusion_risk_level,
            fusion_opposing_detected=(
                fusion_result.opposing_behavior_detected
            ),
            fusion_shared_tags=fusion_result.shared_behavior_tags,
            fusion_reasoning=fusion_result.reasoning,

          #  governance_action=risk_result.action,
            governance_action=governance_action,

            pipeline_complete=(len(errors) == 0),
            pipeline_errors=errors,
        )

    # =====================================================
    # LOWER-LEVEL BUILDING BLOCK (PRE-COMPUTED SIGNALS)
    # =====================================================

    def analyze_signals(
        self,
        function_a: str,
        function_b: str,
        behavior_a_tags: List[str],
        behavior_b_tags: List[str],
        behavior_a_risk: str = "LOW",
        behavior_b_risk: str = "LOW",
        code_a: str = "",
        code_b: str = "",
    ) -> PipelineResult:
        """
        Lower-level building block.

        Takes pre-computed behavioral signals as input. Use this
        for unit-testing fusion logic in isolation. Does NOT
        invoke the behavioral engine.

        For production pipeline integration use analyze_function_pair.
        """

        # SEMANTIC
        semantic_result = self.semantic_engine.analyze_change(
            function_a=function_a,
            function_b=function_b,
            code_a=code_a,
            code_b=code_b,
        )

        # FUSION
        fusion_result = self.fusion_engine.fuse(
            semantic_score=semantic_result["embedding_score"],
            semantic_decision=semantic_result["decision"],
            behavior_a_tags=behavior_a_tags,
            behavior_b_tags=behavior_b_tags,
            behavior_a_risk=behavior_a_risk,
            behavior_b_risk=behavior_b_risk,
        )

        # RISK
        risk_result = self.risk_engine.classify_risk(
            fusion_result.fusion_risk_score
        )

        return PipelineResult(
            function_a=function_a,
            function_b=function_b,

            semantic_decision=semantic_result["decision"],
            semantic_score=semantic_result["embedding_score"],
            semantic_confidence=semantic_result["confidence"],
            semantic_lexical_score=semantic_result["lexical_score"],
            semantic_reasoning=semantic_result["reasoning"],

            behavioral_tags_a=behavior_a_tags,
            behavioral_tags_b=behavior_b_tags,
            behavioral_risk_a=behavior_a_risk,
            behavioral_risk_b=behavior_b_risk,
            behavioral_signatures_extracted=False,

            fusion_decision=fusion_result.fusion_decision,
            fusion_risk_score=fusion_result.fusion_risk_score,
            fusion_risk_level=fusion_result.fusion_risk_level,
            fusion_opposing_detected=(
                fusion_result.opposing_behavior_detected
            ),
            fusion_shared_tags=fusion_result.shared_behavior_tags,
            fusion_reasoning=fusion_result.reasoning,

            governance_action=risk_result.action,

            pipeline_complete=True,
            pipeline_errors=[],
        )

    # =====================================================
    # BULK ANALYSIS
    # =====================================================

    def analyze_function_pairs_batch(
        self,
        pairs: List[Dict],
    ) -> List[PipelineResult]:
        """
        Run analyze_function_pair on multiple pairs.

        Each dict in pairs must have keys:
            file_path, function_a, function_b
        Optional V2.2 key:
            file_path_b (for cross-file pairs)
        """

        results: List[PipelineResult] = []

        for pair in pairs:
            result = self.analyze_function_pair(
                file_path=pair["file_path"],
                function_a=pair["function_a"],
                function_b=pair["function_b"],
                file_path_b=pair.get("file_path_b"),
            )
            results.append(result)

        return results

    # =====================================================
    # INTERNAL HELPERS
    # =====================================================

    def _find_signature(self, signatures, function_name):
        """
        Find a behavioral signature by exact name or by qualified
        ClassName.method name.
        """
        for sig in signatures:
            if sig.function_name == function_name:
                return sig
        # Also try suffix match for class methods
        for sig in signatures:
            if sig.function_name.endswith("." + function_name):
                return sig
        return None

    def _extract_function_code(
        self,
        file_path: str,
        function_name: str,
    ) -> str:
        """
        Extract the source code of a named function from a file.
        Returns empty string if not found or on parse error.
        """
        try:
            source = Path(file_path).read_text(
                encoding="utf-8",
                errors="ignore",
            )
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                ):
                    if node.name == function_name:
                        segment = ast.get_source_segment(source, node)
                        return segment or ""
        except Exception:
            return ""

        return ""

    def _reconcile_action(
    self,
    fusion_decision: str,
    raw_action: str,
    ) -> str:
        """
        Reconcile the risk engine's score-based action with the
        fusion engine's categorical decision.

        Rule: REVIEW and BLOCK decisions must never produce
        AUTO_APPLY. This prevents a low-score REVIEW from being
        silently auto-applied, which would defeat HITL gating.

        Mapping:
            SAFE   -> use raw_action as-is
            REVIEW -> AUTO_APPLY becomes BATCH_APPROVAL
            BLOCK  -> AUTO_APPLY becomes INDIVIDUAL_APPROVAL
        """

        if fusion_decision == "SAFE":
            return raw_action

        if raw_action == "AUTO_APPLY":
            if fusion_decision == "REVIEW":
                return "BATCH_APPROVAL"
            if fusion_decision == "BLOCK":
                return "INDIVIDUAL_APPROVAL"

        return raw_action

# =========================================================
# BACKWARD COMPATIBILITY ALIAS
# =========================================================
# Older code (v2_orchestrator.py, tests) imported
# IntelligenceOrchestrator. Keep the name working but make
# it point to the new class. The new name is more honest.

IntelligenceOrchestrator = DecisionOrchestrator


# =========================================================
# MANUAL TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("DECISION ORCHESTRATOR - MANUAL TEST")
    print("=" * 70)

    # Build a tiny fixture file to test on
    import tempfile

    fixture_source = '''
import os


def save_user_data(user_id, data):
    with open(f"users/{user_id}.json", "w") as f:
        f.write(data)
    return True


def store_user_data(user_id, data):
    with open(f"users/{user_id}.json", "w") as f:
        f.write(data)
    return True


def delete_temp_file(path):
    os.remove(path)
    return True
'''

    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8",
    )
    tmp.write(fixture_source)
    tmp.close()

    orchestrator = DecisionOrchestrator()

    # Test 1: real integration entry point
    print("\nTest 1: analyze_function_pair (REAL integration)")
    print("-" * 70)

    result_1 = orchestrator.analyze_function_pair(
        file_path=tmp.name,
        function_a="save_user_data",
        function_b="store_user_data",
    )

    print(f"  Semantic decision : {result_1.semantic_decision}")
    print(f"  Behavioral A tags : {result_1.behavioral_tags_a}")
    print(f"  Behavioral B tags : {result_1.behavioral_tags_b}")
    print(f"  Fusion decision   : {result_1.fusion_decision}")
    print(f"  Fusion risk       : {result_1.fusion_risk_level}")
    print(f"  Governance action : {result_1.governance_action}")
    print(f"  Pipeline complete : {result_1.pipeline_complete}")

    # Test 2: lower-level signal-based method
    print("\nTest 2: analyze_signals (pre-computed signals)")
    print("-" * 70)

    result_2 = orchestrator.analyze_signals(
        function_a="save_user_data",
        function_b="store_user_data",
        behavior_a_tags=["FILE_WRITE"],
        behavior_b_tags=["FILE_WRITE"],
        behavior_a_risk="MEDIUM",
        behavior_b_risk="MEDIUM",
    )

    print(f"  Semantic decision : {result_2.semantic_decision}")
    print(f"  Fusion decision   : {result_2.fusion_decision}")
    print(f"  Fusion risk       : {result_2.fusion_risk_level}")
    print(f"  Governance action : {result_2.governance_action}")

    # Cleanup
    Path(tmp.name).unlink(missing_ok=True)
