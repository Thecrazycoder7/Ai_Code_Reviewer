import streamlit as st
import os
import ast
import pandas as pd
import json
from collections import defaultdict

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Code Dashboard",
    layout="wide",
    page_icon="⚡"
)

# ---------------- CSS ----------------

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
    .main-header {
        background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);
        padding: 1rem; border-radius: 12px; color: white;
        margin-bottom: 2rem; box-shadow: 0 4px 20px rgba(79, 70, 229, 0.2);
    }
    .pro-card {
        background: white; padding: 1.5rem; border-radius: 16px;
        border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease;
    }
    .pro-card:hover { transform: translateY(-5px); }
    .stat-val { font-size: 2rem; font-weight: 700; color: #1E293B; }
    .stat-label { color: #64748B; text-transform: uppercase; font-size: 0.75rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def get_functions(file_path):
    rows = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read().strip()
        if not code: return []
        code = "\n".join(line for line in code.splitlines() if not line.strip().startswith("```"))
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                doc = ast.get_docstring(node)
                rows.append({"Function": node.name, "Docstring": "Yes" if doc else "No"})
    except (SyntaxError, Exception):
        return []
    return rows

# ---------------- DATA LOADING ----------------
rows = []
folder = "examples"
if os.path.exists(folder):
    for file in os.listdir(folder):
        if file.endswith(".py"):
            rows.extend(get_functions(os.path.join(folder, file)))
functions_df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Function", "Docstring"])

# ---------------- UI ----------------
def dashboard():
    st.markdown('<div class="main-header"><h1>⚡ Pro Code Analytics</h1><p>Analyze your code quality, test results, and metrics in one place.</p></div>', unsafe_allow_html=True)
    
    json_path = "storage/reports/pytest_results.json"
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
        tests = data.get("tests", [])
        passed = sum(1 for t in tests if t.get("outcome") == "passed")
        failed = sum(1 for t in tests if t.get("outcome") == "failed")
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)

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

        with m_col1:
            st.markdown(stat_card(
                "SUCCESS RATE",
                f"{int((passed/len(tests))*100) if tests else 0}%",
                "#6366F1"
            ), unsafe_allow_html=True)

        with m_col2:
            st.markdown(stat_card(
                "PASSED",
                passed,
                "#10B981"
            ), unsafe_allow_html=True)

        with m_col3:
            st.markdown(stat_card(
                "FAILED",
                failed,
                "#EF4444"
            ), unsafe_allow_html=True)

        with m_col4:
            st.markdown(stat_card(
                "AVG DURATION",
                f"{round(data.get('duration', 0), 2)}s",
                "#F59E0B"
            ), unsafe_allow_html=True)


        # Charts Section
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📊 Tests by Category")
        modules = defaultdict(lambda: {"passed": 0, "failed": 0, "total": 0})
        for t in tests:
            module = t.get("nodeid", "unknown").split("::")[0].replace("tests/", "")
            outcome = t.get("outcome", "failed")
            modules[module][outcome] += 1
            modules[module]["total"] += 1
        
        chart_df = pd.DataFrame([{"Module": m, "Passed": v["passed"], "Failed": v["failed"]} for m, v in modules.items()])
        st.bar_chart(chart_df.set_index("Module"), color=["#10B981", "#EF4444"])
        
        with st.expander("🔍 View Detailed Module Table"):
            module_list = []
            for m, v in modules.items():
                module_list.append({"Module": m, "Total": v["total"], "Passed %": round((v["passed"]/v["total"])*100, 1) if v["total"] > 0 else 0})
            st.dataframe(pd.DataFrame(module_list), use_container_width=True)
    else:
        st.info("No test report found. Run pytest to see results.")
        st.code('pytest tests/ --json-report --json-report-file=storage/reports/pytest_results.json -v', language='bash')

    # Tabs Section
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Advanced Filter", "🔎 Search", "📤 Export", "💡 Help & Tips"])
    
    with tab1:
        status = st.selectbox("Select Docstring Status", ["All", "Yes", "No"])
        filtered_df = functions_df if status == "All" else functions_df[functions_df["Docstring"] == status]
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    with tab2:
        query = st.text_input("Search function name...")
        if query:
            res = functions_df[functions_df["Function"].str.contains(query, case=False)]
            st.dataframe(res, use_container_width=True)

    with tab3:
        c1, c2 = st.columns(2)
        c1.download_button("📥 Download JSON", functions_df.to_json(), "report.json", "application/json", use_container_width=True)
        c2.download_button("📄 Download CSV", functions_df.to_csv(), "report.csv", "text/csv", use_container_width=True)

    with tab4:
        st.markdown("##### 🆘 Help & Tips")

        r1c1, r1c2 = st.columns(2)
        r2c1, r2c2 = st.columns(2)

        with r1c1:
            st.info(
                """
                **⚡ Key Features**
                
                • Advanced Filter: Filter functions by docstring status  
                • Search: Find functions by name quickly  
                • Export: Download results as JSON or CSV  
                • Live Update: Data updates after scan
                """
            )

        with r1c2:
            st.success(
                """
                **📊 Coverage Guide**
                
                • 100% = All functions have docstrings  
                • < 100% = Some docstrings missing  
                • Follow PEP-257 for best quality  
                • Higher coverage = Better code
                """
            )

        with r2c1:
            st.warning(
                """
                **🧪 Testing Tips**
                
                • Run pytest before analysis  
                • Fix failed tests first  
                • Use JSON report for dashboard  
                • Re-run after changes
                """
            )

        with r2c2:
            st.info(
                """
                **🚀 Best Practices**
                
                • Write clear docstrings  
                • Keep functions small  
                • Avoid high complexity  
                • Maintain readable code
                """
            )
        st.markdown("----")
        with st.expander("🧭 Advanced Guide"):
            c1, c2 = st.columns(2)
            c3, c4 = st.columns(2)

            with c1:
                st.info(
                    """
                    **📦 Installation**
                    
                    • Install Python (3.9 or above)  
                    • Create virtual environment  
                    • Activate the environment  
                    • Install required packages
                    """
                )

            with c2:
                st.success(
                    """
                    **▶️ Run Application**
                    
                    • Go to project folder  
                    • Activate virtual environment  
                    • Run Streamlit command  
                    • App opens in browser
                    """
                )

            with c3:
                st.warning(
                    """
                    **🧪 Run Tests**
                    
                    • Make sure pytest is installed  
                    • Run tests from terminal  
                    • Generate JSON test report  
                    • Check results in Dashboard
                    """
                )

            with c4:
                st.info(
                    """
                    **📊 After Testing**
                    
                    • Open Dashboard tab  
                    • Review pass / fail stats  
                    • Check complexity & metrics  
                    • Fix issues and re-run tests
                    """
                )
if __name__ == "__main__":
    dashboard()