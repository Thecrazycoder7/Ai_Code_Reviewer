"""
Tests for advanced AST parser and code smell detection
"""

import ast
import pytest

from core.parser.python_parser import (
    _get_annotation,
    _get_default_str,
    is_long_function,
    parse_path,
)


def test_get_annotation():
    node = ast.parse("def f(x: int): pass").body[0].args.args[0].annotation
    assert _get_annotation(node) == "int"


def test_get_annotation_none():
    assert _get_annotation(None) is None


def test_get_default_str():
    node = ast.parse("def f(x=10): pass").body[0].args.defaults[0]
    assert _get_default_str(node) == "10"


def test_simple_parse_function():
    code = """
def add(a: int, b: int) -> int:
    return a + b
"""
    results = parse_path(file_content=code)

    assert len(results) == 1
    fn = results[0]

    assert fn["name"] == "add"
    assert fn["complexity"] >= 1
    assert fn["docstring"] is None
    assert fn["missing_type_hints"] == []


def test_missing_type_hints():
    code = """
def test(a, b):
    return a + b
"""
    fn = parse_path(file_content=code)[0]

    assert "a" in fn["missing_type_hints"]
    assert "b" in fn["missing_type_hints"]
    assert "return" in fn["missing_type_hints"]


def test_long_function_detection():
    code = "def long_fn():\n" + "\n".join(["    x = 1"] * 60)
    fn = parse_path(file_content=code)[0]

    assert is_long_function(ast.parse(code).body[0]) is True
    assert fn["is_long"] is True


def test_deeply_nested_detection():
    code = """
def deep(x):
    if x:
        if x > 1:
            if x > 2:
                if x > 3:
                    return x
"""
    fn = parse_path(file_content=code)[0]

    assert fn["is_deeply_nested"] is True
    assert fn["max_nesting"] > 3


def test_parse_path_file_content():
    code = "def a(): pass"
    results = parse_path(file_content=code)

    assert isinstance(results, list)
    assert results[0]["name"] == "a"


def test_parse_path_invalid_usage():
    with pytest.raises(ValueError):
        parse_path()
