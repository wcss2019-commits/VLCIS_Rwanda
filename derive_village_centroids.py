import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# -----------------------------
# 1️⃣ Load village shapefile
# -----------------------------
shp_path = r"C:\VLCIS\Village.shp"

st.title("🌍 VLCIS Rwanda Villages Map")

try:
    gdf = gpd.read_file(shp_path)
except Exception as e:
    st.error(f"Error loading shapefile: {e}")
    st.stop()

# -----------------------------
# 2️⃣ Compute centroids
# -----------------------------
gdf['centroid'] = gdf.geometry.centroid
gdf['latitude'] = gdf.centroid.y
gdf['longitude'] = gdf.centroid.x

# -----------------------------
# 3️⃣ Build selection widgets
# -----------------------------
province_list = gdf['Province'].unique().tolist()
province = st.selectbox("Select Province", ["All"] + province_list)

if province != "All":
    gdf = gdf[gdf['Province'] == province]

district_list = gdf['District'].unique().tolist()
district = st.selectbox("Select District", ["All"] + district_list)

if district != "All":
    gdf = gdf[gdf['District'] == district]

sector_list = gdf['Sector'].unique().tolist()
sector = st.selectbox("Select Sector", ["All"] + sector_list)

if sector != "All":
    gdf = gdf[gdf['Sector'] == sector]

cell_list = gdf['Cell'].unique().tolist()
cell = st.selectbox("Select Cell", ["All"] + cell_list)

if cell != "All":
    gdf = gdf[gdf['Cell'] == cell]

# -----------------------------
# 4️⃣ Build Folium map
# -----------------------------
if gdf.empty:
    st.warning("No villages found for this selection.")
else:
    # Center map roughly on Rwanda
    m = folium.Map(location=[-1.94, 29.88], zoom_start=8, tiles=None)

    # Add Google Maps tiles
    folium.TileLayer(
        tiles='https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google',
        subdomains=['mt0', 'mt1', 'mt2', 'mt3'],
        name="Google Maps"
    ).add_to(m)

    # Add villages as markers
    for _, row in gdf.iterrows():
        popup_text = f"{row['Province']} → {row['District']} → {row['Sector']} → {row['Cell']} → {row['Name']}"
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=3,
            color='blue',
            fill=True,
            fill_opacity=0.7,
            popup=popup_text
        ).add_to(m)

    # Add layer control
    folium.LayerControl().add_to(m)

    # Display map in Streamlit
    st_folium(m, width=800, height=600)