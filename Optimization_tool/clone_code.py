import ast
import hashlib
from difflib import SequenceMatcher
import autopep8

def generate_ast(source):
    return ast.parse(source)


def remove_functions_with_no_body(code):
    lines = code.splitlines()
    cleaned_code = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check if it's a function declaration
        if line.startswith("def "):
            j = i + 1
            # Skip blank lines and comments
            while j < len(lines) and (lines[j].strip() == "" or lines[j].strip().startswith("#")):
                j += 1

            # If the next meaningful line is another function declaration, skip the current one
            if j < len(lines) and lines[j].strip().startswith("def "):
                i = j  # Skip to the next function
            else:
                cleaned_code.append(lines[i])  # Keep the current function
        else:
            cleaned_code.append(lines[i])  # Non-function lines are kept

        i += 1

    return '\n'.join(cleaned_code)


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def detect_clones(source_code):
    try:
        root = ast.parse(source_code)
        function_code_blocks = {}
        clones_found = False
        clone_result = []

        for node in ast.walk(root):
            if isinstance(node, ast.FunctionDef):
                function_code = ast.unparse(node.body)
                found_similar = False

                for existing_code, func_data in function_code_blocks.items():
                    sim_score = similarity(existing_code, function_code)
                    if sim_score > 0.8:  # Adjust similarity threshold as needed
                        clones_found = True
                        clone_result.append({
                            "name": node.name,
                            "start_line": node.lineno,
                            "end_line": node.end_lineno,
                            "similar_to": func_data["name"],
                            "similar_start": func_data["start_line"],
                            "similar_end": func_data["end_line"]
                        })
                        found_similar = True
                        break

                if not found_similar:
                    function_code_blocks[function_code] = {
                        "name": node.name,
                        "start_line": node.lineno,
                        "end_line": node.end_lineno
                    }

        return clone_result if clones_found else []
    except SyntaxError as e:
        return f"Syntax Error: {e}"


def convert_to_clean_code(source_code):
    formatted_code = autopep8.fix_code(source_code)

    # Parse the cleaned code into AST

    root = generate_ast(formatted_code)

    function_nodes = [node for node in ast.walk(root) if isinstance(node, ast.FunctionDef)]

    cleaned_code = ""
    encountered_functions = set()
    encountered_lines = set()

    for line in source_code.split('\n'):
        if line.strip() not in encountered_lines:
            cleaned_code += line + '\n'
            encountered_lines.add(line.strip())

    print(cleaned_code)
    formatted_code2 = autopep8.fix_code(cleaned_code)
    formatted_code3=remove_functions_with_no_body(formatted_code2)

    return formatted_code3.strip()

