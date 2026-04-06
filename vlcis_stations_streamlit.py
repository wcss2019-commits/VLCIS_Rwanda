import streamlit as st
from streamlit_autorefresh import st_autorefresh
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np

st.title("🌍 VLCIS Rwanda AI Village Observers")

# Auto-refresh every 5 minutes (5*60*1000 ms)
st_autorefresh(interval=5*60*1000)

# Load village centroids
village_csv = r"C:\VLCIS\VLCIS_Rw\dashboard\data2\vlcis_village_centroids.csv"
df_villages = pd.read_csv(village_csv)

# Create map
m = folium.Map(location=[-1.94,29.88], zoom_start=8, tiles=None)
folium.TileLayer(
    tiles='https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attr='Google', subdomains=['mt0','mt1','mt2','mt3']
).add_to(m)

# Add AI Observer markers (example random data)
for _, row in df_villages.iterrows():
    rainfall = np.random.choice(["Light", "Moderate", "Heavy"])
    lightning = np.random.choice(["None", "Detected"])
    aqi = np.random.choice(["Low","Moderate","High","Very High"])
    
    popup_text = f"""
    Village: {row['Name']}
    District: {row['District']}
    Rainfall: {rainfall}
    Lightning: {lightning}
    AQI: {aqi}
    Forecast: {rainfall} rain next 1-3h
    Advisory: Avoid travel if {rainfall=='Heavy'}
    """
    
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=5,
        color='blue' if rainfall=='Light' else 'orange' if rainfall=='Moderate' else 'red',
        fill=True,
        fill_opacity=0.7,
        popup=popup_text
    ).add_to(m)

# Display map in Streamlit
st_folium(m, width=1000, height=700)