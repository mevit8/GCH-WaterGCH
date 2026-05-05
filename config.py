"""
config.py — Edit the two PATH lines to match your setup.
Everything else is derived from the original scripts.
"""
import os
from pathlib import Path

# Use /data (Railway volume) in production, local data/ folder otherwise
_DATA_DIR = Path("/data") if os.environ.get("RAILWAY_ENVIRONMENT") else Path("data")

ENRICHED_CSV    = _DATA_DIR / "aqueduct_pfaf_panel_enriched.csv"
HYDROBASINS_SHP = _DATA_DIR / "pfaf_lev06_merged.shp"

# ── Stress colour palette (matches WRI Aqueduct) ─────────────────────────────
STRESS_COLORS = ["#2E7D32", "#9CCC65", "#FFEB3B", "#FB8C00", "#C62828"]
ARID_COLOR    = "#BDBDBD"
NODATA_COLOR  = "#F5F5F5"
STRESS_LABELS = [
    "Low (<10%)", "Low-Medium (10–20%)", "Medium-High (20–40%)",
    "High (40–80%)", "Extremely High (>80%)",
]

# ── Sentinel ─────────────────────────────────────────────────────────────────
CAP_SENTINEL = 9999

# ── Scenario / year options ───────────────────────────────────────────────────
SCENARIOS = {
    "bau": "Business-as-usual (SSP3-7.0)",
    "opt": "Optimistic (SSP1-2.6)",
    "pes": "Pessimistic (SSP5-8.5)",
}
SCENARIO_TOOLTIPS = {
    "bau": "SSP3-7.0: regional rivalry, slow growth, high population. +2.8–4.6 °C by 2100. Default.",
    "opt": "SSP1-2.6: sustainability pathway, strong governance, rapid emissions cuts. +1.3–2.4 °C by 2100.",
    "pes": "SSP5-8.5: fossil-fuelled growth, carbon-intensive energy. +3.3–5.7 °C by 2100.",
}
YEARS = {
    "30": "Short-term (2030)",
    "50": "Mid-term (2050)",
    "80": "Long-term (2080)",
}
YEAR_TOOLTIPS = {
    "30": "Centered on 2030 (window 2015–2045). Near-term conditions already in motion.",
    "50": "Centered on 2050 (window 2035–2065). Typical horizon for major infrastructure planning.",
    "80": "Centered on 2080 (window 2065–2095). End-of-century long-run trajectory.",
}

# ── Monthly indicators (from 5_country_monthly_explorer.py) ──────────────────
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

INDICATORS = [
    dict(stem="baseline_bws", title="Baseline Water Stress",
         unit="ratio (demand/supply)",
         raw_cmap="YlOrRd", score_cmap="RdYlGn_r"),
    dict(stem="baseline_bwd", title="Baseline Water Depletion",
         unit="ratio (consumption/supply)",
         raw_cmap="YlOrRd", score_cmap="RdYlGn_r"),
    dict(stem="baseline_iav", title="Interannual Variability",
         unit="CV of available water",
         raw_cmap="viridis", score_cmap="RdYlGn_r"),
]
