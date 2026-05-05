"""
utils/plots_plotly.py — Plotly-based country plot functions.

Replaces the matplotlib country functions from utils/plots.py.
Renders in the browser — Railway only sends data, not images.
No file saving, returns plotly Figure objects directly.
"""

import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import (
    STRESS_COLORS, ARID_COLOR, NODATA_COLOR, STRESS_LABELS,
    CAP_SENTINEL, MONTH_NAMES, INDICATORS,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_geojson(gdf):
    """Convert GDF to GeoJSON dict for Plotly, with light simplification."""
    simplified = gdf.copy()
    simplified["geometry"] = simplified.geometry.simplify(0.05)
    return json.loads(simplified.to_json())


def _clean(s: pd.Series, drop_cap: bool = True) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    if drop_cap:
        s = s.where(s != CAP_SENTINEL)
    return s


def _geo_layout(fig, country_gdf):
    """Fit map view to country bounds."""
    bounds = country_gdf.total_bounds  # [minx, miny, maxx, maxy]
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        showframe=False,
        bgcolor="white",
    )
    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return fig


# ── Country annual map ────────────────────────────────────────────────────────

def render_country_annual_plotly(country_gdf, scenario: str, year: str,
                                 descriptor: str):
    """Three-panel annual map (Supply / Demand / Stress) as Plotly figures.
    Returns a list of three go.Figure objects.
    """
    pfx    = f"{scenario}{year}"
    ba_col = f"{pfx}_ba_raw"
    ww_col = f"{pfx}_ww_raw"
    ws_col = f"{pfx}_ws_cat"

    geojson = _to_geojson(country_gdf)
    ids     = country_gdf["pfaf_id"].astype(str).tolist()

    figures = []

    # ── A) Blue Water Availability (log10) ────────────────────────────────────
    df = country_gdf[["pfaf_id", ba_col]].copy()
    df["pfaf_id"] = df["pfaf_id"].astype(str)
    vals = _clean(df[ba_col])
    df["log_ba"] = np.where(vals > 0, np.log10(vals), np.nan)

    fig_a = px.choropleth(
        df, geojson=geojson,
        locations="pfaf_id", featureidkey="properties.pfaf_id",
        color="log_ba",
        color_continuous_scale="YlOrBr_r",
        range_color=[-2, 2.5],
        labels={"log_ba": "log₁₀ [cm/yr]"},
        title=f"A) Blue Water Availability (Supply) – {scenario.upper()} 20{year}",
    )
    _geo_layout(fig_a, country_gdf)
    figures.append(fig_a)

    # ── B) Water Withdrawal (log10) ───────────────────────────────────────────
    df2 = country_gdf[["pfaf_id", ww_col]].copy()
    df2["pfaf_id"] = df2["pfaf_id"].astype(str)
    vals2 = _clean(df2[ww_col])
    df2["log_ww"] = np.where(vals2 > 0, np.log10(vals2), np.nan)

    fig_b = px.choropleth(
        df2, geojson=geojson,
        locations="pfaf_id", featureidkey="properties.pfaf_id",
        color="log_ww",
        color_continuous_scale="YlOrRd",
        range_color=[-2, 2],
        labels={"log_ww": "log₁₀ [cm/yr]"},
        title=f"B) Water Withdrawal (Demand) – {scenario.upper()} 20{year}",
    )
    _geo_layout(fig_b, country_gdf)
    figures.append(fig_b)

    # ── C) Water Stress (categorical) ─────────────────────────────────────────
    df3 = country_gdf[["pfaf_id", ws_col]].copy()
    df3["pfaf_id"] = df3["pfaf_id"].astype(str)
    df3[ws_col] = pd.to_numeric(df3[ws_col], errors="coerce")

    cat_map = {
        -1: "Arid / low water use",
        0:  "Low (<10%)",
        1:  "Low-Medium (10–20%)",
        2:  "Medium-High (20–40%)",
        3:  "High (40–80%)",
        4:  "Extremely High (>80%)",
    }
    color_map = {
        "Arid / low water use":   ARID_COLOR,
        "Low (<10%)":             STRESS_COLORS[0],
        "Low-Medium (10–20%)":    STRESS_COLORS[1],
        "Medium-High (20–40%)":   STRESS_COLORS[2],
        "High (40–80%)":          STRESS_COLORS[3],
        "Extremely High (>80%)":  STRESS_COLORS[4],
        "No data":                NODATA_COLOR,
    }
    category_orders = {
        "stress_label": [
            "Low (<10%)", "Low-Medium (10–20%)", "Medium-High (20–40%)",
            "High (40–80%)", "Extremely High (>80%)",
            "Arid / low water use", "No data",
        ]
    }
    df3["stress_label"] = df3[ws_col].map(cat_map).fillna("No data")

    fig_c = px.choropleth(
        df3, geojson=geojson,
        locations="pfaf_id", featureidkey="properties.pfaf_id",
        color="stress_label",
        color_discrete_map=color_map,
        category_orders=category_orders,
        title=f"C) Water Stress – {scenario.upper()} 20{year}",
    )
    _geo_layout(fig_c, country_gdf)
    figures.append(fig_c)

    return figures


# ── Monthly small-multiples (12 maps per indicator) ───────────────────────────

def render_monthly_smallmultiples_plotly(country_gdf, indicator: dict,
                                         descriptor: str, what: str = "score"):
    """12-panel Plotly figure (3 rows × 4 cols) for one indicator.
    Returns a go.Figure or None if columns are missing.
    """
    stem = indicator["stem"]
    cols = [f"{stem}_{m:02d}_{what}" for m in range(1, 13)]
    missing = [c for c in cols if c not in country_gdf.columns]
    if missing:
        return None

    geojson = _to_geojson(country_gdf)
    id_col  = country_gdf["pfaf_id"].astype(str)

    if what == "score":
        vmin, vmax = 0.0, 5.0
        cmap = indicator["score_cmap"]
    else:
        all_vals = pd.concat([_clean(country_gdf[c]) for c in cols])
        if all_vals.notna().sum() == 0:
            return None
        vmin = float(np.nanpercentile(all_vals, 2))
        vmax = float(np.nanpercentile(all_vals, 98))
        if vmin == vmax:
            vmax = vmin + 1e-6
        cmap = indicator["raw_cmap"]

    # Build 3×4 subplot grid
    fig = make_subplots(
        rows=3, cols=4,
        subplot_titles=MONTH_NAMES,
        specs=[[{"type": "choropleth"}] * 4] * 3,
        horizontal_spacing=0.02,
        vertical_spacing=0.05,
    )

    for m in range(1, 13):
        row = (m - 1) // 4 + 1
        col = (m - 1) % 4 + 1
        data_col = f"{stem}_{m:02d}_{what}"

        df = pd.DataFrame({
            "pfaf_id": id_col,
            "val": _clean(country_gdf[data_col], drop_cap=(what == "raw")),
        })

        trace = go.Choropleth(
            geojson=geojson,
            locations=df["pfah_id"] if "pfah_id" in df else df["pfaf_id"],
            z=df["val"],
            featureidkey="properties.pfaf_id",
            colorscale=cmap,
            zmin=vmin, zmax=vmax,
            showscale=(m == 1),
            colorbar=dict(len=0.3, y=0.5, x=1.02,
                          title=dict(text="Score (0–5)" if what == "score"
                                     else indicator["unit"], side="right")),
            marker_line_width=0.1,
        )
        fig.add_trace(trace, row=row, col=col)

        fig.update_geos(
            fitbounds="locations", visible=False,
            row=row, col=col,
        )

    fig.update_layout(
        title=dict(
            text=f"{descriptor} – Monthly {indicator['title']} "
                 f"({'score 0–5' if what == 'score' else 'raw'})",
            font=dict(size=14),
        ),
        height=700,
        margin={"r": 80, "t": 60, "l": 0, "b": 0},
        paper_bgcolor="white",
    )
    return fig


# ── Monthly aggregated line chart ─────────────────────────────────────────────

def render_country_lines_plotly(country_gdf, descriptor: str):
    """Three-subplot line chart with area-weighted mean across months.
    Returns a go.Figure.
    """
    from utils.plots import country_aggregate

    months = list(range(1, 13))

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=[ind["title"] for ind in INDICATORS],
        horizontal_spacing=0.08,
    )

    colors = {
        "wm_raw":    "#1976D2",
        "med_raw":   "#388E3C",
        "wm_score":  "#D32F2F",
        "med_score": "#F57C00",
    }

    for col_idx, ind in enumerate(INDICATORS, start=1):
        stem = ind["stem"]
        wm_raw, med_raw, wm_score, med_score = [], [], [], []

        for m in months:
            wmr, mdr = country_aggregate(country_gdf, f"{stem}_{m:02d}_raw")
            wms, mds = country_aggregate(country_gdf, f"{stem}_{m:02d}_score")
            wm_raw.append(wmr);   med_raw.append(mdr)
            wm_score.append(wms); med_score.append(mds)

        show_legend = (col_idx == 1)

        fig.add_trace(go.Scatter(
            x=MONTH_NAMES, y=wm_raw, mode="lines+markers",
            name="Area-weighted mean (raw)", line=dict(color=colors["wm_raw"], width=2),
            legendgroup="wm_raw", showlegend=show_legend,
        ), row=1, col=col_idx)

        fig.add_trace(go.Scatter(
            x=MONTH_NAMES, y=med_raw, mode="lines+markers",
            name="Unweighted median (raw)",
            line=dict(color=colors["med_raw"], width=2, dash="dash"),
            legendgroup="med_raw", showlegend=show_legend,
        ), row=1, col=col_idx)

        # Score on secondary y axis
        fig.add_trace(go.Scatter(
            x=MONTH_NAMES, y=wm_score, mode="lines+markers",
            name="Area-weighted mean (score)",
            line=dict(color=colors["wm_score"], width=1.5),
            opacity=0.6, legendgroup="wm_score", showlegend=show_legend,
            yaxis=f"y{col_idx + 3}" if col_idx > 1 else "y4",
        ), row=1, col=col_idx)

        fig.add_trace(go.Scatter(
            x=MONTH_NAMES, y=med_score, mode="lines+markers",
            name="Unweighted median (score)",
            line=dict(color=colors["med_score"], width=1.5, dash="dash"),
            opacity=0.6, legendgroup="med_score", showlegend=show_legend,
            yaxis=f"y{col_idx + 3}" if col_idx > 1 else "y4",
        ), row=1, col=col_idx)

        fig.update_yaxes(title_text=f"Raw ({ind['unit']})", row=1, col=col_idx)

    fig.update_layout(
        title=dict(
            text=f"{descriptor} – Monthly indicators (baseline 1979–2019)",
            font=dict(size=14),
        ),
        height=420,
        legend=dict(orientation="h", y=-0.2),
        margin={"r": 20, "t": 60, "l": 60, "b": 80},
        paper_bgcolor="white",
    )
    return fig
