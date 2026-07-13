"""
model_graph_tracer.py

Static, never-executed tracer for nn.Module-style model architectures
(PyTorch convention, but the pattern generalizes: any class whose
__init__ assigns named sub-components and whose forward()-style
method calls them in some order).

Design, deliberately reusing what's already proven elsewhere in this
project rather than inventing a new mechanism:
  - __init__ scan: same shape as constructor tracking in deep_resolution
    - find self.X = LayerType(...) assignments, record (name, layer_type).
  - forward() scan: walk the method body in source order, find every
    self.X(...) call, record the order they're invoked in.
  - Graph: nodes = layers (from __init__), edges = call sequence
    (from forward()).

Stays static-only by design: no execution, no tensor shapes, no
parameter counts - those require actually running the model, which is
a different, explicitly out-of-scope paradigm for this project.
"""

import ast
from pathlib import Path
from typing import Dict, Any, List, Optional


FORWARD_METHOD_NAMES = {"forward", "call", "__call__"}


class ModelGraphTracer:
    def __init__(self):
        self.layers: Dict[str, Dict[str, Any]] = {}
        self.call_sequence: List[Dict[str, Any]] = []

    def _extract_init_layers(self, class_node: ast.ClassDef):
        init_method = next(
            (n for n in class_node.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"),
            None,
        )
        if not init_method:
            return
        for node in ast.walk(init_method):
            if not isinstance(node, ast.Assign):
                continue
            if len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not isinstance(target, ast.Attribute):
                continue
            if not isinstance(target.value, ast.Name) or target.value.id != "self":
                continue
            if not isinstance(node.value, ast.Call):
                continue
            layer_name = target.attr
            func = node.value.func
            if isinstance(func, ast.Name):
                layer_type = func.id
            elif isinstance(func, ast.Attribute):
                layer_type = func.attr
            else:
                continue
            self.layers[layer_name] = {"layer_type": layer_type, "lineno": node.lineno}

    def _extract_forward_sequence(self, class_node: ast.ClassDef):
        forward_method = next(
            (n for n in class_node.body if isinstance(n, ast.FunctionDef) and n.name in FORWARD_METHOD_NAMES),
            None,
        )
        if not forward_method:
            return
        for node in ast.walk(forward_method):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            if not isinstance(func.value, ast.Name) or func.value.id != "self":
                continue
            layer_name = func.attr
            if layer_name not in self.layers:
                continue  # only count calls to layers actually found in __init__ - never guess
            self.call_sequence.append({"layer_name": layer_name, "lineno": node.lineno})

    def trace_class(self, class_node: ast.ClassDef):
        self._extract_init_layers(class_node)
        self._extract_forward_sequence(class_node)
        return {"layers": self.layers, "call_sequence": self.call_sequence}


def trace_model_file(filepath: str, class_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Traces every class in a file (or just `class_name` if given) that
    has both an __init__ and a forward()-style method. Returns one
    result per matching class.
    """
    source = Path(filepath).read_text(encoding="utf-8")
    tree = ast.parse(source)
    results = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if class_name and node.name != class_name:
            continue
        has_init = any(isinstance(n, ast.FunctionDef) and n.name == "__init__" for n in node.body)
        has_forward = any(isinstance(n, ast.FunctionDef) and n.name in FORWARD_METHOD_NAMES for n in node.body)
        if not (has_init and has_forward):
            continue
        tracer = ModelGraphTracer()
        results[node.name] = tracer.trace_class(node)
    return results
