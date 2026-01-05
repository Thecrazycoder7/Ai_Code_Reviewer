"""
Tests for Groq + AST integration
"""

import ast
from core.docstring_engine.generator import (
    extract_func_info,
    analyze_file_with_groq,
    analyze_function_with_groq,
)


def test_extract_func_info_basic():
    code = """
def add(a, b) -> int:
    return a + b
"""
    tree = ast.parse(code)
    node = tree.body[0]

    info = extract_func_info(node)

    assert info["name"] == "add"
    assert info["args"] == ["a", "b"]
    assert info["returns"] == "int"


def test_extract_func_info_no_return():
    code = """
def hello(name):
    print(name)
"""
    tree = ast.parse(code)
    node = tree.body[0]

    info = extract_func_info(node)

    assert info["name"] == "hello"
    assert info["args"] == ["name"]
    assert info["returns"] == "None"


def test_analyze_file_returns_string(monkeypatch):
    def fake_response(*args, **kwargs):
        class Fake:
            choices = [type("obj", (), {"message": type("m", (), {"content": "File summary"})})]
        return Fake()

    monkeypatch.setattr(
        "core.docstring_engine.groq_integration.client.chat.completions.create",
        fake_response
    )

    result = analyze_file_with_groq("print('hello')")
    assert isinstance(result, str)
    assert len(result) > 0


def test_analyze_file_handles_error(monkeypatch):
    def fake_error(*args, **kwargs):
        raise Exception("API error")

    monkeypatch.setattr(
        "core.docstring_engine.groq_integration.client.chat.completions.create",
        fake_error
    )

    result = analyze_file_with_groq("print('x')")
    assert "Error" in result


def test_analyze_function_returns_string(monkeypatch):
    code = """
def multiply(x, y):
    return x * y
"""
    tree = ast.parse(code)
    node = tree.body[0]

    def fake_response(*args, **kwargs):
        class Fake:
            choices = [type("obj", (), {"message": type("m", (), {"content": "Docstring text"})})]
        return Fake()

    monkeypatch.setattr(
        "core.docstring_engine.groq_integration.client.chat.completions.create",
        fake_response
    )

    result = analyze_function_with_groq(node, code)
    assert isinstance(result, str)
    assert len(result) > 0


def test_analyze_function_error_handling(monkeypatch):
    code = """
def bad(x):
    return x
"""
    tree = ast.parse(code)
    node = tree.body[0]

    def fake_error(*args, **kwargs):
        raise Exception("Groq failed")

    monkeypatch.setattr(
        "core.docstring_engine.groq_integration.client.chat.completions.create",
        fake_error
    )

    result = analyze_function_with_groq(node, code)
    assert "Error" in result
