"""Home Dashboard - shows ONLY real, measured coverage of what is loaded."""
import streamlit as st

import config
import ui
from modules import groundwater_analytics as ga
from modules.rag_pipeline import load_registry

ui.setup_page("AI Groundwater Information Assistant",
              "Ask questions about India's groundwater and get answers grounded in government reports.")

df, problems = ui.datasets()
docs = {k: v for k, v in load_registry().items() if v.get("status") == "ok"}
pipeline = ui.get_pipeline()

c1, c2, c3, c4 = st.columns(4)
with c1:
    ui.metric_card("Reports indexed", str(len(docs)))
with c2:
    ui.metric_card("Searchable chunks", f"{pipeline.store.count():,}")
cov = ga.coverage_summary(df)
with c3:
    ui.metric_card("Monitoring stations", f"{cov.get('stations', 0):,}" if cov["rows"] else "no data")
with c4:
    ui.metric_card("Latest measurement", str(cov["latest_date"]) if cov["rows"] else "no data")

st.subheader("Data coverage and freshness")
if cov["rows"]:
    st.success(f"{cov['rows']:,} validated readings · {cov['states']} states/UTs · "
               f"{cov['districts']} districts · measurements from {cov['first_date']} to {cov['latest_date']}.")
    st.caption("Freshness is computed from the dates inside the loaded files, not assumed.")
else:
    st.warning("No groundwater measurement files are loaded yet. Open **Data Sources** to see "
               "how to add official CGWB / India-WRIS CSV files. Nothing is shown until real data exists.")
for p in problems:
    st.error(p)

st.subheader("Reports")
if docs:
    for rec in docs.values():
        st.markdown(f"<div class='src'>📄 <b>{rec['document']}</b> · {rec['total_pages']} pages · "
                    f"{rec['chunks']} chunks · processed {rec['processed_on'][:10]}</div>",
                    unsafe_allow_html=True)
else:
    st.info("No reports indexed yet. Add government PDFs in **Document Library**.")

st.subheader("AI engine status")
st.write(f"- Embeddings: `{ui.embedder_name()}`")
st.write("- Language model: " + ("configured ✅" if config.llm_configured() else
         "not configured - answers will show retrieved report passages (see README)"))
