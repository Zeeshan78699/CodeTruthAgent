"""
constructor_origin_tracker.py

Purpose:
Identify variables originating from class constructors.

Example:

cfg = Config()
cfg.parse()

Result:

cfg -> Config
"""

from typing import Dict, Any


class ConstructorOriginTracker:

    def __init__(
        self,
        assignment_table: Dict[str, Any],
        class_graph: Dict[str, Any]
    ):
        self.assignment_table = (
            assignment_table or {}
        )

        self.class_graph = (
            class_graph or {}
        )

    def build(self):

        results = {}

        for variable_key, origin in (
            self.assignment_table.items()
        ):

            if (
                origin.get("origin_type")
                != "call"
            ):
                continue

            candidate = origin.get(
                "origin_name"
            )

            #
            # Constructor if class exists
            #

            if candidate in self.class_graph:

                results[
                    variable_key
                ] = {

                    "constructor_class":
                        candidate,

                    "source":
                        "CONSTRUCTOR"
                }

        return results


def build_constructor_origins(
    assignment_table,
    class_graph
):

    tracker = ConstructorOriginTracker(
        assignment_table,
        class_graph
    )

    return tracker.build()