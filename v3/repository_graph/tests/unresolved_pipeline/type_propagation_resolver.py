"""
type_propagation_resolver.py

Experimental Module 2.5 validation harness.

Purpose:
Attempt deterministic resolution of unresolved attribute calls using:

1. Return Type Table
2. Assignment Propagation
3. Constructor Tracking

Truth Boundary:
- Resolve only when type is proven
- Ambiguous remains unresolved
- No guessing
"""

from typing import Any, Dict, List, Optional


class TypePropagationResolver:
    """
    Resolves attribute_call entries using known type information.
    """

    def __init__(self, return_type_table: Dict[str, str]):
        self.return_type_table = return_type_table or {}

    def resolve_entry(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Example unresolved:

        service = create_service()
        service.run()

        If:
        create_service -> PaymentService

        Then:
        service.run -> PaymentService.run
        """

        source_function = entry.get("source_function")

        if not source_function:
            return None

        inferred_type = self.return_type_table.get(source_function)

        if not inferred_type:
            return None

        return {
            "resolved": True,
            "resolver": "type_propagation",
            "resolution_source": "RETURN_TYPE_TABLE",
            "inferred_type": inferred_type,
            "original_entry": entry,
        }

    def resolve_batch(
        self,
        unresolved_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        resolved = []
        remaining = []

        for entry in unresolved_entries:

            if entry.get("pattern") != "attribute_call":
                remaining.append(entry)
                continue

            result = self.resolve_entry(entry)

            if result:
                resolved.append(result)
            else:
                remaining.append(entry)

        return {
            "resolver": "type_propagation",
            "resolved_count": len(resolved),
            "remaining_count": len(remaining),
            "resolved_entries": resolved,
            "remaining_entries": remaining,
        }


def run_type_propagation(
    unresolved_entries: List[Dict[str, Any]],
    return_type_table: Dict[str, str]
) -> Dict[str, Any]:

    resolver = TypePropagationResolver(return_type_table)

    return resolver.resolve_batch(
        unresolved_entries
    )