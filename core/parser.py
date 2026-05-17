import ast


def extract_functions(file_path, include_nested=False):
    with open(file_path, "r", encoding="utf-8") as file:
        source_code = file.read()

    tree = ast.parse(source_code)
    functions = []

    # =========================
    # 🔥 NEW: Helper to detect top-level functions
    # =========================
    def is_top_level(node):
        return isinstance(node, ast.FunctionDef)

    # =========================
    # 🔥 NEW: Extract only top-level by default
    # =========================
    if not include_nested:
        for node in tree.body:   # ✅ ONLY top-level
            if is_top_level(node):
                function_code = ast.get_source_segment(source_code, node)

                functions.append({
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "code": function_code,
                    "start_line": node.lineno,
                    "end_line": node.end_lineno
                })

    # =========================
    # 🔥 OPTIONAL: Allow nested extraction if needed
    # =========================
    else:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_code = ast.get_source_segment(source_code, node)

                functions.append({
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "code": function_code,
                    "start_line": node.lineno,
                    "end_line": node.end_lineno
                })

    return functions


def extract_functions_from_files(file_paths, include_nested=False):
    all_functions = []

    for file_path in file_paths:
        functions = extract_functions(file_path, include_nested=include_nested)

        for f in functions:
            f["file"] = file_path  # track file origin

        all_functions.extend(functions)

    return all_functions