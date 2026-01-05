import streamlit as st
import os
import ast
import pandas as pd
import json

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Code Dashboard",
    layout="wide",
    page_icon="⚡"
)

# ---------------- CSS ----------------
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #f3f2ff, #faf9ff);
    font-family: Segoe UI, sans-serif;
}

.main {
    padding: 25px;
}

/* ONE COMMON CARD STYLE */
.card {
    padding: 24px;
    border-radius: 5px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.12);
    margin-bottom: 30px;
}

.header {
    background: #6c4dfc; /* violet */
    color: white;
}


/* TABS */
.stTabs [data-baseweb="tab"] {
    background: #e5e7eb;
    border-radius: 8px;
    padding: 8px 16px;
}

.stTabs [aria-selected="true"] {
    background: #6c4dfc;
    color: white;
}

/* BUTTON */
.stButton button {
    background: #6c4dfc;
    color: white;
    border-radius: 8px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def get_functions(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    rows = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            rows.append({
                "Function": node.name,
                "Docstring": "Yes" if ast.get_docstring(node) else "No",
                "File": os.path.basename(file_path)
            })
    return rows

# ---------------- LOAD DATA ----------------
rows = []
folder = "examples"
if os.path.exists(folder):
    for file in os.listdir(folder):
        if file.endswith(".py"):
            rows.extend(get_functions(os.path.join(folder, file)))

functions_df = pd.DataFrame(rows)

# ---------------- UI ----------------

def dashboard():
    st.markdown(f"""
            <h2 class="card header" style="padding: 20px; margin-bottom: 30px; background: #6c4dfc; color: white;">
                ⚡AI Code Dashboard
            </h2>
         """, unsafe_allow_html=True)

    # SECTION TITLE (NO CARD HERE)
    st.subheader("📊 Test Reports")

    # Path to reports folder
    report_folder = "storage/reports"
    logs_file = os.path.join(report_folder, "review_logs.json")

    # Read the JSON file
    if os.path.exists(logs_file):
        with open(logs_file, "r") as f:
            logs = json.load(f)  # this should be a list of dicts

        # Convert to DataFrame
        df = pd.DataFrame(logs)
        df = df.rename(columns={"file": "File", "passed": "Passed", "failed": "Failed"})
        df = df.set_index("File")

        st.bar_chart(df)
    else:
        st.info("No review_logs.json file found in storage/reports/")
  

    # TABS
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Advanced Filter", "Search", "Export", "Help"]
    )

    with tab1:
        st.markdown(f"""
            <h4 class="card" style="padding: 20px; margin-bottom: 30px; background: #6c4dfc; color: white;">
                Docstring Status
            </h4>
         """, unsafe_allow_html=True)
        status = st.selectbox("Docstring Status", ["All", "Yes", "No"])
        data = functions_df if status == "All" else functions_df[functions_df["Docstring"] == status]
        st.dataframe(data)

    with tab2:
        st.markdown(f"""
            <h4 class="card" style="padding: 20px; margin-bottom: 30px; background: #6c4dfc; color: white;">
                Search function
            </h4>
         """, unsafe_allow_html=True)
        
        # Search input
        query = st.text_input("Enter function name to search")

        if query:
            # Filter functions_df by function name (case-insensitive)
            result = functions_df[functions_df["Function"].str.contains(query, case=False, na=False)]
            if not result.empty:
                st.dataframe(result)
            else:
                st.info(f"No functions found matching '{query}'")

    with tab3:
        st.markdown(f"""
            <h4 class="card" style="padding: 20px; margin-bottom: 30px; background: #6c4dfc; color: white;">
                Export Reports
            </h4>
         """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        # Export JSON
        with col1:
            json_data = functions_df.to_json(orient="records", indent=4)  # convert DataFrame to JSON string
            st.download_button(
                label="Export JSON",
                data=json_data,
                file_name="functions_report.json",
                mime="application/json"
            )

        # Export CSV (optional) or PDF placeholder
        with col2:
            csv_data = functions_df.to_csv(index=False)
            st.download_button(
                label="Export CSV",
                data=csv_data,
                file_name="functions_report.csv",
                mime="text/csv"
            )

        # PDF export placeholder
        st.info("PDF export not implemented yet.")

    with tab4:
        st.markdown(f"""
            <h4 class="card" style="padding: 20px; margin-bottom: 30px; background: #6c4dfc; color: white;">
                Helps & tips
            </h4>
         """, unsafe_allow_html=True)
        # Create 4 cards in 2 rows
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)

        # Card style
        card_style = "padding:20px; border-radius:10px; background:#f0f4ff; box-shadow:0 4px 10px rgba(0,0,0,0.1); margin-bottom:20px;"

        with row1_col1:
            st.markdown(f"""
                <div style="{card_style}">
                    <h5>⚡ Key Features</h5>
                    <ul>
                        <li>Advanced Filters: Filter functions by docstring status.</li>
                        <li>Search: Find functions by name quickly.</li>
                        <li>Export: Download results in JSON/CSV formats.</li>
                        <li>Help & Tips: Understand how the tool works.</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

        with row1_col2:
            st.markdown(f"""
                <div style="{card_style}">
                    <h5>📊 Coverage Metrics</h5>
                    <ul>
                        <li>Shows documented vs undocumented functions.</li>
                        <li>Example: 100% means all functions have docstrings.</li>
                        <li>Real-time update as files are analyzed.</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

        with row2_col1:
            st.markdown(f"""
                <div style="{card_style}">
                    <h5>📝 Function Status</h5>
                    <ul>
                        <li>Yes: Function has a docstring.</li>
                        <li>No: Function does not have a docstring.</li>
                        <li>Use Advanced Filter to focus on specific functions.</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

        with row2_col2:
            st.markdown(f"""
                <div style="{card_style}">
                    <h5>✅ Test Results</h5>
                    <ul>
                        <li>Shows per-file passed and failed test counts.</li>
                        <li>Bar chart updates in real-time.</li>
                        <li>Helps identify functions needing attention.</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    dashboard()