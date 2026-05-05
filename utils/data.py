"""
utils/data.py — Data loading with Streamlit caching.

load_data() is cached with @st.cache_resource so the expensive
shapefile + CSV merge only happens once per server session.
Downloads data from Google Drive automatically if not present locally.
"""
import streamlit as st
import pandas as pd

from config import ENRICHED_CSV, HYDROBASINS_SHP
from utils.download_data import ensure_data


@st.cache_resource(show_spinner="Loading data (first run only)…")
def load_data():
    """Download if needed, then load and merge shapefile + CSV."""
    ensure_data()

    try:
        import geopandas as gpd
    except ImportError:
        raise SystemExit("geopandas is required. Install with: pip install geopandas")

    panel = pd.read_csv(ENRICHED_CSV, low_memory=False)
    panel["pfaf_id"] = pd.to_numeric(panel["pfaf_id"], errors="coerce").astype("Int64")

    basins = gpd.read_file(HYDROBASINS_SHP)
    basins["PFAF_ID"] = pd.to_numeric(basins["PFAF_ID"], errors="coerce").astype("Int64")

    overlap = (set(basins.columns) & set(panel.columns)) - {"PFAF_ID", "geometry"}
    if overlap:
        basins = basins.drop(columns=list(overlap))

    gdf = basins.merge(panel, left_on="PFAF_ID", right_on="pfaf_id", how="left")

    if "name_0" not in gdf.columns:
        raise RuntimeError(
            "After merge, 'name_0' is missing. "
            "Make sure ENRICHED_CSV is the enriched panel from build_aqueduct_pfaf_panel.py."
        )
    return gdf


@st.cache_data
def get_countries(_gdf):
    """Return sorted list of country name_0 values."""
    return sorted(_gdf["name_0"].dropna().unique().tolist())


def filter_country(gdf, name: str = None, gid: str = None):
    """Restrict to one country's sub-basins."""
    if gid:
        sub = gdf[gdf["gid_0"] == gid].copy()
        descriptor = gid
    elif name:
        sub = gdf[gdf["name_0"] == name].copy()
        descriptor = name
    else:
        raise ValueError("Provide either name or gid.")

    if len(sub) == 0:
        candidates = sorted(gdf["name_0"].dropna().unique())
        sample = ", ".join(c for c in candidates if descriptor.lower() in c.lower())
        raise ValueError(
            f"No pfafs match country '{descriptor}'. "
            f"Closest matches: {sample or '(none)'}"
        )
    return sub, descriptor