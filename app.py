import streamlit as st
from agents import run_schema_evolution
from db_utils import fetch_current_schema, execute_sql
from db_utils import fetch_current_schema

st.set_page_config(page_title="SchemaEvolutionAgent", page_icon="🗄️", layout="wide")

st.title("🗄️ SchemaEvolutionAgent")
st.markdown("""
Agentic AI System for Safe Database Schema Evolution and Migration.
Powered by **CrewAI**, **Groq**, and **PostgreSQL**.
""")

# Sidebar to show current database state
with st.sidebar:
    st.header("Database Context")
    if st.button("Refresh Schema"):
        try:
            schema = fetch_current_schema()
            st.code(schema, language="sql")
        except Exception as e:
            st.error(f"Error details: {e}")

# Main Interface
# Main Interface
st.subheader("Migration Request")
user_request = st.text_area(
    "Describe the schema change you want to make:",
    placeholder="e.g., Split the 'users' table into 'users' and 'user_profiles'...",
    height=100
)

# 1. Teach Streamlit to remember the AI's report
if 'final_report' not in st.session_state:
    st.session_state.final_report = None

# 2. Generate the plan and save it to memory
if st.button("Generate Migration Plan", type="primary"):
    if not user_request:
        st.warning("Please enter a migration request.")
    else:
        with st.spinner("Agents are analyzing schema, planning migration, and validating..."):
            # Run the multi-agent workflow and save to session state
            st.session_state.final_report = run_schema_evolution(user_request)

# 3. If a report exists in memory, display it AND the execution box
if st.session_state.final_report:
    st.success("Migration Plan Generated!")
    st.markdown("### Agent Output Report")
    st.markdown(str(st.session_state.final_report))

   # --- NEW EXECUTION & ROLLBACK UI ---
    st.markdown("---")
    
    # Create two columns for a side-by-side layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 Execute Migration")
        st.info("Paste the **UP MIGRATION** code below to apply changes.")
        
        sql_to_run = st.text_area("UP MIGRATION Script:", height=200, key="up_sql")
        
        if st.button("Run UP Migration", type="primary"):
            if sql_to_run:
                with st.spinner("Executing on cloud database..."):
                    success, message = execute_sql(sql_to_run)
                    if success:
                        st.success("✅ Migration executed successfully!")
                    else:
                        st.error(f"Database Error: {message}")
            else:
                st.warning("Please paste the UP MIGRATION script first.")

    with col2:
        st.subheader("🚨 Emergency Rollback")
        st.warning("Mistakes happen! Paste the **DOWN MIGRATION** code below to revert.")
        
        rollback_sql = st.text_area("DOWN MIGRATION Script:", height=200, key="down_sql")
        
        # Standard button type so it looks different from the primary action
        if st.button("Run Rollback"):
            if rollback_sql:
                with st.spinner("Reverting cloud database changes..."):
                    success, message = execute_sql(rollback_sql)
                    if success:
                        st.success("⏪ Rollback successful! Database restored.")
                    else:
                        st.error(f"Rollback Error: {message}")
            else:
                st.warning("Please paste the DOWN MIGRATION script first.")