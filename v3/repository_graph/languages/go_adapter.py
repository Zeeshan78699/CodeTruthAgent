"""
go_adapter.py
NOT YET IMPLEMENTED. Registers .go files so they are correctly
counted/categorized rather than silently ignored.

To implement: Go ships its own AST package (go/ast, go/parser) - the
cleanest path is a small Go helper binary/script invoked as a subprocess
that dumps function/type/import info as JSON, which this adapter then maps
into the 6-graph shape - see base_adapter.py for the contract.
V3-004 -> func declarations (incl. methods via receiver types);
V3-005 -> struct types + interface embedding as "bases";
V3-007/008 -> import paths - internal (module path prefix from go.mod) vs
external (everything else); V3-009 -> call expressions, resolved via
package.Function or receiver.Method naming.
"""

from .base_adapter import LanguageAdapter, empty_report


class GoAdapter(LanguageAdapter):
    language_name = "go"
    file_extensions = {".go"}

    def is_implemented(self) -> bool:
        return False

    def scan(self, repo_root: str, file_paths: list) -> dict:
        return empty_report()
