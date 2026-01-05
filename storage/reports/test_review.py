import os
import ast
import json

folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests")

logs = []

if not os.path.exists(folder):
    print(f"⚠ Folder '{folder}' not found!")
    exit()

# Go through each Python file
for file in os.listdir(folder):
    if file.endswith(".py"):
        file_path = os.path.join(folder, file)
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        passed = 0
        failed = 0

        # Check each function for docstring
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if ast.get_docstring(node):
                    passed += 1
                else:
                    failed += 1

        logs.append({
            "file": file,
            "passed": passed,
            "failed": failed
        })

# Save JSON
with open("review_logs.json", "w") as f:
    json.dump(logs, f, indent=4)

print("✅ review_logs.json generated!")
