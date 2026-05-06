"""
app_pages/global_view.py — Interactive global maps using Plotly.

Three separate choropleth figures (Supply / Demand / Stress), each with
hover tooltips, descriptive text, and an HTML download button.
Scenario and time-horizon selectors live here and persist via session_state.
"""
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data import load_data
from config import (
    SCENARIOS, YEARS, SCENARIO_TOOLTIPS, YEAR_TOOLTIPS,
    STRESS_COLORS, ARID_COLOR, NODATA_COLOR, CAP_SENTINEL,
)

# ── Selectors ─────────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)
with col_a:
    st.selectbox(
        "Scenario",
        options=list(SCENARIOS.keys()),
        format_func=lambda k: SCENARIOS[k],
        key="scenario",
        help="\n\n".join(
            f"**{SCENARIOS[k]}** — {SCENARIO_TOOLTIPS[k]}" for k in SCENARIOS
        ),
    )
with col_b:
    st.selectbox(
        "Time horizon",
        options=list(YEARS.keys()),
        format_func=lambda k: YEARS[k],
        key="year",
        help="\n\n".join(
            f"**{YEARS[k]}** — {YEAR_TOOLTIPS[k]}" for k in YEARS
        ),
    )

scenario = st.session_state.get("scenario", "bau")
year     = st.session_state.get("year", "50")

st.caption(f"Showing **{SCENARIOS[scenario]}** · **{YEARS[year]}**")

gdf = load_data()


# ── Helpers ───────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _global_geojson(_gdf):
    """Build GeoJSON with aggressive simplification for global view."""
    simplified = _gdf.copy()
    simplified["geometry"] = simplified.geometry.simplify(
        0.1, preserve_topology=True
    )
    return json.loads(simplified.to_json())


def _geo_style(fig):
    fig.update_geos(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#aaaaaa",
        showland=True,
        landcolor="#f5f5f5",
        showocean=True,
        oceancolor="#ddeeff",
        projection_type="natural earth",
    )
    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=480,
        paper_bgcolor="white",
    )
    return fig


def _download_button(fig, filename: str, label: str = "Download interactive map"):
    html_bytes = fig.to_html(
        full_html=True, include_plotlyjs="cdn"
    ).encode("utf-8")
    st.download_button(
        label=f":material/download: {label}",
        data=html_bytes,
        file_name=filename,
        mime="text/html",
    )


# ── Render functions (cached per scenario+year) ───────────────────────────────

@st.cache_data(show_spinner=False)
def _render_supply(_gdf, scenario, year):
    ba_col  = f"{scenario}{year}_ba_raw"
    geojson = _global_geojson(_gdf)

    df = _gdf[["pfaf_id", "name_0", ba_col]].copy()
    df["pfaf_id"] = df["pfaf_id"].astype(str)
    vals = pd.to_numeric(df[ba_col], errors="coerce")
    vals = vals.where(vals != CAP_SENTINEL)
    df["log_ba"]   = np.where(vals > 0, np.log10(vals), np.nan)
    df["val_display"] = vals.round(2).fillna("No data").astype(str)
    df["name_0"]   = df["name_0"].fillna("Unknown")

    fig = px.choropleth(
        df, geojson=geojson,
        locations="pfaf_id", featureidkey="properties.pfaf_id",
        color="log_ba",
        color_continuous_scale="YlOrBr_r",
        range_color=[-2, 2.5],
        custom_data=["name_0", "pfaf_id", "val_display"],
        title=f"Blue Water Availability (Supply) — {SCENARIOS[scenario]}, {YEARS[year]}",
    )
    fig.update_coloraxes(colorbar_title="log₁₀<br>[cm/yr]")
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Sub-basin: %{customdata[1]}<br>"
            "Supply: %{customdata[2]} cm/yr"
            "<extra></extra>"
        )
    )
    return _geo_style(fig)


@st.cache_data(show_spinner=False)
def _render_demand(_gdf, scenario, year):
    ww_col  = f"{scenario}{year}_ww_raw"
    geojson = _global_geojson(_gdf)

    df = _gdf[["pfaf_id", "name_0", ww_col]].copy()
    df["pfaf_id"] = df["pfaf_id"].astype(str)
    vals = pd.to_numeric(df[ww_col], errors="coerce")
    vals = vals.where(vals != CAP_SENTINEL)
    df["log_ww"]      = np.where(vals > 0, np.log10(vals), np.nan)
    df["val_display"] = vals.round(2).fillna("No data").astype(str)
    df["name_0"]      = df["name_0"].fillna("Unknown")

    fig = px.choropleth(
        df, geojson=geojson,
        locations="pfaf_id", featureidkey="properties.pfaf_id",
        color="log_ww",
        color_continuous_scale="YlOrRd",
        range_color=[-2, 2],
        custom_data=["name_0", "pfaf_id", "val_display"],
        title=f"Water Withdrawal (Demand) — {SCENARIOS[scenario]}, {YEARS[year]}",
    )
    fig.update_coloraxes(colorbar_title="log₁₀<br>[cm/yr]")
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Sub-basin: %{customdata[1]}<br>"
            "Demand: %{customdata[2]} cm/yr"
            "<extra></extra>"
        )
    )
    return _geo_style(fig)


@st.cache_data(show_spinner=False)
def _render_stress(_gdf, scenario, year):
    ws_col  = f"{scenario}{year}_ws_cat"
    ws_lbl  = f"{scenario}{year}_ws_label"
    geojson = _global_geojson(_gdf)

    cat_map = {
        -1: "Arid / low water use",
         0: "Low (<10%)",
         1: "Low-Medium (10–20%)",
         2: "Medium-High (20–40%)",
         3: "High (40–80%)",
         4: "Extremely High (>80%)",
    }
    color_map = {
        "Arid / low water use":  ARID_COLOR,
        "Low (<10%)":            STRESS_COLORS[0],
        "Low-Medium (10–20%)":   STRESS_COLORS[1],
        "Medium-High (20–40%)":  STRESS_COLORS[2],
        "High (40–80%)":         STRESS_COLORS[3],
        "Extremely High (>80%)": STRESS_COLORS[4],
        "No data":               NODATA_COLOR,
    }
    category_orders = {"stress_label": list(color_map.keys())}

    df = _gdf[["pfaf_id", "name_0", ws_col]].copy()
    df["pfaf_id"]     = df["pfaf_id"].astype(str)
    df["name_0"]      = df["name_0"].fillna("Unknown")
    df[ws_col]        = pd.to_numeric(df[ws_col], errors="coerce")
    df["stress_label"] = df[ws_col].map(cat_map).fillna("No data")

    fig = px.choropleth(
        df, geojson=geojson,
        locations="pfaf_id", featureidkey="properties.pfaf_id",
        color="stress_label",
        color_discrete_map=color_map,
        category_orders=category_orders,
        custom_data=["name_0", "pfaf_id", "stress_label"],
        title=f"Water Stress — {SCENARIOS[scenario]}, {YEARS[year]}",
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Sub-basin: %{customdata[1]}<br>"
            "Stress: %{customdata[2]}"
            "<extra></extra>"
        )
    )
    return _geo_style(fig)


# ── Panel A — Blue Water Availability ─────────────────────────────────────────

with st.spinner("Rendering supply map…"):
    fig_a = _render_supply(gdf, scenario, year)

st.plotly_chart(fig_a, use_container_width=True)
_download_button(fig_a, f"supply_{scenario}{year}.html")

st.markdown("""
**Blue Water Availability** is the total amount of renewable freshwater
(surface + interflow + groundwater recharge) flowing into each sub-basin per year,
after upstream consumption is removed. Higher values mean more water is naturally
available.
""")

st.divider()

# ── Panel B — Water Withdrawal ────────────────────────────────────────────────

with st.spinner("Rendering demand map…"):
    fig_b = _render_demand(gdf, scenario, year)

st.plotly_chart(fig_b, use_container_width=True)
_download_button(fig_b, f"demand_{scenario}{year}.html")

st.markdown("""
**Water Withdrawal** is the total annual gross water demand from all uses
(domestic, industrial, agricultural irrigation, and livestock) per sub-basin.
It represents the maximum potential water requirement, not necessarily the amount
actually consumed. Higher values mean more human demand for water.
""")

st.divider()

# ── Panel C — Water Stress ────────────────────────────────────────────────────

with st.spinner("Rendering stress map…"):
    fig_c = _render_stress(gdf, scenario, year)

st.plotly_chart(fig_c, use_container_width=True)
_download_button(fig_c, f"stress_{scenario}{year}.html")

st.markdown("""
**Water Stress** is the ratio of total water demand to available renewable supply.
It expresses how much of the available water is already being claimed by users —
values above 80% indicate intense competition for water. Sub-basins with very low
water use and very low supply are flagged separately as "Arid / low water use".
""")

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
