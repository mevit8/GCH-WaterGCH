"""
app_pages/global_view.py — Serves pre-rendered global map PNGs from assets/maps/.
No geopandas, no matplotlib, no waiting.
"""
from pathlib import Path
import streamlit as st
from config import SCENARIOS, YEARS

MAPS_DIR = Path("assets/maps")


def _map_path(scenario: str, year: str) -> Path:
    return MAPS_DIR / f"global_{scenario}{year}.png"


scenario = st.session_state.get("scenario", "bau")
year     = st.session_state.get("year", "50")

st.caption(
    f"Showing **{SCENARIOS[scenario]}** · **{YEARS[year]}**"
)

map_path = _map_path(scenario, year)

if not map_path.exists():
    st.error(
        f"Pre-rendered map not found: `{map_path}`. "
        "Run `python prerender_maps.py` locally and commit the `assets/` folder."
    )
else:
    st.image(str(map_path), use_container_width=True)

with st.expander(":material/info: How these values were estimated", expanded=False):
    st.markdown("""
Aqueduct 4.0 uses the **PCR-GLOBWB 2** global hydrological model to simulate water
supply and demand at ~10 km grid resolution, then aggregates outputs to HydroBASINS
Level-6 sub-basins (median area ~5,300 km², roughly the size of Delaware).

The **baseline period** (1979–2019) uses observed climate forcings; **future
projections** use bias-corrected climate forcings from five CMIP6 General Circulation
Models (GCMs), with values reported as the median across the five models. Long-term
trends are extracted using a 10-year moving average and Theil-Sen regression.

*Source: Kuzma et al. (2023), "Aqueduct 4.0", WRI Technical Note.*
""")