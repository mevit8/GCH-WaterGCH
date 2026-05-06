"""
app_pages/land_water.py — Land-use change effects on water withdrawals.

Three interactive Plotly figures:
  1. Global total water withdrawals 2020–2050 (line chart)
  2. Percent change in withdrawals 2026→2050 by scenario (bar chart)
  3. 2050 withdrawals stacked by land class (stacked bar)
"""
import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

DATA_DIR = Path("land_water")

LAND_CLASSES = ["Crops", "TreeCrops", "Forest", "Grassland",
                "Urban", "Water", "Other"]

# cm/yr depth × km² area → km³ volume
CM_KM2_TO_KM3 = 1e-5

SCENARIO_LABELS = {
    "eat":       "EAT",
    "fat":       "FAT",
    "ndc":       "NDC",
    "afforest":  "Afforest",
    "bioen":     "Bioen",
    "landretir": "Landretir",
    "yieldint":  "Yieldint",
    "bau":       "BAU",
}

SCENARIO_COLORS = [
    "#1f77b4", "#d62728", "#2ca02c", "#ff7f0e",
    "#9467bd", "#8c564b", "#17becf", "#7f7f7f",
]

LAND_COLORS = {
    "Crops":     "#f4a261",
    "TreeCrops": "#8c564b",
    "Forest":    "#2ca02c",
    "Grassland": "#a6d96a",
    "Urban":     "#7f7f7f",
    "Water":     "#1f77b4",
    "Other":     "#c7c7c7",
}


def _short_label(stem: str) -> str:
    s = stem.lower()
    for key, label in SCENARIO_LABELS.items():
        if key in s:
            return label
    return stem.upper()


@st.cache_data(show_spinner=False)
def load_scenarios() -> dict:
    files = sorted(DATA_DIR.glob("*_withdrawals_2020_2050.csv"))
    if not files:
        return {}

    result = {}
    for f in files:
        name  = f.stem.replace("_withdrawals_2020_2050", "")
        label = _short_label(name)
        df    = pd.read_csv(f)
        df.columns = [c.strip() for c in df.columns]

        # Build per-land-class km³ columns: depth (cm/yr) × area (km²) × factor
        found_any = False
        for lc in LAND_CLASSES:
            raw_col  = f"Scaled_withdrawal_cm_per_yr_{lc}"
            area_col = f"Area_km2_{lc}"
            if raw_col in df.columns and area_col in df.columns:
                depth = pd.to_numeric(df[raw_col],  errors="coerce").fillna(0.0)
                area  = pd.to_numeric(df[area_col], errors="coerce").fillna(0.0)
                df[f"{lc}_km3"] = depth * area * CM_KM2_TO_KM3
                found_any = True
            else:
                df[f"{lc}_km3"] = 0.0

        if not found_any:
            continue

        # Total = sum of all land classes
        df["total_km3"] = df[[f"{lc}_km3" for lc in LAND_CLASSES]].sum(axis=1)

        agg = {"total_km3": ("total_km3", "sum")}
        for lc in LAND_CLASSES:
            agg[f"{lc}_km3"] = (f"{lc}_km3", "sum")

        ts = df.groupby("Year").agg(**agg).reset_index().sort_values("Year")
        result[label] = ts

    return result


def _download_html(fig, filename: str):
    buf = io.StringIO()
    fig.write_html(buf, full_html=True, include_plotlyjs="cdn")
    st.download_button(
        label=":material/download: Download interactive chart",
        data=buf.getvalue().encode(),
        file_name=filename,
        mime="text/html",
    )


def _chart_col():
    """Return a column that takes ~70% of page width."""
    col, _ = st.columns([3, 1])
    return col


# ── Intro ─────────────────────────────────────────────────────────────────────

st.markdown("""
Dietary choices and land-use policies strongly affect the area of land needed —
or allowed — for food, feed, fibre and forest. Because every type of land carries
a different water demand, those land-use shifts also reshape how much water humanity
withdraws each year. A hectare of irrigated cropland draws far more from rivers and
aquifers than a hectare of pasture, forest, or restored land; replacing one with
another therefore moves the global water needle, even when total land area stays
the same.

The figures below trace this connection through a set of contrasting **LandGHC
scenarios**. Each scenario describes a different plausible trajectory for global
land use between 2020 and 2050, driven by changes in diet, climate policy, energy
demand, agricultural productivity, or land-management ambition. We translate those
land-use trajectories into annual water withdrawals by combining HILDA+ land-cover
dynamics with country-calibrated water-use intensities derived from WRI Aqueduct 4.0,
FAO/AQUASTAT and peer-reviewed water-footprint datasets.
""")

with st.expander(":material/table: Scenario descriptions", expanded=False):
    st.markdown("""
| Code | Name | Description |
|------|------|-------------|
| BAU | Business As Usual | Baseline model projections to 2050 |
| FAT | High-meat diet | More area to pasture and feed crops |
| EAT | Lancet EAT diet | Increased vegetables/legumes, reduced pasture |
| NDC | National Determined Contributions | Forest gain targets, bioenergy crops |
| Afforest | Afforestation/Reforestation | Forest protection policies |
| Bioen | Bioenergy expansion | Biofuel mandates increase crop area |
| Yieldint | Yield intensification | Higher yields reduce land need |
| Landretir | Land retirement | Marginal cropland to forest |
""")

# ── Load ──────────────────────────────────────────────────────────────────────

with st.spinner("Loading scenario data…"):
    global_ts = load_scenarios()

if not global_ts:
    st.error(
        f"No CSV files found in `{DATA_DIR}/`. "
        "Make sure the `land_water/` folder is committed to the repository."
    )
    st.stop()

scenarios = list(global_ts.keys())
colors     = {s: SCENARIO_COLORS[i % len(SCENARIO_COLORS)]
              for i, s in enumerate(scenarios)}

# ── Figure 1: Time series ─────────────────────────────────────────────────────

st.subheader("Global total water withdrawals, 2020–2050")
st.markdown("""
The first figure tracks global annual water withdrawals from 2020 to 2050 under
each scenario. The trajectories diverge after the mid-2020s as land-use signals
accumulate: high-meat and bioenergy pathways push withdrawals up, while
plant-shifted diets and land retirement bend the curve down.
""")

fig1 = go.Figure()
for scen, ts in global_ts.items():
    fig1.add_trace(go.Scatter(
        x=ts["Year"], y=ts["total_km3"].round(1),
        mode="lines",
        name=scen,
        line=dict(color=colors[scen], width=2),
        hovertemplate=f"<b>{scen}</b><br>Year: %{{x}}<br>Withdrawal: %{{y:.1f}} km³/yr<extra></extra>",
    ))

fig1.update_layout(
    xaxis_title="Year",
    yaxis_title="Global water withdrawal (km³/yr)",
    legend=dict(orientation="h", y=-0.25),
    height=380,
    margin=dict(t=10, b=80),
    hovermode="x unified",
    plot_bgcolor="white",
    paper_bgcolor="white",
)
fig1.update_xaxes(showgrid=True, gridcolor="#eeeeee")
fig1.update_yaxes(showgrid=True, gridcolor="#eeeeee")

with _chart_col():
    st.plotly_chart(fig1, use_container_width=True)
    _download_html(fig1, "withdrawals_timeseries.html")

st.divider()

# ── Figure 2: Percent change ───────────────────────────────────────────────────

st.subheader("Change in global water withdrawals, 2026→2050")
st.markdown("""
The second figure summarises the percent change in global withdrawals between 2026
and 2050. The Lancet EAT diet delivers the largest reduction; high-meat (FAT) diets
and large-scale bioenergy expansion produce the largest increases. Yield
intensification and land retirement are roughly water-neutral overall — but for very
different reasons, since one frees land through productivity gains and the other
through deliberate withdrawal of marginal cropland.
""")

pct_rows = []
for scen, ts in global_ts.items():
    t26 = ts[ts["Year"] == 2026]
    t50 = ts[ts["Year"] == 2050]
    if t26.empty or t50.empty:
        continue
    v26 = t26.iloc[0]["total_km3"]
    v50 = t50.iloc[0]["total_km3"]
    pct = (v50 - v26) / v26 * 100 if v26 != 0 else np.nan
    pct_rows.append({"scenario": scen, "pct": pct})

pct_df = pd.DataFrame(pct_rows).sort_values("pct")

fig2 = go.Figure(go.Bar(
    x=pct_df["scenario"],
    y=pct_df["pct"].round(2),
    marker_color=[
        "#d62728" if v > 0 else "#2ca02c"
        for v in pct_df["pct"]
    ],
    hovertemplate="<b>%{x}</b><br>Change: %{y:.2f}%<extra></extra>",
))
fig2.add_hline(y=0, line_color="black", line_width=0.8)
fig2.update_layout(
    xaxis_title="Scenario",
    yaxis_title="Percent change (%)",
    height=340,
    margin=dict(t=10, b=60),
    plot_bgcolor="white",
    paper_bgcolor="white",
)
fig2.update_yaxes(showgrid=True, gridcolor="#eeeeee")

with _chart_col():
    st.plotly_chart(fig2, use_container_width=True)
    _download_html(fig2, "withdrawals_pct_change.html")

st.divider()

# ── Figure 3: Stacked bar 2050 ────────────────────────────────────────────────

st.subheader("Global water withdrawals by land class, 2050")
st.markdown("""
The third figure decomposes the 2050 withdrawal totals by land class so the
mechanism is visible. Cropland and urban water use dominate every scenario, but
their proportions change: under EAT, croplands account for roughly half of total
withdrawals rather than the ~60% share they hold in the high-meat scenario, with
the difference largely absorbed by reduced pasture-feed demand.
""")

rows_2050 = []
for scen, ts in global_ts.items():
    r = ts[ts["Year"] == 2050]
    if r.empty:
        continue
    r = r.iloc[0]
    row = {"scenario": scen}
    for lc in LAND_CLASSES:
        row[lc] = r.get(f"{lc}_km3", 0.0)
    rows_2050.append(row)

g2050 = pd.DataFrame(rows_2050).set_index("scenario").sort_index()

fig3 = go.Figure()
for lc in LAND_CLASSES:
    fig3.add_trace(go.Bar(
        name=lc,
        x=g2050.index,
        y=g2050[lc].round(1),
        marker_color=LAND_COLORS[lc],
        hovertemplate=f"<b>{lc}</b><br>%{{x}}: %{{y:.1f}} km³/yr<extra></extra>",
    ))

fig3.update_layout(
    barmode="stack",
    xaxis_title="Scenario",
    yaxis_title="Water withdrawals (km³/yr)",
    legend=dict(orientation="h", y=-0.25),
    height=380,
    margin=dict(t=10, b=100),
    plot_bgcolor="white",
    paper_bgcolor="white",
)
fig3.update_yaxes(showgrid=True, gridcolor="#eeeeee")

with _chart_col():
    st.plotly_chart(fig3, use_container_width=True)
    _download_html(fig3, "withdrawals_by_land_class_2050.html")
