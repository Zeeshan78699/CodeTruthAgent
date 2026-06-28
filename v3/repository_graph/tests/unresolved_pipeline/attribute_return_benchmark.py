"""
attribute_return_benchmark.py

Benchmark for AttributeReturnResolver.

Measures:

- Attribute returns found
- Attribute returns resolved
- Resolution rate

Target patterns:

return self.app
return self.response_class
return self.blueprint
return self.config
"""

import ast

from v3.repository_graph.languages.python_adapter import (
    PythonAdapter
)

from v3.repository_graph.tests.unresolved_pipeline.return_flow_tracker_v2 import (
    ReturnFlowTrackerV2
)

from v3.repository_graph.tests.unresolved_pipeline.attribute_return_resolver import (
    build_attribute_returns
)

REPO_PATH = r"C:\repos\v3\flask"


def count_attribute_returns(
    repo_path
):

    import pathlib

    total = 0

    for py_file in pathlib.Path(
        repo_path
    ).rglob("*.py"):

        try:

            source = py_file.read_text(
                encoding="utf-8"
            )

            tree = ast.parse(
                source
            )

        except Exception:
            continue

        for node in ast.walk(
            tree
        ):

            if not isinstance(
                node,
                ast.Return
            ):
                continue

            value = node.value

            if not isinstance(
                value,
                ast.Attribute
            ):
                continue

            total += 1

    return total


def main():

    adapter = PythonAdapter()

    report = adapter.scan(
        repo_root=REPO_PATH,
        file_paths=[]
    )

    class_graph = report.get(
        "class_graph",
        {}
    )

    tracker = (
        ReturnFlowTrackerV2(
            REPO_PATH,
            class_graph
        )
    )

    class_index = (
        tracker.class_name_index
    )

    resolved = (
        build_attribute_returns(
            REPO_PATH,
            class_index
        )
    )

    attribute_count = (
        count_attribute_returns(
            REPO_PATH
        )
    )

    resolved_count = (
        len(resolved)
    )

    remaining = max(
        0,
        attribute_count
        - resolved_count
    )

    reduction = 0.0

    if attribute_count:

        reduction = round(
            (
                resolved_count
                / attribute_count
            ) * 100,
            2
        )

    print("=" * 80)
    print("ATTRIBUTE RETURN BENCHMARK")
    print("=" * 80)

    print(
        f"Attribute returns: "
        f"{attribute_count:,}"
    )

    print(
        f"Resolved: "
        f"{resolved_count:,}"
    )

    print(
        f"Remaining: "
        f"{remaining:,}"
    )

    print(
        f"Resolution rate: "
        f"{reduction}%"
    )

    print("=" * 80)

    if resolved:

        print()
        print(
            "EXAMPLES"
        )

        print("=" * 80)

        for fn, typ in list(
            resolved.items()
        )[:30]:

            print(
                f"{fn} -> {typ}"
            )

        print("=" * 80)
        
    #
    # DEBUG ATTRIBUTE PATTERNS
    #

    print()
    print("ATTRIBUTE RETURN EXAMPLES")
    print("=" * 80)

    shown = 0

    import pathlib

    for py_file in pathlib.Path(
        REPO_PATH
    ).rglob("*.py"):

        try:

            source = py_file.read_text(
            encoding="utf-8"
        )

            tree = ast.parse(
                source
        )

        except Exception:
            continue

        for node in ast.walk(
            tree
        ):

            if not isinstance(
                node,
                ast.Return
            ):
                continue

            if not isinstance(
                node.value,
                ast.Attribute
            ):
                continue

            print(
                ast.dump(
                    node.value,
                    indent=2
                )
            )

            print("-" * 80)

            shown += 1

            if shown >= 20:
                break

        if shown >= 20:
            break


if __name__ == "__main__":

    main()