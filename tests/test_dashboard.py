"""
Tests for Streamlit dashboard
"""

import ast
import os
import tempfile
import pandas as pd

from dashboard.dashboard import get_functions, dashboard


def create_temp_py(code: str):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    tmp.write(code.encode("utf-8"))
    tmp.close()
    return tmp.name


def test_get_functions_with_docstring():
    code = '''
        def add(a, b):
            """Add two numbers"""
            return a + b
        '''
    path = create_temp_py(code)
    rows = get_functions(path)

    assert isinstance(rows, list)
    assert len(rows) == 1
    assert rows[0]["Function"] == "add"
    assert rows[0]["Docstring"] == "Yes"

    os.remove(path)


def test_get_functions_without_docstring():
    code = '''
def hello():
    pass
'''
    path = create_temp_py(code)
    rows = get_functions(path)

    assert len(rows) == 1
    assert rows[0]["Docstring"] == "No"

    os.remove(path)


def test_get_functions_multiple_functions():
    code = '''
def a():
    pass

def b():
    """doc"""
    pass
'''
    path = create_temp_py(code)
    rows = get_functions(path)

    assert len(rows) == 2
    names = [r["Function"] for r in rows]
    assert "a" in names
    assert "b" in names

    os.remove(path)


def test_dashboard_runs_without_crash(monkeypatch):
    """
    Dashboard is UI code.
    We only test that it runs without error.
    """

    class FakeStreamlit:
        def markdown(self, *a, **k): pass
        def subheader(self, *a, **k): pass
        def bar_chart(self, *a, **k): pass
        def tabs(self, *a, **k):
            return [self, self, self, self]
        def selectbox(self, *a, **k): return "All"
        def dataframe(self, *a, **k): pass
        def text_input(self, *a, **k): return ""
        def columns(self, n): return [self] * n
        def button(self, *a, **k): return False
        def write(self, *a, **k): pass

    monkeypatch.setattr(
        "dashboard.dashboard.st",
        FakeStreamlit()
    )

    # should not raise error
    dashboard()
