"""
app_pages/global_view.py — Serves pre-rendered global map PNGs from assets/maps/.
Three separate panels (Supply / Demand / Stress), each with descriptive text
and a download button.
"""
from pathlib import Path
import streamlit as st
from config import SCENARIOS, YEARS, SCENARIO_TOOLTIPS, YEAR_TOOLTIPS

MAPS_DIR = Path("assets/maps")


def _map_path(scenario: str, year: str, panel: str) -> Path:
    return MAPS_DIR / f"global_{scenario}{year}_{panel}.png"


# ── Selectors ─────────────────────────────────────────────────────────────────
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


def _show_panel(panel: str, title: str, description: str):
    path = _map_path(scenario, year, panel)
    if not path.exists():
        st.error(
            f"Pre-rendered map not found: `{path}`. "
            "Run `python prerender_maps.py` locally and commit the `assets/` folder."
        )
        return
    img_bytes = path.read_bytes()
    st.image(img_bytes, use_container_width=True)
    st.download_button(
        label=f":material/download: Download {title} map",
        data=img_bytes,
        file_name=f"{panel}_{scenario}{year}.png",
        mime="image/png",
    )
    st.markdown(description)


# ── Panel A — Blue Water Availability ─────────────────────────────────────────
_show_panel(
    "supply",
    "Supply",
    """
**Blue Water Availability** is the total amount of renewable freshwater
(surface + interflow + groundwater recharge) flowing into each sub-basin per year,
after upstream consumption is removed. Higher values mean more water is naturally
available.
""",
)

st.divider()

# ── Panel B — Water Withdrawal ────────────────────────────────────────────────
_show_panel(
    "demand",
    "Demand",
    """
**Water Withdrawal** is the total annual gross water demand from all uses
(domestic, industrial, agricultural irrigation, and livestock) per sub-basin.
It represents the maximum potential water requirement, not necessarily the amount
actually consumed. Higher values mean more human demand for water.
""",
)

st.divider()

# ── Panel C — Water Stress ────────────────────────────────────────────────────
_show_panel(
    "stress",
    "Stress",
    """
**Water Stress** is the ratio of total water demand to available renewable supply.
It expresses how much of the available water is already being claimed by users —
values above 80% indicate intense competition for water. Sub-basins with very low
water use and very low supply are flagged separately as "Arid / low water use".
""",
)

# ── Methodology ───────────────────────────────────────────────────────────────
with st.expander(":material/info: How these values were estimated", expanded=False):
    st.markdown("""
Aqueduct 4.0 uses the **PCR-GLOBWB 2** global hydrological model to simulate water
supply and demand at ~10 km grid resolution, then aggregates outputs to HydroBASINS
Level-6 sub-basins (median area ~5,300 km², roughly the size of Delaware).

The **baseline period** (1979–2019) uses observed climate forcings; **future
projections** use bias-corrected climate forcings from five CMIP6 General Circulation
Models (GCMs), with values reported as the median across the five models. Long-term
trends are extracted using a 10-year moving average and Theil-Sen regression to
smooth out year-to-year noise.

For more details see references of the Introduction tab.
""")
