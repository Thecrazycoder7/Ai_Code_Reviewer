"""
Tests for coverage computation and report writing
"""

import json
import os
import tempfile

from core.reporter.coverage_reporter import compute_coverage, write_report


def test_compute_coverage_single_file():
    data = [
        {
            "file_path": "test.py",
            "functions": [
                {"name": "a", "docstring": "doc"},
                {"name": "b", "docstring": None},
            ],
        }
    ]

    report = compute_coverage(data)

    assert "test.py" in report
    assert report["test.py"]["total_functions"] == 2
    assert report["test.py"]["functions_with_docstring"] == 1
    assert report["test.py"]["coverage_percent"] == 50.0


def test_compute_coverage_multiple_files():
    data = [
        {
            "file_path": "a.py",
            "functions": [
                {"name": "f1", "docstring": "doc"},
            ],
        },
        {
            "file_path": "b.py",
            "functions": [
                {"name": "f2", "docstring": None},
                {"name": "f3", "docstring": None},
            ],
        },
    ]

    report = compute_coverage(data)

    assert report["a.py"]["coverage_percent"] == 100.0
    assert report["b.py"]["coverage_percent"] == 0.0

    assert report["overall"]["total_functions"] == 3
    assert report["overall"]["functions_with_docstring"] == 1
    assert report["overall"]["coverage_percent"] == round(1 / 3 * 100, 2)


def test_compute_coverage_empty_input():
    report = compute_coverage([])

    assert "overall" in report
    assert report["overall"]["total_functions"] == 0
    assert report["overall"]["coverage_percent"] == 0


def test_write_report_creates_file():
    report = {
        "overall": {
            "total_functions": 1,
            "functions_with_docstring": 1,
            "coverage_percent": 100.0,
        }
    }

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "report.json")
        write_report(report, path)

        assert os.path.exists(path)

        with open(path, "r") as f:
            data = json.load(f)

        assert data["overall"]["coverage_percent"] == 100.0
