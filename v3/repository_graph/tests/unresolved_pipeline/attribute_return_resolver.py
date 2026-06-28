"""
attribute_return_resolver.py

Purpose:
Resolve deterministic attribute-based returns.

Examples:

return self.response_class
return self.app
return self.blueprint
return self.config

Truth Boundary:
- Only explicit assignments
- Only proven class names
- No guessing
"""

import ast
from pathlib import Path
from typing import Dict


class AttributeReturnResolver:

    def __init__(
        self,
        repo_root: str,
        class_name_index
    ):
        self.repo_root = Path(
            repo_root
        )

        self.class_name_index = (
            class_name_index
        )

        self.resolved = {}

    # --------------------------------------------------
    # Collect self assignments
    # --------------------------------------------------

    def _collect_self_assignments(
        self,
        function_node
    ):

        assignments = {}

        for node in ast.walk(
            function_node
        ):

            if not isinstance(
                node,
                ast.Assign
            ):
                continue

            if len(node.targets) != 1:
                continue

            target = node.targets[0]

            #
            # self.x = Flask()
            #

            if not isinstance(
                target,
                ast.Attribute
            ):
                continue

            if not isinstance(
                target.value,
                ast.Name
            ):
                continue

            if (
                target.value.id
                != "self"
            ):
                continue

            assignments[
                target.attr
            ] = node.value

        return assignments

    # --------------------------------------------------
    # Resolve constructor call
    # --------------------------------------------------

    def _resolve_call(
        self,
        value
    ):

        if not isinstance(
            value,
            ast.Call
        ):
            return None

        if not isinstance(
            value.func,
            ast.Name
        ):
            return None

        candidate = (
            value.func.id
        )

        if (
            candidate
            in self.class_name_index
        ):
            return candidate

        return None

    # --------------------------------------------------
    # Process function
    # --------------------------------------------------

    def _process_function(
        self,
        function_node
    ):

        assignments = (
            self._collect_self_assignments(
                function_node
            )
        )

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
            # return self.x
            #

            if not isinstance(
                value,
                ast.Attribute
            ):
                continue

            if not isinstance(
                value.value,
                ast.Name
            ):
                continue

            if (
                value.value.id
                != "self"
            ):
                continue

            attr_name = (
                value.attr
            )

            origin = assignments.get(
                attr_name
            )

            resolved = (
                self._resolve_call(
                    origin
                )
            )

            if resolved:

                self.resolved[
                    function_node.name
                ] = resolved

    # --------------------------------------------------
    # Scan file
    # --------------------------------------------------

    def _scan_file(
        self,
        filepath
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
                )
            ):

                self._process_function(
                    node
                )

    # --------------------------------------------------
    # Build
    # --------------------------------------------------

    def build(self):

        for py_file in (
            self.repo_root.rglob(
                "*.py"
            )
        ):

            self._scan_file(
                py_file
            )

        return self.resolved


def build_attribute_returns(
    repo_root,
    class_name_index
):

    resolver = (
        AttributeReturnResolver(
            repo_root,
            class_name_index
        )
    )

    return resolver.build()