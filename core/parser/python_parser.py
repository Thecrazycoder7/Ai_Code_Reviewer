import ast
import os
from typing import Any, Dict, List, Optional

# ---------------- Helper Functions ----------------

# Get type annotation as string
def _get_annotation(node: Optional[ast.AST]) -> Optional[str]:
    if node is None:
        return None
    return ast.unparse(node)  # Converts AST node to string

# Get default value as string
def _get_default_str(node: Optional[ast.AST]) -> Optional[str]:
    if node is None:
        return None
    return ast.unparse(node)

# Simple complexity: number of statements in the function
def _simple_complexity(node: ast.FunctionDef) -> int:
    return len(node.body)

# Max nesting depth in function
def _max_nesting_depth(node: ast.FunctionDef) -> int:
    def depth(n, current=0):
        max_d = current
        for child in ast.iter_child_nodes(n):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                max_d = max(max_d, depth(child, current + 1))
            else:
                max_d = max(max_d, depth(child, current))
        return max_d
    return depth(node)

# ---------------- Smell Detection ----------------

# Long function: threshold > 50 statements
def is_long_function(node: ast.FunctionDef, threshold=50) -> bool:
    return len(node.body) > threshold

# Deeply nested function: threshold > 3
def is_deeply_nested(node: ast.FunctionDef, threshold=3) -> bool:
    return _max_nesting_depth(node) > threshold

# Missing type hints for args or return
def missing_type_hints(node: ast.FunctionDef) -> List[str]:
    missing = []
    for arg in node.args.args:
        if arg.annotation is None:
            missing.append(arg.arg)
    if node.returns is None:
        missing.append("return")
    return missing

# ---------------- Parse Function ----------------
def _parse_function(node: ast.FunctionDef) -> Dict[str, Any]:
    args = []
    defaults = [None]*(len(node.args.args) - len(node.args.defaults)) + node.args.defaults
    for arg, default in zip(node.args.args, defaults):
        args.append({
            "name": arg.arg,
            "annotation": _get_annotation(arg.annotation),
            "default": _get_default_str(default)
        })

    return {
        "name": node.name,
        "args": args,
        "complexity": _simple_complexity(node),
        "max_nesting": _max_nesting_depth(node),
        "docstring": ast.get_docstring(node),
        "is_long": is_long_function(node),
        "is_deeply_nested": is_deeply_nested(node),
        "missing_type_hints": missing_type_hints(node)
    }

# ---------------- Parse Path ----------------
def parse_path(file_path: str = None, file_content: str = None) -> List[Dict[str, Any]]:
    """
    Parse functions from a Python file or uploaded code content.
    """
    if file_content is not None:
        tree = ast.parse(file_content, filename=file_path or "<uploaded>")
    elif file_path is not None:
        with open(file_path, "r") as f:
            tree = ast.parse(f.read(), filename=file_path)
    else:
        raise ValueError("Either file_path or file_content must be provided.")

    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    return [_parse_function(f) for f in functions]


# ---------------- Example Usage ----------------
if __name__ == "__main__":
    examples_folder = "examples"
    if os.path.exists(examples_folder):
        files = [f for f in os.listdir(examples_folder) if f.endswith(".py")]
        for file in files:
            path = os.path.join(examples_folder, file)
            print(f"\nParsing file: {file}")
            funcs = parse_path(file_path=path)
            for f in funcs:
                print(f)
    else:
        print(f"Folder '{examples_folder}' not found!")
