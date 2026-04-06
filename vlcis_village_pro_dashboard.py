import streamlit as st
from streamlit_autorefresh import st_autorefresh
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide")
st.title("🌍 VLCIS Rwanda AI Village Observer System")

# ---------------- AUTO REFRESH ----------------
st_autorefresh(interval=5*60*1000, key="refresh")

# ---------------- LOAD DATA ----------------
village_csv = r"C:\VLCIS\VLCIS_Rw\dashboard\data2\vlcis_village_centroids.csv"

try:
    df = pd.read_csv(village_csv)
except:
    st.error("❌ Village CSV not found. Check file path.")
    st.stop()

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.header("📍 Select Location")

province = st.sidebar.selectbox("Province", sorted(df['Province'].dropna().unique()))
df_prov = df[df['Province'] == province]

district = st.sidebar.selectbox("District", sorted(df_prov['District'].dropna().unique()))
df_dist = df_prov[df_prov['District'] == district]

sector = st.sidebar.selectbox("Sector", sorted(df_dist['Sector'].dropna().unique()))
df_sector = df_dist[df_dist['Sector'] == sector]

cell = st.sidebar.selectbox("Cell", sorted(df_sector['Cell'].dropna().unique()))
df_cell = df_sector[df_sector['Cell'] == cell]

village = st.sidebar.selectbox("Village", sorted(df_cell['Name'].dropna().unique()))
df_village = df_cell[df_cell['Name'] == village]

# ---------------- MAP ----------------
st.subheader("🛰 Live AI Village Observations")

m = folium.Map(location=[-1.94, 29.88], zoom_start=9, tiles=None)

# Google basemap
folium.TileLayer(
    tiles='https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attr='Google',
    subdomains=['mt0','mt1','mt2','mt3']
).add_to(m)

# ---------------- AI OBSERVERS ----------------
for _, row in df_cell.iterrows():   # show ALL villages in selected cell
    
    rainfall = np.random.choice(["Light", "Moderate", "Heavy"])
    lightning = np.random.choice(["None", "Detected"])
    aqi = np.random.choice(["Low","Moderate","High","Very High"])

    popup = f"""
    <b>Village:</b> {row['Name']}<br>
    <b>District:</b> {row['District']}<br>
    <b>Sector:</b> {row['Sector']}<br>
    <b>Cell:</b> {row['Cell']}<br><br>

    🌧 Rainfall: {rainfall}<br>
    ⚡ Lightning: {lightning}<br>
    🌫 AQI: {aqi}
    """

    color = "blue" if rainfall=="Light" else "orange" if rainfall=="Moderate" else "red"

    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=5,
        color=color,
        fill=True,
        fill_opacity=0.7,
        popup=popup
    ).add_to(m)

# Highlight selected village
for _, row in df_village.iterrows():
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=f"📍 SELECTED: {row['Name']}",
        icon=folium.Icon(color="green", icon="info-sign")
    ).add_to(m)

st_folium(m, width=1000, height=600)

# ---------------- IBF SECTION ----------------
st.subheader("📊 Impact-Based Forecast & Advisory (OPEN 2026)")

ibf_type = st.selectbox("Select Forecast Type", ["Rainfall", "AQI"])

if st.button("🔍 Generate Advisory"):

    if ibf_type == "Rainfall":
        forecast = np.random.choice(["Light rain", "Moderate rain", "Heavy rain"])

        if forecast == "Heavy rain":
            advisory = "🚨 High risk of flooding. Avoid travel."
        elif forecast == "Moderate rain":
            advisory = "⚠️ Be cautious. Possible disruptions."
        else:
            advisory = "✅ No significant impact."

    else:  # AQI
        forecast = np.random.choice(["Low", "Moderate", "High", "Very High"])

        if forecast in ["High", "Very High"]:
            advisory = "🚨 Limit outdoor activities."
        else:
            advisory = "✅ Air quality acceptable."

    st.success(f"""
    📍 Location:
    {village}, {cell}, {sector}, {district}

    🔮 Forecast:
    {forecast}

    🧠 Advisory:
    {advisory}
    """)

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("Weather & Climate Sustainable Solutions Ltd | VLCIS AI Observer Prototype (Fellowship 2026)")