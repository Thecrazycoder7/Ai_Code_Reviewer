import streamlit as st
from core.parser.python_parser import parse_path
from core.docstring_engine.generator import generate_google_docstring
from core.reporter.coverage_reporter import compute_coverage

# Upload file or folder
uploaded_file = st.file_uploader("Upload Python file or zip folder", type=["py", "zip"])

generate_docs = st.checkbox("Generate missing docstrings")

if uploaded_file:
    run_scan = st.button("Run Milestone 1 Scan")

    if run_scan:
        # Save uploaded file temporarily
        with open("temp.py", "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Run the existing CLI functions
        results = parse_path("temp.py")
        # Attach generated docstrings if checkbox checked
        if generate_docs:
            for f in results:
                for fn in f.get("functions", []):
                    if not fn.get("has_docstring"):
                        fn["generated_docstring"] = generate_google_docstring(fn)

        # Compute coverage
        report = compute_coverage(results)

        # Show coverage
        st.success(f"Docstring Coverage: {report['aggregate']['coverage_percent']}%")

        # Show generated docstrings in tab
        tab1, tab2 = st.tabs(["📝 Generated Docstrings", "📊 Coverage Report"])
        with tab1:
            for f in results:
                for fn in f.get("functions", []):
                    doc = fn.get("docstring") or fn.get("generated_docstring") or "No docstring"
                    st.code(f"{fn['name']}():\n{doc}")
        with tab2:
            st.json(report)
