# ===============================================
# VLCIS Rwanda Live Climate Risk Map Dashboard
# Updated: April 2026
# Features:
# - Correct station coordinates
# - Sector selection (handles duplicates)
# - Google Map visualization
# - Company logo on top right
# ===============================================

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# -----------------------------
# Paths
# -----------------------------
stations_csv = r"C:\VLCIS\VLCIS_Rw\dashboard\data2\vlcis_stations_final.csv"
logo_path = r"C:\VLCIS\VLCIS_Rw\dashboard\logo.png"

# -----------------------------
# Streamlit Page Setup
# -----------------------------
st.set_page_config(
    page_title="VLCIS Rwanda Live Climate Risk Map",
    layout="wide"
)

# -----------------------------
# Sidebar: Logo + Info
# -----------------------------
st.sidebar.image(logo_path, width=150)
st.sidebar.markdown("""
### 🌍 Virtual and Localized Climate Information Services (VLCIS)
Rwanda Live Climate Risk Map  
Weather & Climate Sustainable Solutions Ltd

📧 wcss2019@gmail.com  
📞 +250793346422 / +250780761463  
🌐 Facebook: [wcss2019](https://www.facebook.com/wcss2019)  
🐦 X: [CIS_Solutins](https://x.com/CIS_Solutins)  
📸 Instagram: [wcss2019](https://www.instagram.com/wcss2019)  
🎵 TikTok: [cis_resilient_1](https://www.tiktok.com/@cis_resilient_1)  
▶️ YouTube: [Resilient Live](https://www.youtube.com/@Resilient_live)  
""")

# -----------------------------
# Load Stations Data
# -----------------------------
df_stations = pd.read_csv(stations_csv)

# Ensure coordinates are floats
df_stations['latitude'] = df_stations['latitude'].astype(float)
df_stations['longitude'] = df_stations['longitude'].astype(float)

# -----------------------------
# Sector Selection
# -----------------------------
# Create unique sector names by combining district + sector if needed
df_stations['sector_display'] = df_stations['station_name']  # Already unique like RuhangoByimana
sector_options = sorted(df_stations['sector_display'].unique())

selected_sector = st.selectbox("Select Sector", ["All Sectors"] + sector_options)

# Filter stations based on selection
if selected_sector != "All Sectors":
    df_filtered = df_stations[df_stations['sector_display'] == selected_sector]
else:
    df_filtered = df_stations.copy()

# -----------------------------
# Map Display
# -----------------------------
# Initialize map at Rwanda center
m = folium.Map(location=[-1.9403, 29.8739], zoom_start=8, tiles="CartoDB positron")

# Add station markers
marker_cluster = MarkerCluster().add_to(m)

for idx, row in df_filtered.iterrows():
    popup_text = f"""
    <b>{row['station_name']}</b><br>
    Latitude: {row['latitude']}<br>
    Longitude: {row['longitude']}
    """
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=popup_text,
        icon=folium.Icon(color='blue', icon='cloud')
    ).add_to(marker_cluster)

# -----------------------------
# Render Map in Streamlit
# -----------------------------
st.markdown("## 🌍 Rwanda Climate Risk Map")
st_data = st_folium(m, width=1200, height=700)

# -----------------------------
# Sector Alerts (Optional)
# -----------------------------
if selected_sector != "All Sectors":
    st.markdown("### ⚠️ Alerts for Selected Sector")
    # Placeholder: compute or display alerts per station
    for idx, row in df_filtered.iterrows():
        st.write(f"{row['station_name']}: Flood Risk: 0.00 | Landslide Risk: 0.00 | Storm Risk: 0.00")