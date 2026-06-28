"""
property_type_table_builder.py

Experimental Module 2.5 validation harness.

Purpose:
Build a deterministic property type table.

Example:

class Flask:

    response_class = Response

Produces:

{
    "response_class": "Response"
}

Truth Boundary:
- Only explicit assignments
- Only proven class references
- No guessing
"""

import ast
from pathlib import Path
from typing import Dict, Any


class PropertyTypeTableBuilder:

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

        self.property_type_table = {}

    def _is_known_class(
        self,
        class_name: str
    ) -> bool:

        return (
            class_name
            in self.class_graph
        )

    def _process_class(
        self,
        node: ast.ClassDef
    ):

        for item in node.body:

            if not isinstance(
                item,
                ast.Assign
            ):
                continue

            if len(item.targets) != 1:
                continue

            target = item.targets[0]

            if not isinstance(
                target,
                ast.Name
            ):
                continue

            property_name = target.id

            value = item.value

            #
            # response_class = Response
            #

            if isinstance(
                value,
                ast.Name
            ):

                candidate_type = (
                    value.id
                )

                if self._is_known_class(
                    candidate_type
                ):

                    self.property_type_table[
                        property_name
                    ] = candidate_type

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

        for node in ast.walk(tree):

            if isinstance(
                node,
                ast.ClassDef
            ):

                self._process_class(
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

        return self.property_type_table


def build_property_type_table(
    repo_root: str,
    class_graph: Dict[str, Any]
):

    builder = (
        PropertyTypeTableBuilder(
            repo_root,
            class_graph
        )
    )

    return builder.build()