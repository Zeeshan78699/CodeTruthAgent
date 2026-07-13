"""
debug_assignment_trace.py

Directly instruments AssignmentChainBuilder to print EVERY call to
_record_assignment for target "state" within flask.sansio.blueprints
specifically - shows the exact order and values, to find out
definitively whether it's being called more than once (and what
overwrites what) or something else entirely.

    python v3\\repository_graph\\tests\\debug_assignment_trace.py C:\\repos\\v3\\flask
"""
import sys
from pathlib import Path


def _find_and_add_project_root():
    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents]:
        if (candidate / "v3" / "repository_graph").is_dir():
            sys.path.insert(0, str(candidate))
            return
    raise RuntimeError("Could not find the 'v3' package.")


_find_and_add_project_root()

import ast
from v3.repository_graph.deep_resolution import assignment_chain_builder as acb_module
from v3.repository_graph.languages.python_adapter import PythonAdapter
from v3.repository_graph import subtree_naming

# Monkey-patch _record_assignment to log every call for target "state"
# in any module containing "blueprints" - this is purely diagnostic,
# not a permanent change.
_original = acb_module.AssignmentChainBuilder._record_assignment


def _traced(self, module_name, target_name, value_node):
    if target_name == "state" and "blueprints" in module_name:
        print(f"_record_assignment called: module={module_name!r} target={target_name!r} "
              f"value_node_type={type(value_node).__name__} line={getattr(value_node, 'lineno', '?')}")
        print("    ast.dump:", ast.dump(value_node))
    _original(self, module_name, target_name, value_node)


acb_module.AssignmentChainBuilder._record_assignment = _traced

_original_build = acb_module.AssignmentChainBuilder.build


def _traced_build(self):
    result = _original_build(self)
    key = "flask.sansio.blueprints:state"
    print(f"\nFINAL table value for {key!r} right after build() returns: {result.get(key)}")
    return result


acb_module.AssignmentChainBuilder.build = _traced_build

repo_path = sys.argv[1]
report = PythonAdapter().scan(repo_root=repo_path, file_paths=[])
print("\nsrc_layout_prefix_stripped:", report.get("src_layout_prefix_stripped"))
print("Final resolver_results:", report["deep_resolution"]["resolver_results"])