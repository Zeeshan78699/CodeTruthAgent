"""
return_flow_benchmark.py

Debug benchmark for ReturnFlowTrackerV2.
"""

import ast

from v3.repository_graph.languages.python_adapter import (
    PythonAdapter
)

from v3.repository_graph.tests.unresolved_pipeline.return_flow_tracker_v2 import (
    build_return_type_table_v2
)

REPO_PATH = r"C:\repos\v3\flask"


def collect_return_statistics(repo_path):

    stats = {}

    total_functions = 0
    total_returns = 0

    import pathlib

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

        for node in ast.walk(tree):

            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):

                total_functions += 1

                for child in ast.walk(
                    node
                ):

                    if not isinstance(
                        child,
                        ast.Return
                    ):
                        continue

                    total_returns += 1

                    value = child.value

                    if value is None:

                        pattern = "None"

                    else:

                        pattern = (
                            type(
                                value
                            ).__name__
                        )

                    stats[
                        pattern
                    ] = stats.get(
                        pattern,
                        0
                    ) + 1

    return (
        total_functions,
        total_returns,
        stats,
    )


def collect_return_call_candidates(
    repo_path
):

    candidates = {}

    import pathlib

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

        for node in ast.walk(tree):

            if not isinstance(
                node,
                ast.Return
            ):
                continue

            value = node.value

            if not isinstance(
                value,
                ast.Call
            ):
                continue

            if not isinstance(
                value.func,
                ast.Name
            ):
                continue

            name = value.func.id

            candidates[
                name
            ] = candidates.get(
                name,
                0
            ) + 1

    return candidates


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

    return_types = (
        build_return_type_table_v2(
            REPO_PATH,
            class_graph
        )
    )

    (
        total_functions,
        total_returns,
        stats,
    ) = collect_return_statistics(
        REPO_PATH
    )

    call_candidates = (
        collect_return_call_candidates(
            REPO_PATH
        )
    )

    print()
    print("=" * 80)
    print("RETURN FLOW TRACKER V2")
    print("=" * 80)

    print(
        f"Functions scanned: "
        f"{total_functions:,}"
    )

    print(
        f"Return statements: "
        f"{total_returns:,}"
    )

    print(
        f"Return types proven: "
        f"{len(return_types):,}"
    )

    print()

    print(
        "RETURN PATTERN DISTRIBUTION"
    )

    print("=" * 80)

    for pattern, count in sorted(
        stats.items(),
        key=lambda x: x[1],
        reverse=True
    ):

        print(
            f"{pattern:<20} "
            f"{count:,}"
        )

    print("=" * 80)

    print()
    print("CLASS GRAPH DEBUG")
    print("=" * 80)

    print(
        f"class_graph type: "
        f"{type(class_graph)}"
    )

    if class_graph:

        first_key = next(
            iter(class_graph)
        )

        print()

        print("FIRST KEY")
        print("-" * 80)

        print(first_key)

        print()

        print("FIRST VALUE TYPE")
        print("-" * 80)

        print(
            type(
                class_graph[
                    first_key
                ]
            )
        )

        print()

        print("FIRST VALUE")
        print("-" * 80)

        print(
            class_graph[
                first_key
            ]
        )

    else:

        print(
            "class_graph is empty"
        )

    print("=" * 80)

    print()
    

    print("NON-EMPTY CLASS MODULES")
    print("=" * 80)

    non_empty = 0

    for module_name, classes in class_graph.items():

        if classes:

            print(module_name)
            print(classes)
            print("-" * 40)

            non_empty += 1

        if non_empty >= 20:
            break

    print()

    print(
        f"Non-empty modules found: "
        f"{non_empty}"
    )

    print("=" * 80)

    print()
    
    print("TOP RETURN CALLS")
    print("=" * 80)

    for name, count in sorted(
        call_candidates.items(),
        key=lambda x: x[1],
        reverse=True
    )[:30]:

        marker = ""

        if name in class_graph:

            marker = "MATCH"

        print(
            f"{name:<40}"
            f"{count:<10}"
            f"{marker}"
        )

    print("=" * 80)

    if return_types:

        print()
        print("PROVEN RETURNS")
        print("=" * 80)

        for fn, typ in list(
            return_types.items()
        )[:30]:

            print(
                f"{fn} -> {typ}"
            )


if __name__ == "__main__":

    main()