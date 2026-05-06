"""
streamlit_app.py — Main entry point for the WaterReqGCH dashboard.
"""
import streamlit as st
from utils.download_data import ensure_data

st.set_page_config(
    page_title="Water Risk Explorer",
    page_icon=":material/water_drop:",
    layout="wide",
)

ensure_data()

with st.sidebar:
    st.image("assets/final_logo.svg", width=160)
    st.divider()
    st.caption(
        "Data: WRI Aqueduct 4.0 · HydroBASINS Level-6 · "
        "~16,400 sub-basins worldwide"
    )

pages = [
    st.Page("app_pages/intro.py",        title="Introduction",      icon=":material/info:"),
    st.Page("app_pages/global_view.py",  title="Global model",      icon=":material/public:"),
    st.Page("app_pages/country_view.py", title="Country deep-dive", icon=":material/travel_explore:"),
    st.Page("app_pages/land_water.py",   title="Land & water",      icon=":material/forest:"),
]

page = st.navigation(pages, position="top")
st.title(f"{page.icon} {page.title}")
page.run()
