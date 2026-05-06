"""
app_pages/intro.py — Introduction and methodology overview.
"""
import streamlit as st

st.markdown("""
Welcome to the **WaterReqGCH**, a model of the Global Climate Hub to assess water
availability, water withdrawals, water stress and effects of land and diet policies
on water resources. The model covers the whole globe at a sub-basin scale.

All data comes from **WRI Aqueduct 4.0** (Kuzma et al. 2023). We are using two
pre-processed files:

1. Geographically enriched Aqueduct's numerical values (Sutanudjaja et al., 2018),
   keyed by `pfaf_id` according to HydroBASINS Level-6 sub-basin ID.
2. The polygon geometries from the HydroBASINS database
   (Lehner & Grill, 2013; Lehner, 2014).

We joined the two databases, one-to-one for each possible scenario, producing
roughly **16,400 sub-basins worldwide** to ensure global detailed coverage.
""")

with st.expander(":material/menu_book: References", expanded=False):
    st.markdown("""
- Kuzma, S., Bierkens, M. F. P., Lakshman, S., Luo, T., Saccoccia, L.,
  Sutanudjaja, E. H., & Van Beek, R. (2023). *Aqueduct 4.0: Updated
  decision-relevant global water risk indicators.* Technical Note.
  Washington, DC: World Resources Institute.
  https://doi.org/10.46830/writn.23.00061

- Lehner, B., & Grill, G. (2013). Global river hydrography and network routing:
  baseline data and new approaches to study the world's large river systems.
  *Hydrological Processes*, 27(15), 2171–2186.
  https://doi.org/10.1002/hyp.9740

- Lehner, B. (2014). *HydroBASINS: Global watershed boundaries and sub-basin
  delineations derived from HydroSHEDS data at 15 arc-second resolution.*
  World Wildlife Fund (WWF).

- Sutanudjaja, E. H., van Beek, R., Wanders, N., Wada, Y., Bosmans, J. H. C.,
  Drost, N., … & Bierkens, M. F. P. (2018). PCR-GLOBWB 2: a 5 arc-min global
  hydrological and water resources model. *Geoscientific Model Development*,
  11(6), 2429–2453.
""")
