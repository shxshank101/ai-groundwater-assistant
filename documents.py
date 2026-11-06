"""Document Library - upload, process, list, search and remove PDF reports."""
import pandas as pd
import streamlit as st

import config
import ui
from modules.rag_pipeline import load_registry

ui.setup_page("Document Library", "Upload government PDF reports. Text and page numbers are indexed for the chatbot.")
pipeline = ui.get_pipeline()

st.subheader("Upload a PDF")
with st.form("upload", clear_on_submit=True):
    files = st.file_uploader("PDF reports", type=["pdf"], accept_multiple_files=True)
    c1, c2, c3 = st.columns(3)
    url = c1.text_input("Original source URL (recommended)")
    org = c2.text_input("Organization", placeholder="e.g. Central Ground Water Board")
    year = c3.text_input("Publication year")
    go = st.form_submit_button("Process and index")

if go:
    if not files:
        st.error("Choose at least one PDF first.")
    for f in files or []:
        if f.size > 200 * 1024 * 1024:
            st.error(f"{f.name}: larger than 200 MB.")
            continue
        dest = config.PDF_DIR / f.name
        dest.write_bytes(f.getbuffer())
        with st.spinner(f"Processing {f.name} (extracting, chunking, embedding)..."):
            rec = pipeline.ingest_pdf(dest, url, org, year)
        if rec["status"] == "ok":
            st.success(f"{f.name}: {rec['pages_with_text']}/{rec['total_pages']} pages, {rec['chunks']} chunks indexed.")
        elif rec["status"] == "duplicate":
            dest.unlink(missing_ok=True)
            st.warning(f"{f.name}: skipped. {rec['error']}")
        else:
            st.error(f"{f.name}: {rec['error']}")

st.subheader("Library")
registry = load_registry()
if registry:
    table = pd.DataFrame(registry.values())[["document", "status", "total_pages", "pages_with_text",
                                             "chunks", "organization", "publication_year", "processed_on", "source_url", "error"]]
    st.dataframe(table, width="stretch", hide_index=True)
    victim = st.selectbox("Remove a document", [""] + list(registry))
    if victim and st.button(f"Remove {victim}"):
        pipeline.remove_document(victim)
        (config.PDF_DIR / victim).unlink(missing_ok=True)
        st.rerun()
else:
    st.info("The library is empty.")

st.subheader("Keyword search")
term = st.text_input("Exact words to find in the indexed text")
if term.strip():
    results = pipeline.store.keyword_search(term.strip())
    st.caption(f"{len(results)} matching passages (max 20).")
    for r in results:
        with st.container(border=True):
            st.markdown(f"**{r['document']}** · page {r['page']}")
            st.write(r["text"])
