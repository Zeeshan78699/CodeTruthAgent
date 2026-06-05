"""
CodeTruth Agent V2
Full Orchestration Integration Test

Objective:
Validate the FULL V2 orchestration pipeline.

This is NOT autonomous repository mutation.

This is:
SAFE
DETERMINISTIC
EXPLAINABLE
ROLLBACK-GOVERNED
repository intelligence orchestration.
"""

from pathlib import Path
import json
import sys
import os

# =========================================================
# PROJECT ROOT FIX
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)

# =========================================================
# IMPORT V2 COMPONENTS
# =========================================================

from ai.repository_graph_engine import (
    RepositoryGraphEngine
)

from ai.behavioral_signature_engine import (
    BehavioralSignatureEngine
)

from ai.semantic_decision_engine import (
    SemanticDecisionEngine
)

from validation.syntax_validator import (
    SyntaxValidator
)

from validation.rollback_manager import (
    RollbackManager
)

from memory.memory_store_v2 import (
    MemoryStoreV2
)

from reporting.report_generator import (
    ReportGenerator
)

# =========================================================
# CONFIGURATION
# =========================================================

PROJECT_ROOT = Path.cwd()

TARGET_FILE = "main_v2.py"

REPORT_OUTPUT = (
    PROJECT_ROOT
    / "reports"
    / "v2_orchestrator_report.json"
)

# =====================================================
# BEHAVIORAL-SEMANTIC FUSION LAYER
# =====================================================

def combine_decision(
    semantic_result,
    behavioral_a,
    behavioral_b
):

    """
    Combine semantic reasoning
    with behavioral contradiction analysis.
    """

    opposing_pairs = {

        (
            "BACKUP_OPERATION",
            "RECOVERY_OPERATION"
        ),

        (
            "FILE_WRITE",
            "DELETE_OPERATION"
        ),

        (
            "AUTH_OPERATION",
            "DELETE_OPERATION"
        ),

        (
            "STATE_MUTATION",
            "RECOVERY_OPERATION"
        )
    }

    behaviors_a = set(
        behavioral_a["behaviors"]
    )

    behaviors_b = set(
        behavioral_b["behaviors"]
    )

    # =================================================
    # OPPOSING BEHAVIOR DETECTION
    # =================================================

    for op_a, op_b in opposing_pairs:

        if (
            (
                op_a in behaviors_a
                and
                op_b in behaviors_b
            )
            or
            (
                op_b in behaviors_a
                and
                op_a in behaviors_b
            )
        ):

            return {

                "decision":
                "BLOCK",

                "reason":
                (
                    f"Opposing operations detected: "
                    f"{op_a} vs {op_b}"
                ),

                "risk_level":
                "HIGH"
            }

    # =================================================
    # FALLBACK TO SEMANTIC ENGINE
    # =================================================

    return {

        "decision":
        semantic_result["decision"],

        "reason":
        semantic_result["reasoning"],

        "risk_level":
        semantic_result["risk_level"]
    }

# =========================================================
# MAIN PIPELINE
# =========================================================

def run_v2_orchestrator():

    print("=" * 70)
    print("CODETRUTH V2 - FULL ORCHESTRATION TEST")
    print("=" * 70)

    final_report = {}

    # =====================================================
    # STEP 1 - REPOSITORY GRAPH
    # =====================================================

    print("\n[1] Repository Intelligence")

    repository_engine = (
        RepositoryGraphEngine(
            str(PROJECT_ROOT)
        )
    )

    repository_graph = (
        repository_engine.build_graph()
    )

    repository_summary = {
        "files_scanned":
        len(repository_graph.files),

        "functions_found":
        sum(
            len(f.functions)
            for f in repository_graph.files.values()
        ),

        "classes_found":
        sum(
            len(f.classes)
            for f in repository_graph.files.values()
        ),

        "dependency_links":
        sum(
            len(v)
            for v in repository_graph.dependency_map.values()
        )
    }

    print(repository_summary)

    final_report[
        "repository_intelligence"
    ] = repository_summary


    # =====================================================
    # STEP 2 - BEHAVIORAL ANALYSIS
    # =====================================================

    print("\n[2] Behavioral Intelligence")

    behavioral_engine = (
        BehavioralSignatureEngine()
    )

    #rollback_file = (
    #    PROJECT_ROOT
    #    / "validation"
    #    / "rollback_manager.py"
    #)
    
    rollback_file = (
        PROJECT_ROOT
        / "memory"
        / "memory_store_v2.py"
    )

    rollback_signatures = (
        behavioral_engine.analyze_file(
            str(rollback_file)
        )
    )

    behavioral_output = []

    behavior_map = {}

    for signature in rollback_signatures:

        entry = {

            "function":
            signature.function_name,

            "risk":
            signature.risk_level,

            "behaviors":
            signature.behavioral_tags,

            "side_effects":
            signature.side_effects,

            "object_creations":
            signature.object_creations
        }

        behavioral_output.append(entry)

        behavior_map[
            signature.function_name
        ] = entry

    print(
        f"Behavioral signatures: "
        f"{len(behavioral_output)}"
    )

    final_report[
        "behavioral_intelligence"
    ] = behavioral_output
    
    # =====================================================
    # STEP 3 - SEMANTIC DECISION
    # =====================================================

    print("\n[3] Semantic Decision Intelligence")

    semantic_engine = (
        SemanticDecisionEngine()
    )

    semantic_result = (
        semantic_engine.analyze_change(
            
            function_a=
            "get_memory",

            function_b=
            "_load_memory",

            docstring_a=
            "Get memory data safely",

            docstring_b=
            "Load memory data safely"
        )
    )

    # =====================================================
    # BEHAVIORAL-SEMANTIC FUSION
    # =====================================================
    
    behavioral_a = next(
        (
            value
            for key, value in behavior_map.items()
            if key.endswith("get_memory")
        ),
        {
            "behaviors": []
        }
    )

    behavioral_b = next(
        (
            value
            for key, value in behavior_map.items()
            if key.endswith("_load_memory")
        ),
        {
            "behaviors": []
        }
    )

    fusion_result = combine_decision(
        semantic_result,
        behavioral_a,
        behavioral_b
    )

    print(
        f"Semantic Decision: "
        f"{semantic_result['decision']}"
    )

    print(
        f"Fusion Decision: "
        f"{fusion_result['decision']}"
    )

    final_report[
        "semantic_decision"
    ] = semantic_result

    final_report[
        "behavioral_semantic_fusion"
    ] = fusion_result

    # =====================================================
    # STEP 4 - SYNTAX VALIDATION
    # =====================================================

    print("\n[4] Syntax Validation")

    target_path = (
        PROJECT_ROOT
        / TARGET_FILE
    )

    source_code = (
        target_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )
    )

    syntax_result = (
        SyntaxValidator
        .validate_python_code(
            source_code
        )
    )

    print(syntax_result)

    final_report[
        "syntax_validation"
    ] = syntax_result

    # =====================================================
    # STEP 5 - ROLLBACK SAFETY
    # =====================================================

    print("\n[5] Rollback Protection")

    rollback_result = (
        RollbackManager.create_backup(
            TARGET_FILE
        )
    )

    print(rollback_result)

    final_report[
        "rollback_safety"
    ] = rollback_result

    # =====================================================
    # STEP 6 - MEMORY GOVERNANCE
    # =====================================================

    print("\n[6] Memory Governance")

    memory = MemoryStoreV2()

    memory_result = (
        memory.store_approved_decision({
            "decision":
            fusion_result["decision"],

            "risk_level":
            fusion_result["risk_level"]
        })
    )

    print(memory_result)

    final_report[
        "memory_governance"
    ] = memory_result

    # =====================================================
    # STEP 7 - FINAL GOVERNANCE DECISION
    # =====================================================

    print("\n[7] Final Governance Decision")
    
    final_decision = (
        fusion_result["decision"]
    )

    if not syntax_result["valid"]:

        final_decision = "BLOCK"

    governance_summary = {

        "final_decision":
        final_decision,

        "semantic_decision":
        fusion_result["decision"],

        "semantic_confidence":
        semantic_result["confidence"],

        "syntax_valid":
        syntax_result["valid"],

        "rollback_ready":
        rollback_result["success"],

        "memory_recorded":
        memory_result["success"]
    }

    print(governance_summary)

    final_report[
        "governance_summary"
    ] = governance_summary

    # =====================================================
    # STEP 8 - REPORT GENERATION
    # =====================================================

    print("\n[8] Report Generation")

    REPORT_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        REPORT_OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            final_report,
            file,
            indent=4
        )

    ReportGenerator.generate_console_report(
        final_report
    )

    print(
        "\nReport exported to:"
    )

    print(REPORT_OUTPUT)

    # =====================================================
    # FINAL STATUS
    # =====================================================

    print("\n" + "=" * 70)
    print("V2 ORCHESTRATION COMPLETED SUCCESSFULLY")
    print("=" * 70)


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    run_v2_orchestrator()