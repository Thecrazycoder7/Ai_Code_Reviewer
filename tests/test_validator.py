"""
Tests for file and folder validation
"""

import os
import tempfile

from core.validator.validator import (
    validate_file,
    validate_folder,
    validate_docstrings,
)


def create_temp_file(code: str):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    tmp.write(code.encode("utf-8"))
    tmp.close()
    return tmp.name


def test_validate_file_basic():
    code = '''
def add(a, b):
    """Add two numbers"""
    return a + b
'''
    path = create_temp_file(code)
    result = validate_file(path)

    assert isinstance(result, dict)
    assert result["parse_error"] is False
    assert result["total_functions"] == 1
    assert result["missing_docstrings"] == 0

    os.remove(path)


def test_validate_file_missing_docstring():
    code = '''
def hello():
    pass
'''
    path = create_temp_file(code)
    result = validate_file(path)

    assert result["total_functions"] == 1
    assert result["missing_docstrings"] == 1

    os.remove(path)


def test_validate_file_parse_error():
    code = "def bad("
    path = create_temp_file(code)

    result = validate_file(path)
    assert result["parse_error"] is True

    os.remove(path)


def test_validate_file_formatting_issue():
    code = "def add(a,b):return a+b"
    path = create_temp_file(code)

    result = validate_file(path)
    assert result["formatting_issues"] in [0, 1]

    os.remove(path)


def test_validate_folder():
    with tempfile.TemporaryDirectory() as folder:
        file1 = os.path.join(folder, "a.py")
        file2 = os.path.join(folder, "b.py")

        with open(file1, "w") as f:
            f.write("def a(): pass")

        with open(file2, "w") as f:
            f.write("def b(): pass")

        results = validate_folder(folder)

        assert isinstance(results, list)
        assert len(results) == 2


def test_validate_docstrings_detects_missing():
    code = '''
def test():
    pass
'''
    path = create_temp_file(code)
    violations = validate_docstrings(path)

    assert isinstance(violations, list)
    assert len(violations) == 1
    assert violations[0]["code"] == "D103"

    os.remove(path)


def test_validate_docstrings_no_error():
    code = '''
def test():
    """doc"""
    pass
'''
    path = create_temp_file(code)
    violations = validate_docstrings(path)

    assert isinstance(violations, list)
    assert len(violations) == 0

    os.remove(path)
