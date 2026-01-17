import ast
import os
from typing import Any, List, Dict
import autopep8
import pydocstyle
import streamlit as st
from radon.complexity import cc_visit
from radon.metrics import mi_visit

# --- METRIC FUNCTIONS ---
def compute_complexity_from_string(code: str) -> dict:
    """Analyze code string directly to avoid path issues."""
    try:
        analysis = cc_visit(code)
        if not analysis:
            return {"info": "No functions found"}
        return {item.name: item.complexity for item in analysis if item.is_function}
    except Exception as e:
        return {"error": str(e)}

import ast
from radon.complexity import cc_visit
from radon.metrics import mi_visit

def summarize_complexity(code: str) -> dict:
    """Analyze complexity directly from a string of code."""
    try:
        # cc_visit returns a list of Function objects
        analysis = cc_visit(code)
        
        if not analysis:
            return {"info": "No functions found"}

        # Filter only for functions/methods
        complexity_map = {item.name: item.complexity for item in analysis if hasattr(item, 'complexity')}
        
        if not complexity_map:
            return {"info": "No functions found"}

        values = list(complexity_map.values())
        max_val = max(values)
        
        return {
            "total_functions": len(values),
            "average_complexity": round(sum(values) / len(values), 2),
            "max_complexity": max_val,
            "risk_level": "Low" if max_val <= 5 else "Medium" if max_val <= 10 else "High",
            "per_function": complexity_map
        }
    except Exception as e:
        return {"error": str(e)}

def compute_maintainability_single(code: str) -> dict:
    """Computes Maintainability Index from a string of code."""
    try:
        # mi_visit returns a score (0-100)
        mi_score = mi_visit(code, multi=True)
        return {
            "score": round(mi_score, 2),
            "status": "Good" if mi_score >= 70 else "Average" if mi_score >= 50 else "Poor"
        }
    except Exception as e:
        return {"score": 0, "status": "Error"}
    
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
            if line.strip().startswith("def ") and i < len(lines) and '"""' not in lines[i]:

                violations.append({
                    "code": "D103",
                    "line": i,
                    "message": "Missing docstring"
                })

    except Exception as e:
        return []

    return violations
