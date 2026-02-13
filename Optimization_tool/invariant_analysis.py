import ast
import astor

class LICMVisitor(ast.NodeVisitor):
    def __init__(self):
        self.loop_vars = set()
        self.loop_invariants = []
        self.in_loop = False
        self.loop_node = None
        self.function_invariants = {}  # Store invariants per function

    def visit_FunctionDef(self, node):
        # Reset loop vars and invariants for each function
        self.loop_vars = set()
        self.loop_invariants = []
        self.generic_visit(node)

        # Store the loop-invariants for the current function
        self.function_invariants[node.name] = self.loop_invariants

    def visit_For(self, node):
        if not self.in_loop:
            self.in_loop = True
            self.loop_node = node
        self.loop_vars.add(node.target.id)
        self.generic_visit(node)
        if self.loop_node is node:
            self.in_loop = False

    def visit_Assign(self, node):
        if self.in_loop:
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id not in self.loop_vars:
                    self.loop_invariants.append(node)

    def visit_BinOp(self, node):
        if self.in_loop:
            left_is_invariant = isinstance(node.left, (ast.Name, ast.Constant)) and \
                                (isinstance(node.left, ast.Constant) or node.left.id not in self.loop_vars)
            right_is_invariant = isinstance(node.right, (ast.Name, ast.Constant)) and \
                                 (isinstance(node.right, ast.Constant) or node.right.id not in self.loop_vars)
            if left_is_invariant and right_is_invariant:
                self.loop_invariants.append(node)
        self.generic_visit(node)

def move_loop_invariants_outside_loop(source_code):
    tree = ast.parse(source_code)
    licm_visitor = LICMVisitor()
    licm_visitor.visit(tree)

    moved_lines = []

    # For each function, move its own invariants outside its loop
    for func_name, loop_invariants in licm_visitor.function_invariants.items():
        if not loop_invariants:
            continue

        # Find the loop node within the AST, even if it's nested
        def find_loop_node(node):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.For):
                    return child
                else:
                    result = find_loop_node(child)
                    if result is not None:
                        return result
            return None

        # Find the function node in the AST by function name
        for func in tree.body:
            if isinstance(func, ast.FunctionDef) and func.name == func_name:
                loop_node = find_loop_node(func)
                if loop_node is None:
                    continue

                # Track the original line numbers of the loop-invariant expressions
                moved_lines.extend([node.lineno for node in loop_invariants])

                # Remove loop-invariant expressions from the loop body
                loop_node.body = [n for n in loop_node.body if n not in loop_invariants]

                # Insert loop-invariant expressions before the loop
                for parent in ast.walk(func):
                    if hasattr(parent, 'body') and isinstance(parent.body, list):
                        for index, child in enumerate(parent.body):
                            if child is loop_node:
                                for invariant in reversed(loop_invariants):
                                    parent.body.insert(index, invariant)
                                break

    return astor.to_source(tree), moved_lines


if __name__ == "__main__":
    code = '''
def sum_elements(arr):
    result = 0
    for num in arr:
        result += num
    return result

def product_elements(arr):
    result = 1
    for num in arr:
        result *= num
    return result

def compare_elements(arr1, arr2):
    if len(arr1) != len(arr2):
        return False
    for i in range(len(arr1)):
        if arr1[i] != arr2[i]:
            return False
    return True

def find_max(arr):
    max_value = arr[0]
    for num in arr:
        if num > max_value:
            max_value = num
    return max_value

def find_min(arr):
    min_value = arr[0]
    for num in arr:
        if num < min_value:
            min_value = num
    return min_value

def sum_elements_modified(arr):
    result = 0
    length = len(arr)
    for i in range(length):
        result += arr[i]
    return result

def sum_elements_invariant(arr):
    result = 0
    length = len(arr)
    for i in range(length):
        result += arr[i]
    return result

def average_elements(arr):
    sum_value = sum_elements(arr)
    return sum_value / len(arr) if len(arr) > 0 else 0

def sort_array(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]

def sum_function(arr):
    total = 0
    for num in arr:
        total += num
    return total

def find_first_occurrence(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1

def product_function(arr):
    result = 1
    length = len(arr)
    for i in range(length):
        result *= arr[i]
    return result
    '''
    optimized_code, moved_lines = move_loop_invariants_outside_loop(code)
    print("Optimized Code:")
    print(optimized_code)
    print("Moved Lines:", moved_lines)
