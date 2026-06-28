"""
test_unresolved_resolution_pipeline.py

Experimental unresolved resolution benchmark.

Purpose:
Run unresolved analysis pipeline against a real repository.

Current Target:
Flask

Future Targets:
FastAPI
Odoo

This file does NOT modify Module 2.
It only consumes Module 2 output.
"""

import json
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from v3.repository_graph.languages.python_adapter import (
    PythonAdapter
)

from v3.repository_graph.tests.unresolved_pipeline.resolution_pipeline import (
    run_resolution_pipeline,
)

from v3.repository_graph.tests.unresolved_pipeline.report_generator import (
    generate_report,
)

# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------

REPO_PATH = r"C:\repos\v3\flask"

OUTPUT_DIR = (
    r"v3\outputs\unresolved_pipeline"
)

# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------


def extract_unresolved_entries(report):

    print("\nREPORT KEYS")
    print("=" * 80)

    if isinstance(report, dict):
        print(list(report.keys()))

    print("=" * 80)

    unresolved = report.get(
        "unresolved",
        []
    )

    print(
        f"\nUNRESOLVED TYPE: "
        f"{type(unresolved)}"
    )

    try:
        print(
            f"UNRESOLVED COUNT: "
            f"{len(unresolved)}"
        )
    except Exception:
        print(
            "UNRESOLVED COUNT: "
            "unable to determine"
        )

    return unresolved


def extract_return_type_table(report):

    value = report.get(
        "return_type_table",
        {}
    )

    print(
        "\nRETURN TYPE TABLE TYPE:",
        type(value)
    )

    return value


def extract_class_graph(report):

    value = report.get(
        "class_graph",
        {}
    )

    print(
        "\nCLASS GRAPH TYPE:",
        type(value)
    )

    return value


# ------------------------------------------------------------------
# MAIN TEST
# ------------------------------------------------------------------


def test_flask_unresolved_pipeline():

    print()
    print("=" * 80)
    print("FLASK UNRESOLVED PIPELINE")
    print("=" * 80)

    adapter = PythonAdapter()

    report = adapter.scan(
        repo_root=REPO_PATH,
        file_paths=[]
    )

    print("\nRAW REPORT TYPE")
    print(type(report))

    unresolved_entries = (
        extract_unresolved_entries(
            report
        )
    )

    return_type_table = (
        extract_return_type_table(
            report
        )
    )

    class_graph = (
        extract_class_graph(
            report
        )
    )

    results = run_resolution_pipeline(
        unresolved_entries=
            unresolved_entries,

        return_type_table=
            return_type_table,

        class_graph=
            class_graph,
    )

    report_file = generate_report(
        repo_name="flask",
        pipeline_results=results,
        output_dir=OUTPUT_DIR,
    )

    print()
    print(
        f"Report saved: {report_file}"
    )

    print()
    print("PIPELINE RESULTS")
    print("=" * 80)

    print(
        json.dumps(
            results,
            indent=2,
            default=str
        )[:10000]
    )

    print("=" * 80)

    assert results is not None
    assert "final" in results


if __name__ == "__main__":

    test_flask_unresolved_pipeline()