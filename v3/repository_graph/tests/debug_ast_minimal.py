"""
debug_ast_minimal.py

Most minimal possible isolation: parses blueprints.py directly, finds
the "state = ..." Assign node, and prints exactly what AST node type
Python parsed the right-hand side into - completely bypassing the rest
of the pipeline to rule out anything else as a variable.

    python v3\\repository_graph\\tests\\debug_ast_minimal.py C:\\repos\\v3\\flask\\src\\flask\\sansio\\blueprints.py
"""
import ast
import sys

filepath = sys.argv[1]
source = open(filepath, encoding="utf-8").read()
print("Python version:", sys.version)
print("File length (chars):", len(source))

tree = ast.parse(source)
for node in ast.walk(tree):
    if not isinstance(node, ast.Assign):
        continue
    if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
        continue
    if node.targets[0].id != "state":
        continue
    print(f"\nFound 'state = ...' assignment at line {node.lineno}")
    print("  value_node type:", type(node.value).__name__)
    print("  ast.dump(value_node):", ast.dump(node.value))
    if isinstance(node.value, ast.Call):
        print("  value_node.func type:", type(node.value.func).__name__)
        if isinstance(node.value.func, ast.Attribute):
            print("  value_node.func.attr:", node.value.func.attr)