"""
return_flow_tracker.py

Purpose:
Build a deterministic function return-type table.

Examples:

def create_app():
    return Flask()

Result:

{
    "create_app": "Flask"
}

Truth Boundary:
- Explicit return statements only
- Explicit constructor returns only
- No guessing
"""

import ast
from pathlib import Path
from typing import Dict, Any


class ReturnFlowTracker:

    def __init__(
        self,
        repo_root: str,
        class_graph: Dict[str, Any]
    ):
        self.repo_root = Path(
            repo_root
        )

        self.class_graph = (
            class_graph or {}
        )

        self.return_type_table = {}

    def _process_function(
        self,
        function_node
    ):

        function_name = (
            function_node.name
        )

        return_types = set()

        for node in ast.walk(
            function_node
        ):

            if not isinstance(
                node,
                ast.Return
            ):
                continue

            value = node.value

            #
            # return Flask()
            #

            if (
                isinstance(
                    value,
                    ast.Call
                )
                and isinstance(
                    value.func,
                    ast.Name
                )
            ):

                candidate = (
                    value.func.id
                )

                if (
                    candidate
                    in self.class_graph
                ):

                    return_types.add(
                        candidate
                    )

        #
        # Only accept if exactly one
        # proven return type exists
        #

        if len(return_types) == 1:

            self.return_type_table[
                function_name
            ] = next(
                iter(return_types)
            )

    def _scan_file(
        self,
        filepath: Path
    ):

        try:

            source = filepath.read_text(
                encoding="utf-8"
            )

            tree = ast.parse(
                source
            )

        except Exception:
            return

        for node in ast.walk(
            tree
        ):

            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):

                self._process_function(
                    node
                )

    def build(self):

        for py_file in (
            self.repo_root.rglob(
                "*.py"
            )
        ):

            self._scan_file(
                py_file
            )

        return self.return_type_table


def build_return_type_table(
    repo_root: str,
    class_graph: Dict[str, Any]
):

    tracker = ReturnFlowTracker(
        repo_root,
        class_graph
    )

    return tracker.build()