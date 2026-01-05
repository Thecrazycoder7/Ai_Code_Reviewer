import ast
import os

import json
from groq import Groq
from dotenv import load_dotenv

# ---------------- LOAD ENV ----------------
load_dotenv()

# ---------------- GROQ CLIENT ----------------
client = Groq()
MODEL = "llama-3.3-70b-versatile"

# ---------------- AST HELPERS ----------------

def extract_func_info(node: ast.FunctionDef) -> dict:
    return {
        "name": node.name,
        "args": [arg.arg for arg in node.args.args],
        "returns": ast.unparse(node.returns) if node.returns else "None"
    }

def analyze_file_with_groq(code: str) -> str:
    prompt = f"""
Explain this Python file in simple words.
Keep it short.

Code:
{code}
"""
    try:
        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

def analyze_function_with_groq(node, code) -> str:
    info = extract_func_info(node)

    prompt = f"""
You are a Python documentation expert.

Generate THREE docstrings in the EXACT format below.
Follow spacing and line breaks strictly.

[GOOGLE]
Summarize the function in one line.

A more detailed description of the function, if necessary, follows here.

Args:
    param1: Description.
    param2: Description.

Returns:
    Description of return value.

[NUMPY]
Summarize the function in one line.

A more detailed description of the function, if necessary.

Parameters
----------
param1 : type
    Description.
param2 : type
    Description.

Returns
-------
type
    Description of return value.

[REST]
Summarize the function in one line.

A more detailed description of the function, if necessary.

:param param1: Description.
:type param1: type
:param param2: Description.
:type param2: type
:returns: Description of return value.
:rtype: type

Rules:
- The summary MUST be written in imperative mood
- Start with the base verb (e.g., Add, Calculate, Normalize, Convert, Fetch, Validate)
- Do NOT use third-person verbs (no Adds, Calculates, Returns)
- If the summary violates this rule, rewrite it internally before responding
- Include "raises" ONLY if exceptions actually occur
- If no exceptions occur, return "raises": {{}}
- Do NOT invent exceptions
- Do NOT include markdown
- Do NOT include triple quotes
- JSON must be strictly valid
- Be concise and professional

Function name: {info['name']}
Arguments: {info['args']}
Return type: {info['returns']}
"""


    try:
        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"


def json_to_google_docstring(json_text: str) -> str:
    data = json.loads(json_text)

    lines = [
        data.get("summary", ""),
        "",
        "A more detailed description of the function, if necessary, follows here.",
        ""
    ]

    if data.get("args"):
        lines.append("Args:")
        for k, v in data["args"].items():
            lines.append(f"    {k}: {v}")
        lines.append("")

    if data.get("returns"):
        lines.append("Returns:")
        lines.append(f"    {data['returns']}")

    return "\n".join(lines)



def json_to_numpy_docstring(json_text: str) -> str:
    data = json.loads(json_text)

    lines = [
        data.get("summary", ""),
        "",
        "A more detailed description of the function, if necessary.",
        ""
    ]

    if data.get("args"):
        lines.extend([
            "Parameters",
            "----------"
        ])
        for k, v in data["args"].items():
            lines.append(f"{k} : type")
            lines.append(f"    {v}")
        lines.append("")

    if data.get("returns"):
        lines.extend([
            "Returns",
            "-------",
            "type",
            f"    {data['returns']}"
        ])

    return "\n".join(lines)



def json_to_rest_docstring(json_text: str) -> str:
    data = json.loads(json_text)

    lines = [
        data.get("summary", ""),
        "",
        "A more detailed description of the function, if necessary.",
        ""
    ]

    for k, v in data.get("args", {}).items():
        lines.append(f":param {k}: {v}")
        lines.append(f":type {k}: type")

    if data.get("returns"):
        lines.append("")
        lines.append(f":returns: {data['returns']}")
        lines.append(":rtype: type")

    return "\n".join(lines)
