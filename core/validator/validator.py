import ast
from typing import List, Dict
import autopep8
import pydocstyle

def compute_complexity(file_path: str) -> Dict[str, int]:
    """
    Compute cyclomatic complexity for functions in a Python file.
    Returns a dictionary mapping function names to their complexity scores.
    """
    from radon.complexity import cc_visit

    complexities = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        analysis = cc_visit(code)
        for item in analysis:
            if item.is_function:
                complexities[item.name] = item.complexity

    except Exception:
        pass  # In case of error, return empty dict

    return complexities

def compute_maintainability(file_path: str) -> float:
    """
    Compute maintainability index for a Python file.
    Returns the maintainability index as a float.
    """
    from radon.metrics import mi_visit

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        mi_score = mi_visit(code, True)
        return mi_score

    except Exception:
        return -1.0  # Indicate failure to compute
    
    
def validate_file(file_path: str) -> Dict:
    """
    Validate a Python file for code quality.
    
    Returns a dictionary:
    {
        "file": filename,
        "parse_error": bool,
        "missing_docstrings": int,
        "total_functions": int,
        "pep257_violations": int,
        "formatting_issues": int
    }
    """
    results = {
        "file": file_path,
        "parse_error": False,
        "missing_docstrings": 0,
        "total_functions": 0,
        "pep257_violations": 0,
        "formatting_issues": 0
    }

    # Read file content
    with open(file_path, "r") as f:
        code = f.read()

    # ---------------- PARSE ERROR ----------------
    try:
        tree = ast.parse(code)
    except Exception:
        results["parse_error"] = True
        return results  # cannot proceed if parsing fails

    # ---------------- DOCSTRING CHECK ----------------
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    results["total_functions"] = len(functions)
    for fn in functions:
        if not ast.get_docstring(fn):
            results["missing_docstrings"] += 1

    # ---------------- PEP-257 CHECK ----------------
    try:
        pep_issues = list(pydocstyle.check([file_path]))
        results["pep257_violations"] = len(pep_issues)
    except Exception:
        results["pep257_violations"] = -1  # failed to check

    # ---------------- FORMATTING ISSUES ----------------
    try:
        formatted_code = autopep8.fix_code(code, options={'aggressive': 1})
        if formatted_code != code:
            results["formatting_issues"] = 1  # indicates code needs formatting
    except Exception:
        results["formatting_issues"] = -1  # failed to check

    return results


def validate_folder(folder_path: str) -> List[Dict]:
    """
    Validate all Python files in a folder.
    Returns a list of results for each file.
    """
    results_list = []
    import os
    for f in os.listdir(folder_path):
        if f.endswith(".py"):
            file_path = os.path.join(folder_path, f)
            results_list.append(validate_file(file_path))
    return results_list

def validate_docstrings(file_path):
    violations = []

    # example dummy check (replace with real pydocstyle later)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, start=1):
            if line.strip().startswith("def ") and '"""' not in lines[i]:
                violations.append({
                    "code": "D103",
                    "line": i,
                    "message": "Missing docstring"
                })

    except Exception as e:
        return []

    return violations
