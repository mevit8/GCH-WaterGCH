"""
utils/plots.py — Plotting functions adapted from:
  - example1_for_plots.py        (global 3-panel map)
  - 5_country_monthly_explorer.py (country monthly maps + line chart)

Key adaptations for Streamlit:
  1. Accept a pre-loaded GeoDataFrame instead of file paths.
  2. Return PNG bytes (via _fig_to_png) instead of saving to disk.
  3. Pure functions — no Streamlit calls inside.

All caching of the rendered PNG bytes is done in the page modules
using @st.cache_data with the underscore-prefixed GDF argument.
"""

import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch

from config import (
    STRESS_COLORS, ARID_COLOR, NODATA_COLOR, STRESS_LABELS,
    CAP_SENTINEL, MONTH_NAMES, INDICATORS,
)


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _fig_to_png(fig, dpi=150):
    """Render figure to PNG bytes and close it to free memory."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def clean_for_numeric(s: pd.Series, drop_cap: bool = True) -> pd.Series:
    """Coerce to numeric and optionally NaN-out the 9999 cap sentinel.
    Identical to clean_for_numeric() in 5_country_monthly_explorer.py.
    """
    s = pd.to_numeric(s, errors="coerce")
    if drop_cap:
        s = s.where(s != CAP_SENTINEL)
    return s


def country_aggregate(country_gdf, value_col: str, weight_col: str = "SUB_AREA"):
    """Area-weighted mean and unweighted median.
    Identical to country_aggregate() in 5_country_monthly_explorer.py.
    """
    v = clean_for_numeric(country_gdf[value_col])
    if weight_col in country_gdf.columns:
        w = pd.to_numeric(country_gdf[weight_col], errors="coerce")
    else:
        w = country_gdf.to_crs("ESRI:54034").area
    mask = v.notna() & w.notna() & (w > 0)
    if mask.sum() == 0:
        return np.nan, np.nan
    weighted_mean = (v[mask] * w[mask]).sum() / w[mask].sum()
    unweighted_median = v[mask].median()
    return float(weighted_mean), float(unweighted_median)


def _stress_legend_patches():
    patches = [Patch(facecolor=STRESS_COLORS[i], label=STRESS_LABELS[i]) for i in range(5)]
    patches += [
        Patch(facecolor=ARID_COLOR, label="Arid / low water use"),
        Patch(facecolor=NODATA_COLOR, label="No data"),
    ]
    return patches


# ── Global 3-panel map ─────────────────────────────────────────────────────────

def render_global_map(gdf, scenario: str, year: str) -> bytes:
    """Global Supply / Demand / Stress map.
    Adapted from plot_three_panel() in example1_for_plots.py.
    Returns PNG bytes.
    """
    pfx = f"{scenario}{year}"
    ba_col = f"{pfx}_ba_raw"
    ww_col = f"{pfx}_ww_raw"
    ws_cat = f"{pfx}_ws_cat"

    fig, axes = plt.subplots(3, 1, figsize=(16, 22))

    # A) Blue Water Availability (log10 cm/yr)
    ax = axes[0]
    log_ba = np.log10(gdf[ba_col].where(gdf[ba_col] > 0))
    gdf.assign(_v=log_ba).plot(
        column="_v", cmap="YlOrBr_r", vmin=-2, vmax=2.5, ax=ax,
        legend=True,
        legend_kwds={"label": "log₁₀(Blue Water Availability) [cm/yr]",
                     "orientation": "horizontal", "shrink": 0.6, "pad": 0.05},
        missing_kwds={"color": NODATA_COLOR},
    )
    ax.set_title(f"A) Blue Water Availability (Supply) – {scenario.upper()} 20{year}", fontsize=13)
    ax.set_xlim(-180, 180); ax.set_ylim(-60, 85)

    # B) Water Withdrawal (log10 cm/yr)
    ax = axes[1]
    log_ww = np.log10(gdf[ww_col].where(gdf[ww_col] > 0))
    gdf.assign(_v=log_ww).plot(
        column="_v", cmap="YlOrRd", vmin=-2, vmax=2, ax=ax,
        legend=True,
        legend_kwds={"label": "log₁₀(Water Withdrawal) [cm/yr]",
                     "orientation": "horizontal", "shrink": 0.6, "pad": 0.05},
        missing_kwds={"color": NODATA_COLOR},
    )
    ax.set_title(f"B) Water Withdrawal (Demand) – {scenario.upper()} 20{year}", fontsize=13)
    ax.set_xlim(-180, 180); ax.set_ylim(-60, 85)

    # C) Water Stress (discrete 5-class + arid mask)
    ax = axes[2]
    cat = gdf[ws_cat].copy()
    color_map = {
        -1: ARID_COLOR,
        0: STRESS_COLORS[0], 1: STRESS_COLORS[1],
        2: STRESS_COLORS[2], 3: STRESS_COLORS[3], 4: STRESS_COLORS[4],
    }
    facecolors = cat.map(color_map).fillna(NODATA_COLOR)
    gdf.plot(color=facecolors, ax=ax, linewidth=0)
    ax.set_title(f"C) Water Stress – {scenario.upper()} 20{year}", fontsize=13)
    ax.set_xlim(-180, 180); ax.set_ylim(-60, 85)
    ax.legend(handles=_stress_legend_patches(), loc="lower center",
              bbox_to_anchor=(0.5, -0.18), ncol=4, frameon=False,
              title="Water Stress Category")

    fig.suptitle(
        f"Global Water Risk Assessment – {scenario.upper()} 20{year} Scenario",
        fontsize=15, y=0.995, fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.985])
    return _fig_to_png(fig, dpi=150)


# ── Country annual 3-panel map ─────────────────────────────────────────────────

def render_country_annual_map(country_gdf, scenario: str, year: str,
                              descriptor: str) -> bytes:
    """Same three panels as global but zoomed to the country bounding box.
    Adapted from plot_three_panel() with country filtering added.
    Returns PNG bytes.
    """
    pfx = f"{scenario}{year}"
    ba_col = f"{pfx}_ba_raw"
    ww_col = f"{pfx}_ww_raw"
    ws_cat = f"{pfx}_ws_cat"

    bbox = country_gdf.total_bounds          # [minx, miny, maxx, maxy]
    pad_x = max(0.05 * (bbox[2] - bbox[0]), 0.5)
    pad_y = max(0.05 * (bbox[3] - bbox[1]), 0.5)
    xlim = (bbox[0] - pad_x, bbox[2] + pad_x)
    ylim = (bbox[1] - pad_y, bbox[3] + pad_y)

    fig, axes = plt.subplots(3, 1, figsize=(12, 18))

    # A) Blue Water Availability
    ax = axes[0]
    log_ba = np.log10(country_gdf[ba_col].where(country_gdf[ba_col] > 0))
    country_gdf.assign(_v=log_ba).plot(
        column="_v", cmap="YlOrBr_r", vmin=-2, vmax=2.5, ax=ax,
        legend=True,
        legend_kwds={"label": "log₁₀(Blue Water Availability) [cm/yr]",
                     "orientation": "horizontal", "shrink": 0.6, "pad": 0.05},
        missing_kwds={"color": NODATA_COLOR},
        linewidth=0.3, edgecolor="white",
    )
    ax.set_title(f"A) Blue Water Availability (Supply) – {scenario.upper()} 20{year}", fontsize=12)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)

    # B) Water Withdrawal
    ax = axes[1]
    log_ww = np.log10(country_gdf[ww_col].where(country_gdf[ww_col] > 0))
    country_gdf.assign(_v=log_ww).plot(
        column="_v", cmap="YlOrRd", vmin=-2, vmax=2, ax=ax,
        legend=True,
        legend_kwds={"label": "log₁₀(Water Withdrawal) [cm/yr]",
                     "orientation": "horizontal", "shrink": 0.6, "pad": 0.05},
        missing_kwds={"color": NODATA_COLOR},
        linewidth=0.3, edgecolor="white",
    )
    ax.set_title(f"B) Water Withdrawal (Demand) – {scenario.upper()} 20{year}", fontsize=12)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)

    # C) Water Stress
    ax = axes[2]
    cat = country_gdf[ws_cat].copy()
    color_map = {
        -1: ARID_COLOR,
        0: STRESS_COLORS[0], 1: STRESS_COLORS[1],
        2: STRESS_COLORS[2], 3: STRESS_COLORS[3], 4: STRESS_COLORS[4],
    }
    facecolors = cat.map(color_map).fillna(NODATA_COLOR)
    country_gdf.plot(color=facecolors, ax=ax, linewidth=0.3, edgecolor="white")
    ax.set_title(f"C) Water Stress – {scenario.upper()} 20{year}", fontsize=12)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.legend(handles=_stress_legend_patches(), loc="lower center",
              bbox_to_anchor=(0.5, -0.18), ncol=4, frameon=False,
              title="Water Stress Category")

    fig.suptitle(
        f"{descriptor} – Water Risk Assessment – {scenario.upper()} 20{year}",
        fontsize=14, y=0.995, fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.985])
    return _fig_to_png(fig, dpi=150)


# ── Country monthly: small-multiples map ──────────────────────────────────────

def render_monthly_smallmultiples(country_gdf, indicator: dict,
                                  descriptor: str, what: str = "score"):
    """12-panel small-multiples map (3×4 grid, Jan–Dec) for one indicator.
    Adapted from plot_monthly_smallmultiples() in 5_country_monthly_explorer.py.
    Returns PNG bytes, or None if columns are missing.
    """
    stem = indicator["stem"]
    cmap = indicator["raw_cmap"] if what == "raw" else indicator["score_cmap"]
    cols = [f"{stem}_{m:02d}_{what}" for m in range(1, 13)]

    missing = [c for c in cols if c not in country_gdf.columns]
    if missing:
        return None

    if what == "score":
        vmin, vmax = 0.0, 5.0
    else:
        all_vals = pd.concat([clean_for_numeric(country_gdf[c]) for c in cols])
        if all_vals.notna().sum() == 0:
            return None
        vmin = float(np.nanpercentile(all_vals, 2))
        vmax = float(np.nanpercentile(all_vals, 98))
        if vmin == vmax:
            vmax = vmin + 1e-6

    fig, axes = plt.subplots(3, 4, figsize=(16, 11))
    bbox = country_gdf.total_bounds
    pad_x = max(0.03 * (bbox[2] - bbox[0]), 0.3)
    pad_y = max(0.03 * (bbox[3] - bbox[1]), 0.3)

    for m, ax in enumerate(axes.flat, start=1):
        col = f"{stem}_{m:02d}_{what}"
        plot_gdf = country_gdf.copy()
        plot_gdf["_v"] = clean_for_numeric(plot_gdf[col], drop_cap=(what == "raw"))
        plot_gdf.plot(
            column="_v", cmap=cmap, vmin=vmin, vmax=vmax, ax=ax,
            linewidth=0.1, edgecolor="white",
            missing_kwds={"color": "#E0E0E0", "edgecolor": "white", "linewidth": 0.1},
        )
        ax.set_title(MONTH_NAMES[m - 1], fontsize=11)
        ax.set_xlim(bbox[0] - pad_x, bbox[2] + pad_x)
        ax.set_ylim(bbox[1] - pad_y, bbox[3] + pad_y)
        ax.set_xticks([]); ax.set_yticks([])

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=mcolors.Normalize(vmin=vmin, vmax=vmax))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes.ravel().tolist(),
                        orientation="horizontal", shrink=0.55, pad=0.04)
    label = (f"{indicator['title']} ({indicator['unit']})" if what == "raw"
             else f"{indicator['title']} – Aqueduct score (0–5)")
    cbar.set_label(label)

    fig.suptitle(
        f"{descriptor} – Monthly {indicator['title']} "
        f"({'raw' if what == 'raw' else '0–5 score'})",
        fontsize=14, fontweight="bold", y=0.995,
    )
    return _fig_to_png(fig, dpi=150)


# ── Country monthly: aggregated line chart ────────────────────────────────────

def render_country_lines(country_gdf, descriptor: str) -> bytes:
    """Three-subplot line chart with monthly area-weighted mean and median.
    Adapted from plot_country_lines() in 5_country_monthly_explorer.py.
    Returns PNG bytes.
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    months = list(range(1, 13))

    for ax, ind in zip(axes, INDICATORS):
        stem = ind["stem"]
        wm_raw, med_raw, wm_score, med_score = [], [], [], []

        for m in months:
            wmr, mdr = country_aggregate(country_gdf, f"{stem}_{m:02d}_raw")
            wms, mds = country_aggregate(country_gdf, f"{stem}_{m:02d}_score")
            wm_raw.append(wmr);   med_raw.append(mdr)
            wm_score.append(wms); med_score.append(mds)

        ax.plot(months, wm_raw, marker="o", linewidth=2, color="#1976D2",
                label="Area-weighted mean (raw)")
        ax.plot(months, med_raw, marker="s", linewidth=2, color="#388E3C",
                linestyle="--", label="Unweighted median (raw)")
        ax.set_xlabel("Month")
        ax.set_ylabel(f"Raw value\n({ind['unit']})", color="#333333")
        ax.set_xticks(months)
        ax.set_xticklabels(MONTH_NAMES, rotation=0, fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_title(ind["title"], fontsize=12)

        ax2 = ax.twinx()
        ax2.plot(months, wm_score, marker="o", linewidth=1.2, color="#D32F2F",
                 alpha=0.55, label="Area-weighted mean (score)")
        ax2.plot(months, med_score, marker="s", linewidth=1.2, color="#F57C00",
                 alpha=0.55, linestyle="--", label="Unweighted median (score)")
        ax2.set_ylabel("Aqueduct score (0–5)", color="#666666")
        ax2.set_ylim(-0.2, 5.2)

        if ax is axes[0]:
            h1, l1 = ax.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8, framealpha=0.85)

    fig.suptitle(
        f"{descriptor} – Country-aggregated monthly indicators (baseline 1979–2019)",
        fontsize=14, fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    return _fig_to_png(fig, dpi=150)
