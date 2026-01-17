from click import style
import streamlit as st
import os
import ast
import pandas as pd
import altair as alt
import json

from core.reporter.coverage_reporter import compute_coverage, write_report
from dashboard.dashboard import dashboard
from core.parser.python_parser import parse_path
from core.validator.validator import summarize_complexity, validate_docstrings, compute_maintainability_single
from core.docstring_engine.groq_integration import generate_placeholder_docstring
# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="AI Code Reviewer", layout="wide", page_icon="🔍")

# ------------------ CUSTOM CSS ------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
        .main-header {
            background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);
            padding: 1rem; border-radius: 12px; color: white;
            margin-bottom: 2rem; box-shadow: 0 4px 20px rgba(79, 70, 229, 0.2);
        }
        .pro-pro-card {
            background: white; padding: 1.2rem; border-radius: 16px;
            border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s ease;
        }
        .pro-pro-card:hover { transform: translateY(-5px); }
        .stat-val { font-size: 2rem; font-weight: 700; color: #1E293B; }
        .stat-label { color: #64748B; text-transform: uppercase; font-size: 0.75rem; font-weight: 600; }
        .code-box {
            border-radius: 14px;
            padding: 14px;
            background: white;
            box-shadow: 0 6px 16px rgba(0,0,0,0.06);
        }

        .before-box {
            border-left: 6px solid #EF4444;
        }

        .after-box {
            border-left: 6px solid #10B981;
        }
        /* Sidebar background */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #7C3AED, #5B21B6);
            color: white;
        }

        /* Sidebar title */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        .sidebar-title {
            color: white !important;
            font-size: 24px;
            font-weight: 700;
        }

        /* Radio labels (menu items) */
        section[data-testid="stSidebar"] label {
            color: #EDE9FE !important;   /* light white */
            font-weight: 600;
            padding: 8px 12px;
            border-radius: 8px;
        }

        /* Hover */
        section[data-testid="stSidebar"] label:hover {
            color: #FFFFFF !important;
        }

        /* Selected item */
        section[data-testid="stSidebar"] input:checked + div {
            color: #FFFFFF !important;
            font-weight: 700;
        }

        /* Upload text */
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {
            color: #EDE9FE !important;
        }
        .stat-val { font-size: 2rem; font-weight: 700; color: #1E293B; }
        .stat-label { color: #64748B; text-transform: uppercase; font-size: 0.75rem; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

def stat_card(title, value, color):
            return f"""
            <div style="
                background: white;
                padding: 16px 18px;
                border-radius: 10px;
                border-left: 4px solid {color};
                box-shadow: 0 2px 6px rgba(0,0,0,0.06);
            ">
                <div style="
                    font-size: 12px;
                    font-weight: 600;
                    color: #64748B;
                    letter-spacing: 0.04em;
                ">
                    {title}
                </div>
                <div style="
                    font-size: 30px;
                    font-weight: 700;
                    color: #0F172A;
                    margin-top: 6px;
                ">
                    {value}
                </div>
            </div>
            """

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

def insert_docstring_clean(code: str, node, docstring: str) -> str:
    lines = code.splitlines()
    
    # 1. Identify where to start and end removal of old docstring
    start_line = node.lineno # This is the 'def' line
    body = node.body
    
    # 2. Check if the first statement in the body is already a docstring
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, (ast.Str, ast.Constant)):
        # Remove the lines occupied by the existing docstring
        old_ds_start = body[0].lineno - 1
        old_ds_end = body[0].end_lineno
        del lines[old_ds_start:old_ds_end]
    
    # 3. Calculate insertion point (immediately after the 'def' line)
    # We use node.lineno because lines is 0-indexed and node.lineno is 1-indexed
    insert_at = node.lineno 
    indent = " " * (node.col_offset + 4)

    # 4. Format with triple quotes correctly
    doc_lines = [f'{indent}"""{line}"""' if len(docstring.splitlines()) == 1 else f'{indent}"""']
    if len(docstring.splitlines()) > 1:
        for line in docstring.splitlines():
            doc_lines.append(f"{indent}{line}")
        doc_lines.append(f'{indent}"""')

    lines[insert_at:insert_at] = doc_lines
    return "\n".join(lines)

# ------------------ SESSION STATE ------------------
for key in ["scanned","code","file_name","page","updated_code"]:
    if key not in st.session_state: st.session_state[key] = False if key=="scanned" else "" if key=="code" else None

# ------------------ SIDEBAR ------------------
st.sidebar.markdown(
    '<div class="sidebar-title">🖥️ AI Reviewer</div>',
    unsafe_allow_html=True
)

options = ["🏠 Home", "📝 Docstring", "✅ Validation", "📐 Metrics", "⚡ Dashboard"]
st.session_state.page = st.sidebar.radio(
    "Navigation",
    options,
    label_visibility="collapsed"
)

uploaded_file = st.sidebar.file_uploader("Upload Python file", type=["py"])
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
    st.markdown(
    '<div class="main-header"><h1>⚡AI Code Reviewer</h1><p tyle="color: #A0AEC0;>Automatically check your code for errors, style, and best practices.</p></div>',
    unsafe_allow_html=True
)

    if not st.session_state.scanned:
        st.info("Upload or select a Python file.")
    else:
        total = len(funcs)
        documented = len([f for f in funcs if f.get("docstring")])
        coverage = int((documented/total)*100) if total else 0
        col1,col2,col3 = st.columns(3)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                stat_card("TOTAL FUNCTIONS", total, "#6366F1"),
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                stat_card("DOCUMENTED", documented, "#10B981"),
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                stat_card("COVERAGE", f"{coverage}%", "#F59E0B"),
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.markdown(f"""
                    <h3 class="pro-card" style="padding: 20px; margin-top: 30px; background: #6c4dfc; color: white;">
                        📄 Current Code
                    </h3>
                """, unsafe_allow_html=True)
        st.code(st.session_state.updated_code or st.session_state.code, language="python")
                

elif page == "📝 Docstring":
    st.markdown(f"""
            <div class="main-header"><h3>
                📝 Docstring
            </h3>
            <p style="color: #A0AEC0;">Write clear descriptions for functions and classes to make code easier to understand.</p></div>
         """, unsafe_allow_html=True)

    if not funcs:
        st.warning("No functions found.")
        st.stop()

    current_code = st.session_state.get("updated_code", st.session_state.get("code", ""))
    tree = ast.parse(current_code)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    names = [f.name for f in functions]

    if not names:
        st.warning("No functions found.")
        st.stop()

    selected = st.selectbox("Select a function to review", names)
    node = next((f for f in functions if f.name == selected), None)

    # Generate placeholder docstrings once per selection
    if st.session_state.get("last_selected") != selected:
        st.session_state.last_selected = selected
        fn_info = {
            "name": node.name,
            "args": [{"name": arg.arg, "annotation": ast.unparse(arg.annotation) if arg.annotation else None} for arg in node.args.args],
            "returns": ast.unparse(node.returns) if node.returns else None,
        }

        st.session_state.google_doc = generate_placeholder_docstring(fn_info, "google")
        st.session_state.numpy_doc  = generate_placeholder_docstring(fn_info, "numpy")
        st.session_state.rest_doc   = generate_placeholder_docstring(fn_info, "rest")

    google_doc = st.session_state.get("google_doc", "No docstring generated")
    numpy_doc  = st.session_state.get("numpy_doc", "No docstring generated")
    rest_doc   = st.session_state.get("rest_doc", "No docstring generated")

    # Show Before / After
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="code-box before-box"">
            <h4>📖 Before</h4>
        </div>
        """, unsafe_allow_html=True)

        before_code = ast.get_docstring(node) or "No docstring"
        st.code(before_code, language="python")

    with col2:
        st.markdown("""
        <div class="code-box after-box">
            <h4>✨ After</h4>
        </div>
        """, unsafe_allow_html=True)

        tabs = st.tabs(["Google", "NumPy", "reST"])
        with tabs[0]:
            st.code(google_doc, language="python")
        with tabs[1]:
            st.code(numpy_doc, language="python")
        with tabs[2]:
            st.code(rest_doc, language="python")

        # Select style to apply
        st.markdown("---")
        st.subheader("Select Docstring Style to Apply")
        selected_style = st.selectbox("Choose style to apply", ["Google", "NumPy", "reST"])
        accepted_doc = {"Google": google_doc, "NumPy": numpy_doc, "reST": rest_doc}.get(selected_style, google_doc)

        # Accept / Reject buttons
        colA, colB = st.columns(2)
        with colA:
            if st.button("✅ Accept"):
                new_code = insert_docstring_clean(current_code, node, accepted_doc)
                st.session_state.updated_code = new_code
                st.session_state.code = new_code
                save_code_to_file(st.session_state.file_name, new_code)
                st.success("Docstring applied successfully!")
                st.rerun()
        with colB:
            if st.button("❌ Reject"):
                st.info("Docstring rejected.")

elif page == "✅ Validation":
    st.markdown(f"""
            <div class="main-header"><h3>
                ✅ Validation
            </h3>
            <p style="color: #A0AEC0;">Ensure your code works correctly and meets all requirements.</p></div>
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
            
            st.subheader("📊Compliance Overview")
            c1, c2 = st.columns(2)

            with c1:
                st.markdown(
                    stat_card("COMPLIANT", 1 if not violations else 0, "#10B981"),
                    unsafe_allow_html=True
                )

            with c2:
                st.markdown(
                    stat_card("VIOLATIONS", len(violations), "#EF4444"),
                    unsafe_allow_html=True
                )
            st.markdown("---")
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
    st.markdown(
        '<div class="main-header"><h1>📐 Code Quality Metrics</h1><p style="color: #A0AEC0;">Track code health, complexity, and performance to improve your projects.</p></div>',
        unsafe_allow_html=True
    )

    # Get latest code
    current_code = st.session_state.get("updated_code") or st.session_state.get("code")

    if not current_code or current_code.strip() == "":
        st.info("The selected file is empty. Please upload code with functions (def).")
    else:
        # ---------------- MAINTAINABILITY ----------------
        mi_data = compute_maintainability_single(current_code)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                stat_card(
                    "MAINTAINABILITY",
                    mi_data["score"],
                    "#6366F1"
                ),
                unsafe_allow_html=True
            )

        # ---------------- COMPLEXITY ----------------
        complexity = summarize_complexity(current_code)

        if "per_function" in complexity:
            with col2:
                st.markdown(
                    stat_card(
                        "AVG COMPLEXITY",
                        complexity["average_complexity"],
                        "#F59E0B"
                    ),
                    unsafe_allow_html=True
                )

            with col3:
                risk_color = "#EF4444" if complexity["risk_level"] == "High" else "#10B981"
                st.markdown(
                    stat_card(
                        "RISK LEVEL",
                        complexity["risk_level"],
                        risk_color
                    ),
                    unsafe_allow_html=True
                )

            st.markdown("---")
            st.subheader("📊 Function Breakdown")
            st.json(complexity["per_function"])

        else:
            st.warning(f"⚠️ {complexity.get('info', 'Analysis Error')}")
            if "error" in complexity:
                st.error(f"Syntax Error: {complexity['error']}")

            with st.expander("View Code"):
                st.code(current_code, language="python")

elif page == "⚡ Dashboard":
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