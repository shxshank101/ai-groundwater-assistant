"""About Project page."""
import streamlit as st

import config
import ui

ui.setup_page("About Project", f"{config.PROJECT_NAME} · {config.PROJECT_ID}")

st.markdown(f"**Team:** {config.TEAM_NAME}")
for i, (name, reg) in enumerate(config.TEAM_MEMBERS, 1):   # Shashank Singh is first
    st.markdown(f"{i}. {name} - Registration No. {reg}")

st.markdown("""
### What it does
A RAG (Retrieval-Augmented Generation) assistant: it finds the right passages in government
groundwater reports and answers only from them, with report name and page number.

### How it works
1. **PDF -> text** with PyMuPDF, keeping page numbers
2. **Chunks** of about 1000 characters with 150 overlap (LangChain splitter)
3. **Embeddings** with Sentence Transformers (offline hashing fallback)
4. **ChromaDB** stores vectors on disk
5. **Retrieve** the top matches for a question, then an **LLM** writes an answer from them

### Data integrity
No measurement is generated or invented. Charts use only CSV files you load from official sources,
with metadata recorded. Derived values (means, trends) are labelled as derived.
""")
