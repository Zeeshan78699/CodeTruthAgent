"""
CodeTruth Agent V2
Behavioral Signature Engine

Objective:
Provide deterministic behavioral intelligence for repository analysis.

This engine detects:
- FILE_WRITE
- FILE_READ
- DELETE_OPERATION
- NETWORK_OPERATION
- AUTH_OPERATION
- DATABASE_OPERATION
- MEMORY_OPERATION
- BACKUP_OPERATION
- RECOVERY_OPERATION
- OBJECT_CREATION
- STATE_MUTATION
- HIGH_IMPACT operations

This is NOT AI generation.
This is deterministic behavioral classification.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set


# ---------------------------------------------------------
# Behavioral Categories
# ---------------------------------------------------------

FILE_WRITE_CALLS = {
    "write",
    "writelines",
    "dump",
    "save",
    "copy",
    "copy2",
}

FILE_READ_CALLS = {
    "read",
    "readlines",
    "load",
    "open",
    "exists",
}

DELETE_CALLS = {
    "remove",
    "unlink",
    "delete",
    "rmdir",
}

NETWORK_CALLS = {
    "request",
    "post",
    "put",
    "socket",
    "send",
}

DATABASE_CALLS = {
    "execute",
    "commit",
    "rollback",
    "cursor",
    "connect",
}

AUTH_CALLS = {
    "authenticate",
    "authorize",
    "login",
    "logout",
    "token",
    "validate_user",
}

BACKUP_CALLS = {
    "create_backup",
    "backup",
}

RECOVERY_CALLS = {
    "restore_backup",
    "recover",
    "rollback",
}

MEMORY_CALLS = {
    "store_memory",
    "load_memory",
    "get_memory",
    "store_approved_decision",
}

STATE_MUTATION_CALLS = {
    "append",
    "extend",
    "insert",
    "update",
    "write",
    "save",
    "copy",
    "copy2",
}

HIGH_IMPACT_BEHAVIORS = {
    "DELETE_OPERATION",
    "AUTH_OPERATION",
    "DATABASE_OPERATION",
    "RECOVERY_OPERATION",
}


# ---------------------------------------------------------
# Data Models
# ---------------------------------------------------------

@dataclass
class BehavioralSignature:
    function_name: str
    file_path: str

    behavioral_tags: List[str]
    risk_level: str

    function_calls: List[str]
    method_calls: List[str]

    object_creations: List[str]
    side_effects: List[str]


# ---------------------------------------------------------
# Behavioral Signature Engine
# ---------------------------------------------------------

class BehavioralSignatureEngine:

    def __init__(self) -> None:
        pass

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------

    def analyze_file(self, file_path: str) -> List[BehavioralSignature]:
        """
        Analyze all functions/classes in a file.
        """

        path = Path(file_path)

        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
        except Exception:
            return []

        signatures: List[BehavioralSignature] = []

        class_index = self._extract_class_names(tree)

        for node in tree.body:

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                signatures.append(
                    self._analyze_function(
                        node=node,
                        file_path=str(path),
                        class_index=class_index,
                    )
                )

            elif isinstance(node, ast.ClassDef):

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):

                        qualified_name = f"{node.name}.{item.name}"

                        signatures.append(
                            self._analyze_function(
                                node=item,
                                file_path=str(path),
                                class_index=class_index,
                                qualified_name=qualified_name,
                            )
                        )

        return signatures

    def print_report(self, file_path: str) -> None:
        """
        Print readable behavioral report.
        """

        signatures = self.analyze_file(file_path)

        print("=" * 70)
        print("CODETRUTH V2 - BEHAVIORAL SIGNATURE REPORT")
        print("=" * 70)

        for sig in signatures:

            print(f"\nFUNCTION: {sig.function_name}")
            print(f"FILE: {sig.file_path}")

            print(f"RISK LEVEL: {sig.risk_level}")

            print(f"BEHAVIORS: {sig.behavioral_tags}")

            if sig.object_creations:
                print(f"OBJECT CREATIONS: {sig.object_creations}")

            if sig.side_effects:
                print(f"SIDE EFFECTS: {sig.side_effects}")

            if sig.function_calls:
                print(f"FUNCTION CALLS: {sig.function_calls}")

            if sig.method_calls:
                print(f"METHOD CALLS: {sig.method_calls}")

    # -----------------------------------------------------
    # Core Analysis
    # -----------------------------------------------------

    def _analyze_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: str,
        class_index: Set[str],
        qualified_name: Optional[str] = None,
    ) -> BehavioralSignature:

        function_calls: Set[str] = set()
        method_calls: Set[str] = set()

        object_creations: Set[str] = set()
        behavioral_tags: Set[str] = set()
        side_effects: Set[str] = set()
        
        # -------------------------------------------------
        # Classify function/method name itself
        # -------------------------------------------------

        function_base_name = node.name
        
        is_constructor = (
            function_base_name == "__init__"
        )

        if not is_constructor:
            self._classify_behavior(
                base_call=function_base_name,
                behavioral_tags=behavioral_tags,
                side_effects=side_effects,
            )

        for child in ast.walk(node):

            if isinstance(child, ast.Call):

                call_name = self._get_call_name(child)

                if not call_name:
                    continue

                base_call = call_name.split(".")[-1]

                # -----------------------------------------
                # Object Awareness Layer
                # -----------------------------------------

                if base_call in class_index:
                    object_creations.add(base_call)
                    behavioral_tags.add("OBJECT_CREATION")

                # -----------------------------------------
                # Method vs Function Call
                # -----------------------------------------

                if "." in call_name:
                    method_calls.add(call_name)
                else:
                    function_calls.add(call_name)

                # -----------------------------------------
                # Behavioral Classification
                # -----------------------------------------

                self._classify_behavior(
                    base_call=base_call,
                    behavioral_tags=behavioral_tags,
                    side_effects=side_effects,
                )

        risk_level = self._determine_risk(behavioral_tags)

        return BehavioralSignature(
            function_name=qualified_name or node.name,
            file_path=file_path,

            behavioral_tags=sorted(behavioral_tags),
            risk_level=risk_level,

            function_calls=sorted(function_calls),
            method_calls=sorted(method_calls),

            object_creations=sorted(object_creations),
            side_effects=sorted(side_effects),
        )

    # -----------------------------------------------------
    # Behavioral Classification
    # -----------------------------------------------------

    def _classify_behavior(
        self,
        base_call: str,
        behavioral_tags: Set[str],
        side_effects: Set[str],
    ) -> None:

        # FILE WRITE
        if base_call in FILE_WRITE_CALLS:
            behavioral_tags.add("FILE_WRITE")
            side_effects.add("PERSISTENT_STATE_CHANGE")

        # FILE READ
        if base_call in FILE_READ_CALLS:
            behavioral_tags.add("FILE_READ")

        # DELETE
        if base_call in DELETE_CALLS:
            behavioral_tags.add("DELETE_OPERATION")
            side_effects.add("DATA_REMOVAL")

        # NETWORK
        if base_call in NETWORK_CALLS:
            behavioral_tags.add("NETWORK_OPERATION")

        # DATABASE
        if base_call in DATABASE_CALLS:
            behavioral_tags.add("DATABASE_OPERATION")
            side_effects.add("DATABASE_STATE_CHANGE")

        # AUTH
        if base_call in AUTH_CALLS:
            behavioral_tags.add("AUTH_OPERATION")

        # BACKUP
        if base_call in BACKUP_CALLS:
            behavioral_tags.add("BACKUP_OPERATION")

        # RECOVERY
        if base_call in RECOVERY_CALLS:
            behavioral_tags.add("RECOVERY_OPERATION")

        # MEMORY
        if base_call in MEMORY_CALLS:
            behavioral_tags.add("MEMORY_OPERATION")

        # STATE MUTATION
        if base_call in STATE_MUTATION_CALLS:
            behavioral_tags.add("STATE_MUTATION")

    # -----------------------------------------------------
    # Risk Classification
    # -----------------------------------------------------

    def _determine_risk(self, behavioral_tags: Set[str]) -> str:

        if any(tag in HIGH_IMPACT_BEHAVIORS for tag in behavioral_tags):
            return "HIGH"

        if behavioral_tags:
            return "MEDIUM"

        return "LOW"

    # -----------------------------------------------------
    # Helpers
    # -----------------------------------------------------

    def _extract_class_names(self, tree: ast.AST) -> Set[str]:

        class_names: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_names.add(node.name)

        return class_names

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        return self._get_name(node.func)

    def _get_name(self, node: ast.AST) -> Optional[str]:

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):

            parent = self._get_name(node.value)

            if parent:
                return f"{parent}.{node.attr}"

            return node.attr

        if isinstance(node, ast.Call):
            return self._get_call_name(node)

        return None


# ---------------------------------------------------------
# Standalone Test Runner
# ---------------------------------------------------------

if __name__ == "__main__":

    target_file = "main_v2.py"

    engine = BehavioralSignatureEngine()
    engine.print_report(target_file)