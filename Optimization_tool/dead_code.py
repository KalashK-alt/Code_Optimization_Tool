import ast

def remove_dead_code(code):
    tree = ast.parse(code)
    optimized_code = code
    removed_code = ""
    removed_lines = []

    # Collect global variable names
    global_vars = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    global_vars.add(target.id)

    # Collect variable names used within the tree
    used_vars = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used_vars.add(node.id)

    # Remove unused global variables
    for node in reversed(tree.body):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in global_vars:
                    if target.id not in used_vars:
                        removed_code += ast.unparse(node) + "\n"
                        removed_lines.append(node.lineno)  # Track the line number
                        tree.body.remove(node)
                        global_vars.remove(target.id)

    # Collect function names
    functions = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions.add(node.name)

    # Remove unused functions
    for node in reversed(tree.body):
        if isinstance(node, ast.FunctionDef) and node.name in functions:
            if not any(isinstance(child, ast.Call) and
                       ((isinstance(child.func, ast.Name) and child.func.id == node.name) or
                        (isinstance(child.func, ast.Attribute) and child.func.attr == node.name))
                       for child in ast.walk(tree)):
                removed_code += ast.unparse(node) + "\n"
                removed_lines.append(node.lineno)  # Track the line number
                tree.body.remove(node)

    if removed_code:
        optimized_code = ast.unparse(tree)
    return optimized_code, removed_code, removed_lines
