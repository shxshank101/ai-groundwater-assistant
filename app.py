"""
app.py - entry point.  Run with:  streamlit run app.py
Sets up the sidebar navigation and shows the selected page.
"""
import streamlit as st

import config

st.set_page_config(page_title=config.PROJECT_NAME, page_icon="💧", layout="wide")

pages = [
    st.Page("pages/dashboard.py", title="Home Dashboard", icon="🏠", default=True),
    st.Page("pages/chatbot.py", title="AI Groundwater Assistant", icon="💬"),
    st.Page("pages/analytics.py", title="Groundwater Analytics", icon="📈"),
    st.Page("pages/reports.py", title="Explore Government Reports", icon="🔎"),
    st.Page("pages/documents.py", title="Document Library", icon="📚"),
    st.Page("pages/sources.py", title="Data Sources", icon="🗂️"),
    st.Page("pages/about.py", title="About Project", icon="ℹ️"),
]
nav = st.navigation(pages)

with st.sidebar:
    st.markdown("### 💧 Groundwater Assistant")
    st.caption(f"{config.PROJECT_ID} · Team {config.TEAM_NAME}")

nav.run()
