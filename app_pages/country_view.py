"""
app_pages/country_view.py — Country deep-dive using Plotly for fast browser rendering.

Tab 1 (Annual):  Scenario/year selectors + three Plotly choropleth maps.
Tab 2 (Monthly): Small-multiples Plotly maps + aggregated line chart.
"""
import streamlit as st

from utils.data import load_data, get_countries, filter_country
from utils.plots_plotly import (
    render_country_annual_plotly,
    render_monthly_smallmultiples_plotly,
    render_country_lines_plotly,
)
from config import SCENARIOS, YEARS, SCENARIO_TOOLTIPS, YEAR_TOOLTIPS, INDICATORS


# ── Cached render wrappers ─────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def cached_annual(_gdf, country, scenario, year):
    sub, descriptor = filter_country(_gdf, name=country)
    return render_country_annual_plotly(sub, scenario, year, descriptor), descriptor

@st.cache_data(show_spinner=False)
def cached_lines(_gdf, country):
    sub, descriptor = filter_country(_gdf, name=country)
    return render_country_lines_plotly(sub, descriptor)

@st.cache_data(show_spinner=False)
def cached_smallmultiples(_gdf, country, ind_stem, what):
    sub, descriptor = filter_country(_gdf, name=country)
    ind = next(i for i in INDICATORS if i["stem"] == ind_stem)
    return render_monthly_smallmultiples_plotly(sub, ind, descriptor, what)


# ── Page body ──────────────────────────────────────────────────────────────────

gdf      = load_data()
countries = get_countries(gdf)

country = st.selectbox(
    "Select country",
    options=countries,
    index=countries.index("India") if "India" in countries else 0,
    key="selected_country",
)

tab_annual, tab_monthly = st.tabs([
    ":material/public: Annual view",
    ":material/calendar_month: Monthly patterns",
])


# ── Tab 1: Annual ──────────────────────────────────────────────────────────────
with tab_annual:

    # Selectors — only apply to this tab
    col_a, col_b = st.columns(2)
    with col_a:
        st.selectbox(
            "Scenario",
            options=list(SCENARIOS.keys()),
            format_func=lambda k: SCENARIOS[k],
            key="scenario",
        )
        st.caption(SCENARIO_TOOLTIPS[st.session_state.get("scenario", "bau")])
    with col_b:
        st.selectbox(
            "Time horizon",
            options=list(YEARS.keys()),
            format_func=lambda k: YEARS[k],
            key="year",
        )
        st.caption(YEAR_TOOLTIPS[st.session_state.get("year", "50")])

    scenario = st.session_state.get("scenario", "bau")
    year     = st.session_state.get("year", "50")

    st.caption(
        f"**{country}** · {SCENARIOS[scenario]} · {YEARS[year]}"
    )

    with st.spinner("Rendering maps…"):
        (fig_a, fig_b, fig_c), descriptor = cached_annual(gdf, country, scenario, year)

    st.plotly_chart(fig_a, use_container_width=True)
    st.plotly_chart(fig_b, use_container_width=True)
    st.plotly_chart(fig_c, use_container_width=True)


# ── Tab 2: Monthly ─────────────────────────────────────────────────────────────
with tab_monthly:
    st.caption("Monthly baseline indicators (1979–2019)")

    # ── Line chart ────────────────────────────────────────────────────────────
    st.subheader("Seasonal aggregation", divider=False)
    st.caption(
        "Area-weighted mean and unweighted median across all sub-basins. "
        "Solid lines = raw value · Dashed lines = Aqueduct score (0-5)."
    )
    with st.spinner("Computing monthly aggregates…"):
        fig_lines = cached_lines(gdf, country)
    st.plotly_chart(fig_lines, use_container_width=True)

    # ── Small-multiples maps ──────────────────────────────────────────────────
    st.subheader("Spatial distribution by month", divider=False)

    st.markdown("""
- **Baseline Water Stress (BWS):** Same as annual water stress (demand ÷ supply), but computed for each calendar month. Shows when in the year a basin is most water-stressed.
- **Baseline Water Depletion (BWD):** Ratio of water consumption (water that is evaporated or incorporated into products and not returned to the system) to available supply, per month. Higher values mean more permanent water loss to downstream users.
- **Interannual Variability (IAV):** Year-to-year variability in water availability for that calendar month, measured as the coefficient of variation across 1979–2019. High values mean a given month's water availability is unpredictable from one year to the next.
""")

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
                fig_mm = cached_smallmultiples(gdf, country, ind["stem"], what)
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
12 monthly time series per sub-basin (all Januaries, all Februaries, etc.) and computing
the indicator independently for each. For water stress and depletion, demand and supply
are aggregated per calendar month and the ratio computed. For interannual variability,
the coefficient of variation is computed across years for that specific calendar month.
Country-level values are an area-weighted mean across the country's sub-basins.
*For more details see references of the Introduction tab.*
""")
