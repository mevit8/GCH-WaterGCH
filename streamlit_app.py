"""
streamlit_app.py — Main entry point for the WaterReqGCH dashboard.

Handles:
  - Page config and app-level layout
  - Shared sidebar selectors (scenario + time horizon)
    written to session_state so both pages read the same values
  - Navigation between Global map and Country deep-dive
"""
import streamlit as st
from config import SCENARIOS, YEARS, SCENARIO_TOOLTIPS, YEAR_TOOLTIPS

st.set_page_config(
    page_title="Water Risk Explorer",
    page_icon=":material/water_drop:",
    layout="wide",
)

# ── Shared sidebar selectors ──────────────────────────────────────────────────
# These write directly to session_state via their `key=` parameter.
# Both page modules read st.session_state["scenario"] and ["year"].

with st.sidebar:
    st.markdown("### :material/tune: Scenario settings")

    st.selectbox(
        "Time horizon",
        options=list(YEARS.keys()),
        format_func=lambda k: YEARS[k],
        key="year",
        help="\n\n".join(f"**{YEARS[k]}** — {YEAR_TOOLTIPS[k]}" for k in YEARS),
    )

    st.selectbox(
        "Scenario",
        options=list(SCENARIOS.keys()),
        format_func=lambda k: SCENARIOS[k],
        key="scenario",
        help="\n\n".join(f"**{SCENARIOS[k]}** — {SCENARIO_TOOLTIPS[k]}" for k in SCENARIOS),
    )

    st.divider()
    st.caption(
        "Data: WRI Aqueduct 4.0 · HydroBASINS Level-6 · "
        "~16,400 sub-basins worldwide"
    )

# ── Navigation ────────────────────────────────────────────────────────────────
pages = [
    st.Page("app_pages/global_view.py",  title="Global map",       icon=":material/public:"),
    st.Page("app_pages/country_view.py", title="Country deep-dive", icon=":material/travel_explore:"),
]

page = st.navigation(pages, position="top")
st.title(f"{page.icon} {page.title}")
page.run()
