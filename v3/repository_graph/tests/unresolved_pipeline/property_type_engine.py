from typing import Any, Dict, List, Optional


class PropertyTypeEngine:
    def __init__(self, extracted_facts, property_type_table, class_graph):
        self.extracted_facts = extracted_facts or []
        self.property_type_table = property_type_table or {}
        self.class_graph = class_graph or {}

    def _method_exists(self, class_name, method_name) -> bool:
        class_info = self.class_graph.get(class_name)
        if not class_info:
            return False
        methods = set(class_info.get("methods", []))
        return method_name in methods

    def resolve_fact(self, fact):
        """
        Original case this was designed for: self.X.method() - X is a
        property whose type is proven, and `method` is then looked up
        on that type. Requires both property_name and attribute_name.
        """
        property_name = fact.get("property_name")
        attribute_name = fact.get("attribute_name")
        if not property_name or not attribute_name:
            return None
        property_type = self.property_type_table.get(property_name)
        if not property_type:
            return None
        if not self._method_exists(property_type, attribute_name):
            return None
        return {"resolved": True, "resolver": "property_type_engine", "property_name": property_name,
                "property_type": property_type, "method_name": attribute_name,
                "resolution_source": "PROPERTY_TYPE_TABLE", "original_fact": fact}

    def resolve_self_method_fact(self, fact):
        """
        FIX: the real-world shape found in Flask is different from
        resolve_fact's case above - self.response_class(...) calls the
        property directly AS a constructor (since response_class =
        Response is a class reference, not an instance). There's no
        further attribute_name to look up: being in property_type_table
        at all is itself the complete proof needed - the call resolves
        directly to that class's constructor. No method existence
        check applies, since this isn't calling a method ON the
        property's type, it's calling the type itself.
        """
        property_name = fact.get("property_name")
        if not property_name:
            return None
        property_type = self.property_type_table.get(property_name)
        if not property_type:
            return None
        return {"resolved": True, "resolver": "property_type_engine", "property_name": property_name,
                "property_type": property_type, "resolution_source": "PROPERTY_TYPE_TABLE_DIRECT_CONSTRUCTOR",
                "original_fact": fact}

    def resolve_batch(self):
        resolved, remaining = [], []
        for fact in self.extracted_facts:
            if fact.get("pattern") == "attribute_call":
                result = self.resolve_fact(fact)
            elif fact.get("pattern") == "self_method_not_found":
                result = self.resolve_self_method_fact(fact)
            else:
                result = None
            if result:
                resolved.append(result)
            else:
                remaining.append(fact)
        return {"resolver": "property_type_engine", "resolved_count": len(resolved), "remaining_count": len(remaining),
                "resolved_entries": resolved, "remaining_entries": remaining}


def run_property_type_engine(extracted_facts, property_type_table, class_graph):
    return PropertyTypeEngine(extracted_facts, property_type_table, class_graph).resolve_batch()
