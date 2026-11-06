"""Data Sources - official sources, registered datasets, CSV upload with metadata."""
import streamlit as st

import config
import ui
from modules import data_ingestion

ui.setup_page("Data Sources", "Every dataset is traceable to an official source. Nothing is synthetic.")

st.subheader("Official sources")
for s in config.OFFICIAL_SOURCES:
    st.markdown(f"- **[{s['name']}]({s['url']})** - {s['organization']}")
st.caption("Download groundwater-level CSVs / report PDFs from these sites (see docs/DATA_GUIDE.md), "
           "then upload them below or in the Document Library.")

st.subheader("Add a groundwater-level CSV")
with st.form("csv", clear_on_submit=True):
    f = st.file_uploader("CSV file (columns: date, state_name, district_name, station_name, currentlevel ...)", type=["csv"])
    a, b = st.columns(2)
    name = a.text_input("Dataset name")
    org = b.text_input("Source organization", placeholder="e.g. CGWB via India-WRIS")
    url = a.text_input("Original source URL")
    pub = b.text_input("Publication / last-updated date")
    units = a.text_input("Measurement units", value="m bgl (metres below ground level)")
    lim = b.text_input("Known limitations (optional)")
    go = st.form_submit_button("Validate and add")
if go:
    if f is None or not name.strip():
        st.error("Choose a file and enter a dataset name.")
    else:
        dest = config.RAW_DIR / f.name
        dest.write_bytes(f.getbuffer())
        try:
            rec = data_ingestion.auto_register(dest, {
                "dataset_name": name.strip(), "source_organization": org, "source_url": url,
                "publication_date": pub, "measurement_units": units, "limitations": lim or None})
            st.success(f"Added. Period: {rec['measurement_period']}. Coverage: {rec['geographic_coverage']}.")
            st.cache_data.clear()
        except ValueError as exc:
            dest.unlink(missing_ok=True)
            st.error(str(exc))

st.subheader("Registered datasets")
registry = data_ingestion.load_registry()
if not registry:
    st.info("No datasets registered yet.")
for rec in registry.values():
    with st.expander(rec["dataset_name"]):
        for k in data_ingestion.METADATA_FIELDS:
            st.write(f"**{k.replace('_', ' ').title()}:** {rec[k]}")
