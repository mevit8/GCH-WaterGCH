"""
app_pages/country_view.py — Country deep-dive page.

Tab 1 (Annual):  Same three panels as global, filtered + zoomed to the country.
Tab 2 (Monthly): Small-multiples maps (per indicator) + aggregated line chart.

Scenario/year come from session_state (sidebar selectors in streamlit_app.py).
All renders are cached by (country, scenario, year) so re-selecting the same
combination is instant.
"""
import streamlit as st

from utils.data import load_data, get_countries, filter_country
from utils.plots import (
    render_country_annual_map,
    render_monthly_smallmultiples,
    render_country_lines,
)
from config import SCENARIOS, YEARS, INDICATORS


# ── Cached render helpers ──────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _cached_annual_map(_country_gdf, scenario, year, descriptor):
    return render_country_annual_map(_country_gdf, scenario, year, descriptor)


@st.cache_data(show_spinner=False)
def _cached_small_multiples(_country_gdf, stem, descriptor, what="score"):
    ind = next(i for i in INDICATORS if i["stem"] == stem)
    return render_monthly_smallmultiples(_country_gdf, ind, descriptor, what)


@st.cache_data(show_spinner=False)
def _cached_lines(_country_gdf, descriptor):
    return render_country_lines(_country_gdf, descriptor)


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
        "Same three panels as the global map, filtered and zoomed to this country. "
        "Change scenario or time horizon in the sidebar."
    )
    with st.spinner("Rendering country map…"):
        png = _cached_annual_map(country_gdf, scenario, year, descriptor)
    st.image(png, use_container_width=True)


# ── Tab 2: Monthly ─────────────────────────────────────────────────────────────
with tab_monthly:
    st.caption(
        "Monthly baseline indicators (1979–2019). "
        "Aqueduct does not publish monthly future projections — "
        "use the Annual view for future scenarios."
    )

    # ── Aggregated line chart (all 3 indicators, one figure) ──────────────────
    st.subheader("Seasonal aggregation", divider=False)
    st.caption(
        "Area-weighted mean and unweighted median across all sub-basins. "
        "Left axis = raw value · Right axis = Aqueduct score (0–5)."
    )
    with st.spinner("Computing monthly aggregates…"):
        lines_png = _cached_lines(country_gdf, descriptor)
    st.image(lines_png, use_container_width=True)

    # ── Small-multiples maps (per indicator, selectable) ─────────────────────
    st.subheader("Spatial distribution by month", divider=False)

    what = st.radio(
        "Value type",
        options=["score", "raw"],
        format_func=lambda x: "Aqueduct score (0–5, comparable across indicators)"
                               if x == "score" else "Raw value (native units)",
        horizontal=True,
        key="monthly_what",
    )

    ind_tabs = st.tabs([ind["title"] for ind in INDICATORS])
    for tab, ind in zip(ind_tabs, INDICATORS):
        with tab:
            with st.spinner(f"Rendering {ind['title']} maps…"):
                mm_png = _cached_small_multiples(country_gdf, ind["stem"], descriptor, what)
            if mm_png is None:
                st.warning(
                    f"Monthly columns for **{ind['title']}** not found in the dataset."
                )
            else:
                st.image(mm_png, use_container_width=True)

    # ── Methodology blurb ─────────────────────────────────────────────────────
    with st.expander(":material/info: How monthly values were estimated", expanded=False):
        st.markdown("""
Monthly values are derived by splitting the 1979–2019 PCR-GLOBWB 2 simulation into
12 monthly time series per sub-basin (all Januaries, all Februaries, etc.) and
computing the indicator independently for each.

For **water stress** and **depletion**, demand and supply are aggregated per calendar
month and the ratio computed. For **interannual variability**, the coefficient of
variation is computed across years for that specific calendar month.

Country-level values are an **area-weighted mean** across the country's sub-basins.

*Source: Kuzma et al. (2023), Aqueduct 4.0 Technical Note, Section "Indicators".*
""")
