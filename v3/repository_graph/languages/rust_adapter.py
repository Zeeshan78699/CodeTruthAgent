"""
rust_adapter.py
NOT YET IMPLEMENTED. Registers .rs files so they are correctly
counted/categorized rather than silently ignored.

To implement: parse via `syn` (Rust's own parser crate, invoked through a
small Rust helper binary that dumps JSON) or a tree-sitter-rust grammar,
then map into the 6-graph shape - see base_adapter.py for the contract.
V3-004 -> fn items (incl. impl-block methods); V3-005 -> struct/enum/trait
definitions + trait bounds or `impl Trait for Type` as "bases";
V3-007/008 -> `use` statements - internal (crate::/self::/super::, similar
in spirit to D-007's relative-import handling) vs external (crates.io deps
from Cargo.toml); V3-009 -> call expressions and method calls, resolved via
module path + impl-block association.
"""

from .base_adapter import LanguageAdapter, empty_report


class RustAdapter(LanguageAdapter):
    language_name = "rust"
    file_extensions = {".rs"}

    def is_implemented(self) -> bool:
        return False

    def scan(self, repo_root: str, file_paths: list) -> dict:
        return empty_report()
