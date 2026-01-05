import streamlit as st
import os
import ast
import pandas as pd
import altair as alt
import json

from core.reporter.coverage_reporter import compute_coverage, write_report

from dashboard.dashboard_app import dashboard
from core.parser.python_parser import parse_path
from core.validator.validator import validate_docstrings, compute_complexity, compute_maintainability
# from core.metrics.maintainability import compute_maintainability
from core.docstring_engine.generator import (
    json_to_google_docstring,
    json_to_numpy_docstring,    
    json_to_rest_docstring,
    analyze_file_with_groq,
    analyze_function_with_groq,
)
# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="AI Code Reviewer", layout="wide", page_icon="🔍")

# ------------------ CUSTOM CSS ------------------
st.markdown("""
<style>

/* ---------- GLOBAL ---------- */
body {
    background: linear-gradient(135deg, #f3f2ff, #faf9ff);
    font-family: "Segoe UI", sans-serif;
}

/* ---------- SIDEBAR ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #6c4dfc, #4b2fd6);
    padding: 5px;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label {
    color: white !important;
}


/* ---------- PAGE CONTAINER ---------- */
.main {
    padding: 25px;
}

/* ---------- CARDS ---------- */
.card {
    background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
    color: #111827;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.12);
    margin-bottom: 20px;
    transition: 0.3s ease;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 18px 40px rgba(0,0,0,0.18);
}

/* ---------- METRIC CARDS ---------- */
.metric {
    background: linear-gradient(135deg, #ede9ff, #f6f4ff);
    padding: 18px;
    border-radius: 16px;
    text-align: center;
    font-size: 18px;
    font-weight: 600;
    box-shadow: 0 8px 18px rgba(108,77,252,0.25);
}

/* ---------- BUTTONS ---------- */
.stButton button {
    background: linear-gradient(135deg, #6c4dfc, #4b2fd6);
    color: white;
    border-radius: 12px;
    padding: 10px 18px;
    font-weight: bold;
    border: none;
    box-shadow: 0 6px 16px rgba(0,0,0,0.25);
}

.stButton button:hover {
    transform: scale(1.05);
    background: linear-gradient(135deg, #7d66ff, #563de6);
}

/* ---------- INPUTS ---------- */
input, textarea, select {
    border-radius: 10px !important;
    padding: 8px !important;
}

/* ---------- TABS ---------- */
.stTabs [data-baseweb="tab"] {
    background: #ede9ff;
    border-radius: 12px;
    margin-right: 6px;
    padding: 10px 18px;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: #6c4dfc;
    color: white;
}

/* ---------- TABLE ---------- */
.dataframe {
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}

/* ---------- CODE BLOCK ---------- */
pre {
    border-radius: 5px;
    background: #1e1e2f;
    color: #f8f8f2;
}

</style>
""", unsafe_allow_html=True)

total = documented = coverage = 0
# ------------------ HELPERS ------------------
def split_docstrings(text):
    google = numpy = rest = ""
    if "[GOOGLE]" in text: google = text.split("[GOOGLE]")[1].split("[NUMPY]")[0].strip()
    if "[NUMPY]" in text: numpy = text.split("[NUMPY]")[1].split("[REST]")[0].strip()
    if "[REST]" in text: rest = text.split("[REST]")[1].strip()
    return google, numpy, rest

def save_code_to_file(file_name: str, code: str):
    try:
        if not file_name: st.error("No file name found."); return
        os.makedirs("examples", exist_ok=True)
        file_path = os.path.join("examples", file_name)
        with open(file_path, "w", encoding="utf-8") as f: f.write(code)
        st.success(f"File updated successfully: {file_name}")
    except Exception as e: st.error(f"Error saving file: {e}")

def clean_code(code: str) -> str:
    return "\n".join(line for line in code.splitlines() if not line.strip().startswith("```"))

def insert_docstring_clean(code, node, docstring_text):
    try:
        lines = code.split("\n")
        # Remove old docstring
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, (ast.Str, ast.Constant)):
            doc_node = node.body[0]
            lines[doc_node.lineno-1:doc_node.end_lineno] = []
        # Insert new docstring
        def_line_idx = node.lineno-1
        indent = " "*(node.col_offset+4)
        doc_lines = [f'{indent}"""'] + [f"{indent}{line}" for line in docstring_text.split("\n")] + [f'{indent}"""']
        lines[def_line_idx+1:def_line_idx+1] = doc_lines
        return "\n".join(lines)
    except Exception as e: st.error(f"Error inserting docstring: {e}"); return code


# ------------------ SESSION STATE ------------------
for key in ["scanned","code","file_name","page","updated_code"]:
    if key not in st.session_state: st.session_state[key] = False if key=="scanned" else "" if key=="code" else None

# ------------------ SIDEBAR ------------------
st.sidebar.title("</> AI Reviewer")
options = ["🏠 Home", "📝 Docstring", "✅ Validation", "📐 Metrics", "⚡Dashboard"]
st.session_state.page = st.sidebar.radio("Navigate to", options, index=options.index(st.session_state.page) if st.session_state.page in options else 0)

uploaded_file = st.sidebar.file_uploader("Choose a Python file", type=["py"])
examples_folder = "examples"
if uploaded_file:
    st.session_state.code = uploaded_file.read().decode("utf-8")
    st.session_state.file_name = uploaded_file.name
    st.session_state.scanned = True
    st.session_state.updated_code = st.session_state.code
elif os.path.exists(examples_folder):
    files = [f for f in os.listdir(examples_folder) if f.endswith(".py")]
    if files:
        selected = st.sidebar.selectbox("Or select an example file", files)
        with open(os.path.join(examples_folder, selected), "r", encoding="utf-8") as f: st.session_state.code = f.read()
        st.session_state.file_name = selected
        st.session_state.scanned = True
        st.session_state.updated_code = st.session_state.code

# ------------------ PARSE CODE ------------------
funcs = []
cleaned_code = ""
if st.session_state.scanned and st.session_state.code:
    cleaned_code = clean_code(st.session_state.code)
    try: funcs = parse_path(file_content=cleaned_code)
    except Exception as e: st.error(f"Syntax error: {e}"); st.stop()

parsed_files = []
if st.session_state.scanned and st.session_state.file_name:
    parsed_files = [{
        "file_path": os.path.join("examples", st.session_state.file_name)
    }]


# ------------------ PAGES ------------------
page = st.session_state.page

if page == "🏠 Home":
    st.markdown(f"""
            <h3 class="card" style="padding: 20px; margin-bottom: 30px; background: #6c4dfc; color: white;">
                🏠 Home
            </h3>
         """, unsafe_allow_html=True)
    if not st.session_state.scanned:
        st.info("Upload or select a Python file.")
    else:
        total = len(funcs)
        documented = len([f for f in funcs if f.get("docstring")])
        coverage = int((documented/total)*100) if total else 0
        col1,col2,col3 = st.columns(3)

        with col1:
            st.markdown(
                f"""
                <div class="card">
                    <h4>Total Functions</h4>
                    <h2>{total}</h2>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""
                <div class="card">
                    <h4>Documented</h4>
                    <h2>{documented}</h2>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                f"""
                <div class="card">
                    <h4>Coverage</h4>
                    <h2>{coverage}%</h2>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(f"""
            <h3 class="card" style="padding: 20px; margin-top: 30px; background: #6c4dfc; color: white;">
                📄 Current Code
            </h3>
         """, unsafe_allow_html=True)
        st.code(st.session_state.updated_code or st.session_state.code, language="python")
        

elif page == "📝 Docstring":
    st.markdown(f"""
            <h3 class="card" style="padding: 20px; margin-bottom: 30px; background: #6c4dfc; color: white;">
                📝 Docstring Review
            </h3>
         """, unsafe_allow_html=True)
    if not funcs: st.warning("No functions found."); st.stop()
    current_code = st.session_state.updated_code or st.session_state.code
    tree = ast.parse(current_code)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    names = [f.name for f in functions]
    if not names: st.warning("No functions found."); st.stop()

    selected = st.selectbox("Select a function to review", names)
    node = next((f for f in functions if f.name==selected), None)
    if "last_selected" not in st.session_state or st.session_state.last_selected != selected:
        st.session_state.last_selected = selected
        with st.spinner("Generating docstrings..."):
            raw_output = analyze_function_with_groq(node, current_code)
            google_doc, numpy_doc, rest_doc = split_docstrings(raw_output)
            st.session_state.google_doc = google_doc
            st.session_state.numpy_doc = numpy_doc
            st.session_state.rest_doc = rest_doc

    google_doc = st.session_state.get("google_doc","No docstring generated")
    numpy_doc = st.session_state.get("numpy_doc","No docstring generated")
    rest_doc = st.session_state.get("rest_doc","No docstring generated")

    col1,col2 = st.columns(2)
    with col1: st.subheader("📖 Before"); st.code(ast.get_docstring(node) or "No docstring")
    with col2:
        st.subheader("✨ After")
        tabs = st.tabs(["Google","NumPy","reST"])
        with tabs[0]: st.code(google_doc)
        with tabs[1]: st.code(numpy_doc)
        with tabs[2]: st.code(rest_doc)

    selected_style = st.selectbox("Choose style to apply", ["Google","NumPy","reST"])
    accepted_doc = {"Google": google_doc, "NumPy": numpy_doc, "reST": rest_doc}.get(selected_style, google_doc)

    colA,colB = st.columns(2)
    with colA:
        if st.button("✅ Accept & Apply"):
            new_code = insert_docstring_clean(current_code, node, accepted_doc)
            st.session_state.updated_code = new_code
            st.session_state.code = new_code
            save_code_to_file(st.session_state.file_name, new_code)
            st.success("Docstring applied successfully!")
            st.rerun()
    with colB:
        if st.button("❌ Reject"): st.info("Docstring rejected.")
elif page == "✅ Validation":
    st.markdown(f"""
            <h3 class="card" style="padding: 20px; margin-bottom: 30px; background: #6c4dfc; color: white;">
                ✅ Validation
            </h3>
         """, unsafe_allow_html=True)
    if not parsed_files:
        st.info("Please scan a file first.")
    else:
        st.subheader("📂 Files")

        for f in parsed_files:
            file_path = f["file_path"]
            violations = validate_docstrings(file_path)

            pep_status = "🟢 OK" if not violations else "🔴 Fix"

            if st.button(
                f"{os.path.basename(file_path)}   {pep_status}",
                key=f"val_btn_{file_path}"
            ):
                st.session_state["validation_file"] = file_path

        st.markdown("---")

        selected_file = st.session_state.get("validation_file")
        if selected_file:
            violations = validate_docstrings(selected_file)

            st.bar_chart({
                "Compliant": 1 if not violations else 0,
                "Violations": len(violations)
            })

            if not violations:
                st.success("✅ No PEP-257 issues")
            else:
                for v in violations:
                    st.error(
                        f"{v['code']} (line {v['line']}): {v['message']}"
                    )


elif page == "📐 Metrics":
    st.markdown(f"""
            <h3 class="card" style="padding: 20px; margin-bottom: 30px; background: #6c4dfc; color: white;">
                📐 Metrics
            </h3>
    """, unsafe_allow_html=True)

    if not parsed_files:
        st.info("Run a scan first")
    else:
        file_paths = [f["file_path"] for f in parsed_files]
        selected_file = st.selectbox("Select File", file_paths)

        with open(selected_file, "r", encoding="utf-8") as f:
            src = f.read()

        st.metric("Maintainability Index", compute_maintainability(src))
        st.json(compute_complexity(src))



elif page == "⚡Dashboard":
    dashboard()

# -------------------------------------------------
# DOWNLOAD
# -------------------------------------------------
if coverage:
    st.markdown("---")
    st.download_button(
        "Download Coverage Report JSON",
        data=json.dumps(coverage, indent=2),
        file_name="review_report.json",
        mime="application/json"
    )