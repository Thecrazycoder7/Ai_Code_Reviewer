import json
from typing import List, Dict, Any

# Compute docstring coverage per file
def compute_coverage(per_file_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    report = {}
    total_functions = 0
    total_with_doc = 0

    for file_result in per_file_results:
        file_name = file_result.get("file_path", "unknown")
        functions = file_result.get("functions", [])
        file_total = len(functions)
        file_with_doc = sum(1 for f in functions if f.get("docstring"))
        
        total_functions += file_total
        total_with_doc += file_with_doc

        coverage = (file_with_doc / file_total * 100) if file_total else 0
        report[file_name] = {
            "total_functions": file_total,
            "functions_with_docstring": file_with_doc,
            "coverage_percent": round(coverage, 2)
        }

    overall_coverage = (total_with_doc / total_functions * 100) if total_functions else 0
    report["overall"] = {
        "total_functions": total_functions,
        "functions_with_docstring": total_with_doc,
        "coverage_percent": round(overall_coverage, 2)
    }

    return report

# Write report to JSON file
def write_report(reports: Dict[str, Any], path: str) -> None:
    with open(path, "w") as f:
        json.dump(reports, f, indent=4)

# Example usage
if __name__ == "__main__":
    sample_results = [
        {
            "file_path": "example.py",
            "functions": [
                {"name": "foo", "docstring": "Example doc"},
                {"name": "bar", "docstring": None}
            ]
        }
    ]
    coverage_report = compute_coverage(sample_results)
    write_report(coverage_report, "coverage_report.json")
    print("Report saved!")
