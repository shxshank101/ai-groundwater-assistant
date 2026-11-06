"""Explore Government Reports - semantic search across all indexed reports."""
import streamlit as st

import ui

ui.setup_page("Explore Government Reports", "Search inside the indexed reports and jump to the exact page.")
pipeline = ui.get_pipeline()
store = pipeline.store

if store.count() == 0:
    st.warning("No reports indexed yet. Add PDFs in **Document Library**.")
    st.stop()

docs = store.documents()
c1, c2 = st.columns([3, 1])
query = c1.text_input("What are you looking for?", placeholder="e.g. stage of groundwater extraction Punjab")
scope = c2.selectbox("Report", ["All reports"] + docs)
count = st.slider("Results", 3, 15, 6)

if query.strip():
    with st.spinner("Searching..."):
        hits = store.search(query, top_k=count, document=None if scope == "All reports" else scope)
    if not hits:
        st.info("No matching passages.")
    for h in hits:
        with st.container(border=True):
            st.markdown(f"**{h['document']}** · page {h['page']} · relevance {h['score']:.2f}")
            st.write(h["text"])
