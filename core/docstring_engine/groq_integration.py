# llm_generator.py
import os
import json
import dotenv
from groq import Groq
from core.docstring_engine.generator import to_google, to_numpy, to_rest

dotenv.load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_placeholder_docstring(fn_info: dict, style: str) -> str:
    """
    Generates docstring using LLM + formatter.
    Returns formatted docstring text (NOT triple quotes).
    """
    prompt = f"""
Analyze this Python function:
Name: {fn_info['name']}
Args: {fn_info['args']}
Returns: {fn_info['returns']}

Return JSON with:
summary: str,
arg_descs: {{ "arg_name": {{ "description": str, "inferred_type": str }} }},
ret_desc: str,
ret_type_inferred: str
"""

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"} # FORCES GROQ TO RETURN JSON
        )
        raw = res.choices[0].message.content
        content = json.loads(raw)

        formatters = {"google": to_google, "numpy": to_numpy, "rest": to_rest}
        return formatters[style.lower()](fn_info, content)
    except Exception as e:
        return f"Error: {str(e)}"
