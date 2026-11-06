"""Groundwater Analytics - charts built only from loaded, validated real records."""
import streamlit as st

import ui
from modules import data_ingestion
from modules import groundwater_analytics as ga

ui.setup_page("Groundwater Analytics",
              "Depth to water level in metres below ground level (m bgl). Larger = deeper water table.")

df, problems = ui.datasets()
for p in problems:
    st.error(p)
if df.empty:
    st.warning("No measurement data loaded. Add official CSV files under **Data Sources**. "
               "This page never displays placeholder numbers.")
    st.stop()

# ---- filters
with st.sidebar:
    st.header("Filters")
    files = sorted(df["dataset_file"].unique())
    chosen_files = st.multiselect("Dataset file", files, default=files)
    base = df[df["dataset_file"].isin(chosen_files)]
    states = st.multiselect("State / UT", sorted(base["state_name"].dropna().unique()))
    pool = base[base["state_name"].isin(states)] if states else base
    districts = st.multiselect("District", sorted(pool["district_name"].dropna().unique()))
    y0, y1 = int(base["date"].dt.year.min()), int(base["date"].dt.year.max())
    years = st.slider("Years", y0, y1, (y0, y1)) if y0 < y1 else (y0, y1)

view = ga.filter_data(base, states, districts, years)
if view.empty:
    st.info("No readings match these filters.")
    st.stop()

registry = data_ingestion.load_registry()
with st.expander("📌 Source and measurement period", expanded=True):
    for f in chosen_files:
        m = registry.get(f)
        if m:
            st.markdown(f"**{m['dataset_name']}** · {m['source_organization']} · period {m['measurement_period']} · "
                        f"units {m['measurement_units']} · [source]({m['source_url']})")
        else:
            st.markdown(f"**{f}** · metadata not registered (add it under Data Sources).")
    st.caption(f"Showing {len(view):,} readings from {view['date'].min().date()} to {view['date'].max().date()}.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["State-wise", "Trends", "Quarterly", "Compare years", "Stations map"])

with tab1:
    summary = ga.state_summary(view)
    st.plotly_chart(ga.chart_state_depth(summary), width="stretch")
    st.caption("Mean depth is a derived calculation over the filtered readings, not an official ranking.")
    st.dataframe(summary, width="stretch", hide_index=True)
    st.plotly_chart(ga.chart_distribution(view), width="stretch")

with tab2:
    by = "state_name" if len(view["state_name"].unique()) > 1 else None
    yearly = ga.yearly_trend(view, by)
    st.plotly_chart(ga.chart_yearly_trend(yearly, by), width="stretch")
    overall = ga.linear_trend(ga.yearly_trend(view))
    if overall:
        st.info(f"Derived straight-line trend over {overall['years']} years: "
                f"{overall['slope_m_per_year']:+.3f} m/year ({overall['direction']}). "
                "This is our own calculation on the selected data, not a prediction or official statistic.")
    else:
        st.caption("Fewer than 3 years of data selected, so no trend line is computed.")

with tab3:
    st.plotly_chart(ga.chart_quarterly(ga.quarterly_comparison(view)), width="stretch")

with tab4:
    avail = sorted(view["date"].dt.year.unique())
    if len(avail) < 2:
        st.info("Need at least two different years in the selection.")
    else:
        c1, c2, c3 = st.columns(3)
        a = c1.selectbox("Year A", avail, index=0)
        b = c2.selectbox("Year B", avail, index=len(avail) - 1)
        level = c3.radio("Level", ["state_name", "district_name"], horizontal=True)
        st.dataframe(ga.compare_years(view, a, b, level), width="stretch", hide_index=True)
        st.caption("change_m > 0 means the water table was deeper in Year B than Year A (only places with data in both years).")

with tab5:
    fig = ga.chart_map(view)
    if fig is None:
        st.info("This dataset has no latitude/longitude columns.")
    else:
        st.plotly_chart(fig, width="stretch")
