"""
app_pages/global_view.py — Global three-panel map page.

Reads scenario/year from session_state (set by the sidebar in streamlit_app.py).
Renders the map once per scenario+year combination; subsequent selections of the
same combo are served from cache instantly.
"""
import streamlit as st

from utils.data import load_data
from utils.plots import render_global_map
from config import SCENARIOS, YEARS


@st.cache_data(show_spinner=False)
def _cached_global_map(_gdf, scenario: str, year: str) -> bytes:
    """Cache the rendered PNG bytes keyed on scenario + year (9 combinations)."""
    return render_global_map(_gdf, scenario, year)


# ── Page body ──────────────────────────────────────────────────────────────────

gdf = load_data()

scenario = st.session_state.get("scenario", "bau")
year     = st.session_state.get("year", "50")

st.caption(
    f"Showing **{SCENARIOS[scenario]}** · **{YEARS[year]}** · "
    f"{len(gdf):,} sub-basins worldwide"
)

with st.spinner("Rendering global map…"):
    png = _cached_global_map(gdf, scenario, year)

st.image(png, use_container_width=True)

# ── Methodology blurb (from instructions) ─────────────────────────────────────
with st.expander(":material/info: How these values were estimated", expanded=False):
    st.markdown("""
Aqueduct 4.0 uses the **PCR-GLOBWB 2** global hydrological model to simulate water
supply and demand at ~10 km grid resolution, then aggregates outputs to HydroBASINS
Level-6 sub-basins (median area ~5,300 km², roughly the size of Delaware).

The **baseline period** (1979–2019) uses observed climate forcings; **future
projections** use bias-corrected climate forcings from five CMIP6 General Circulation
Models (GCMs), with values reported as the median across the five models. Long-term
trends are extracted using a 10-year moving average and Theil-Sen regression to smooth
out year-to-year noise.

*Source: Kuzma et al. (2023), "Aqueduct 4.0", WRI Technical Note.*
""")
