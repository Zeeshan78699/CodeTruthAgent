"""
TC_V2_FINAL_002 — Dependency Inspection Validation

Title:
Are the Detected Dependencies Truly Cross-File?

Description:
This diagnostic validates whether CodeTruth Agent V2
is detecting REAL cross-file repository cognition
or only within-file relationships.

Objective:
Validate true repository-wide dependency cognition.

Expected Result:
Cross-file dependency edges detected.

Category:
Repository Dependency Cognition Validation
"""

from collections import Counter
from pathlib import Path
import json

from ai.repository_graph_engine import (
    RepositoryGraphEngine
)


# =========================================================
# CONFIGURATION
# =========================================================

REPO_ROOT = Path(
    r"C:\AI_Project\CodeTruthAgent"
)

OUTPUT_DIR = Path(
    r"tests/output/v2/dependency_inspection_reports"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

TEXT_OUTPUT = (
    OUTPUT_DIR /
    "inspect_dependencies_output.txt"
)

JSON_OUTPUT = (
    OUTPUT_DIR /
    "inspect_dependencies_report.json"
)

# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 70)
    print(
        "TC_V2_FINAL_002 — Dependency Inspection Validation"
    )
    print("=" * 70)

    # -----------------------------------------------------
    # STEP 1 — Build Repository Graph
    # -----------------------------------------------------

    graph_engine = RepositoryGraphEngine(
        repo_root=str(REPO_ROOT)
    )

    graph = graph_engine.build_graph()
    
    print("\n[DEBUG] function_index sample:")

    print("\n[DEBUG] function_index type:")
    print(type(graph.function_index))

    print("\n[DEBUG] function_index value:")
    print(graph.function_index)


    print("\n[DEBUG] function.calls sample:")

    for file_path, file_node in graph.files.items():

        for function in file_node.functions:

            if function.calls:

                print(
                    f"\nfunction={function.name!r}"
                )

                print(
                    f"calls={function.calls[:5]}"
                )

                print(
                    f"call_type="
                    f"{type(function.calls[0]).__name__}"
                )

                break

        break

    # -----------------------------------------------------
    # STEP 2 — Extract Dependency Edges
    # -----------------------------------------------------

    dependency_edges = []

    for file_path, file_node in graph.files.items():

        for function in file_node.functions:

            for called_function in function.calls:

                resolved = False
                
                for (
                    indexed_function,
                    indexed_files
                ) in graph.function_index.items():

                    if called_function == indexed_function:

                        dependency_edges.append({

                            "from_file":
                            file_path,

                            "from_func":
                            function.name,

                            "to_file":
                            indexed_files[0],

                            "to_func":
                            called_function
                        })

                        resolved = True

                        break

                # -----------------------------------------
                # Unresolved Dependency
                # -----------------------------------------

                if not resolved:

                    dependency_edges.append({

                        "from_file":
                            file_path,

                        "from_func":
                            function.name,

                        "to_file":
                            None,

                        "to_func":
                            called_function
                    })

    # -----------------------------------------------------
    # STEP 3 — Dependency Classification
    # -----------------------------------------------------

    within_file = 0
    cross_file = 0
    unresolved = 0

    cross_examples = []
    within_examples = []

    for edge in dependency_edges:

        from_file = edge["from_file"]
        to_file = edge["to_file"]

        if to_file is None:

            unresolved += 1
            continue

        if from_file == to_file:

            within_file += 1

            if len(within_examples) < 5:
                within_examples.append(edge)

        else:

            cross_file += 1

            if len(cross_examples) < 5:
                cross_examples.append(edge)

    # -----------------------------------------------------
    # STEP 4 — Coverage
    # -----------------------------------------------------

    files_with_outgoing = Counter()

    for edge in dependency_edges:

        if edge["from_file"]:

            files_with_outgoing[
                edge["from_file"]
            ] += 1

    # -----------------------------------------------------
    # STEP 5 — FINAL REPORT
    # -----------------------------------------------------

    total_edges = len(dependency_edges)

    cross_ratio = round(
        (
            cross_file / total_edges
            if total_edges
            else 0
        ),
        2
    )

    governance_decision = (
        "PASS"
        if cross_file > 0
        else "FAIL"
    )

    final_report = {

        "test_case":
            "TC_V2_FINAL_002_DEPENDENCY_INSPECTION",

        "repository_root":
            str(REPO_ROOT),

        "total_dependency_edges":
            total_edges,

        "within_file_edges":
            within_file,

        "cross_file_edges":
            cross_file,

        "unresolved_edges":
            unresolved,

        "cross_file_ratio":
            cross_ratio,

        "files_with_dependencies":
            len(files_with_outgoing),

        "governance_decision":
            governance_decision,

        "cross_file_examples":
            cross_examples,

        "within_file_examples":
            within_examples
    }

    # -----------------------------------------------------
    # STEP 6 — DISPLAY RESULTS
    # -----------------------------------------------------

    print("\n[Dependency Statistics]")

    print(
        json.dumps(
            {
                "total_edges":
                    total_edges,
                "within_file":
                    within_file,
                "cross_file":
                    cross_file,
                "unresolved":
                    unresolved,
                "cross_ratio":
                    cross_ratio
            },
            indent=4
        )
    )

    print("\n[Coverage]")
    print(
        f"Files with dependencies: "
        f"{len(files_with_outgoing)}"
    )

    print("\n[Governance Decision]")
    print(governance_decision)

    # -----------------------------------------------------
    # STEP 7 — SAVE REPORTS
    # -----------------------------------------------------

    with open(
        JSON_OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            final_report,
            f,
            indent=4
        )

    with open(
        TEXT_OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            json.dumps(
                final_report,
                indent=4
            )
        )

    print("\n[Reports Generated]")
    print(OUTPUT_DIR)


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    main()