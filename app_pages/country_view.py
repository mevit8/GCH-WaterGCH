"""
app_pages/country_view.py — Country deep-dive using Plotly for fast browser rendering.

Tab 1 (Annual):  Three Plotly choropleth maps filtered + zoomed to the country.
Tab 2 (Monthly): Small-multiples Plotly maps + aggregated line chart.

Data is loaded/cached once; rendering happens in the browser — no server-side
image generation per request.
"""
import streamlit as st

from utils.data import load_data, get_countries, filter_country
from utils.plots_plotly import (
    render_country_annual_plotly,
    render_monthly_smallmultiples_plotly,
    render_country_lines_plotly,
)
from config import SCENARIOS, YEARS, INDICATORS


# ── Page body ──────────────────────────────────────────────────────────────────

gdf       = load_data()
countries = get_countries(gdf)

scenario = st.session_state.get("scenario", "bau")
year     = st.session_state.get("year", "50")

country = st.selectbox(
    "Select country",
    options=countries,
    index=countries.index("India") if "India" in countries else 0,
    key="selected_country",
)

try:
    country_gdf, descriptor = filter_country(gdf, name=country)
except ValueError as e:
    st.error(str(e))
    st.stop()

st.caption(
    f"**{descriptor}** · {len(country_gdf):,} sub-basins · "
    f"{SCENARIOS[scenario]} · {YEARS[year]}"
)

tab_annual, tab_monthly = st.tabs([
    ":material/public: Annual view",
    ":material/calendar_month: Monthly patterns",
])


# ── Tab 1: Annual ──────────────────────────────────────────────────────────────
with tab_annual:
    st.caption(
        "Supply, demand, and stress maps filtered to this country. "
        "Change scenario or time horizon in the sidebar."
    )

    with st.spinner("Rendering maps…"):
        fig_a, fig_b, fig_c = render_country_annual_plotly(
            country_gdf, scenario, year, descriptor
        )

    st.plotly_chart(fig_a, use_container_width=True)
    st.plotly_chart(fig_b, use_container_width=True)
    st.plotly_chart(fig_c, use_container_width=True)


# ── Tab 2: Monthly ─────────────────────────────────────────────────────────────
with tab_monthly:
    st.caption(
        "Monthly baseline indicators (1979–2019). "
        "Aqueduct does not publish monthly future projections — "
        "use the Annual view for future scenarios."
    )

    # ── Line chart ────────────────────────────────────────────────────────────
    st.subheader("Seasonal aggregation", divider=False)
    st.caption(
        "Area-weighted mean and unweighted median across all sub-basins. "
        "Solid lines = raw value · Dashed lines = Aqueduct score (0-5)."
    )
    with st.spinner("Computing monthly aggregates…"):
        fig_lines = render_country_lines_plotly(country_gdf, descriptor)
    st.plotly_chart(fig_lines, use_container_width=True)

    # ── Small-multiples maps ──────────────────────────────────────────────────
    st.subheader("Spatial distribution by month", divider=False)

    what = st.radio(
        "Value type",
        options=["score", "raw"],
        format_func=lambda x: "Aqueduct score (0-5)" if x == "score" else "Raw value",
        horizontal=True,
        key="monthly_what",
    )

    ind_tabs = st.tabs([ind["title"] for ind in INDICATORS])
    for tab, ind in zip(ind_tabs, INDICATORS):
        with tab:
            with st.spinner(f"Rendering {ind['title']} maps…"):
                fig_mm = render_monthly_smallmultiples_plotly(
                    country_gdf, ind, descriptor, what
                )
            if fig_mm is None:
                st.warning(
                    f"Monthly columns for **{ind['title']}** not found in the dataset."
                )
            else:
                st.plotly_chart(fig_mm, use_container_width=True)

    # ── Methodology ───────────────────────────────────────────────────────────
    with st.expander(":material/info: How monthly values were estimated", expanded=False):
        st.markdown("""
Monthly values are derived by splitting the 1979–2019 PCR-GLOBWB 2 simulation into
12 monthly time series per sub-basin and computing the indicator independently for each.

For **water stress** and **depletion**, demand and supply are aggregated per calendar
month and the ratio computed. For **interannual variability**, the coefficient of
variation is computed across years for that specific calendar month.

Country-level values are an **area-weighted mean** across the country's sub-basins.

*Source: Kuzma et al. (2023), Aqueduct 4.0 Technical Note, Section "Indicators".*
""")
