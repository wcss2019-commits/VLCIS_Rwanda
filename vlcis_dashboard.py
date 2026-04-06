import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
from folium.raster_layers import ImageOverlay
import numpy as np
import datetime
import time
import base64
import matplotlib.pyplot as plt
from io import BytesIO
import os
import requests
import rioxarray

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

DATA_PATH = r"C:\VLCIS\data\master_weather_data.csv"
LOGO_PATH = r"C:\VLCIS\logo.png"
REFRESH_INTERVAL = 600  # seconds

sat_folder = r"C:\VLCIS\satellite"
os.makedirs(sat_folder, exist_ok=True)

# ---------------- BRANDING ----------------
def get_base64_logo(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = get_base64_logo(LOGO_PATH)

st.markdown(f"""
<div style='display:flex; align-items:center; gap:15px;'>
    <img src="data:image/png;base64,{logo_base64}" width="80">
    <div>
        <h2>Virtual and Localized Climate Information Services (VLCIS)</h2>
        <h4>Rwanda Live Climate Risk Map</h4>
        <p>by Weather & Climate Sustainable Solutions Ltd</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------- CONTACT LINKS ----------------
st.markdown("""
📧 Email: wcss2019@gmail.com  
📞 Phone: +250793346422 / +250780761463  
🌐 Facebook: https://www.facebook.com/wcss2019  
🐦 X: https://x.com/CIS_Solutins  
📸 Instagram: https://www.instagram.com/wcss2019  
🎵 TikTok: https://www.tiktok.com/@cis_resilient_1  
▶️ YouTube: https://www.youtube.com/@Resilient_live
""")

# ---------------- LOAD DATA ----------------
def load_data():
    df = pd.read_csv(DATA_PATH)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# ---------------- THUNDER DETECTION ----------------
def detect_thunderstorm(row):
    return (row['humidity'] > 85) and (row['temperature'] < 24)

# ---------------- SIMULATE LIVE ----------------
def simulate_live_alerts(df):
    latest = df.sort_values('timestamp').groupby('station_name').tail(1).copy()
    latest['rainfall_mm'] = np.random.uniform(0, 50, len(latest))
    latest['thunderstorm'] = latest.apply(detect_thunderstorm, axis=1)
    return latest

# ---------------- AI RISK ----------------
def compute_risk(row):
    rain = row['rainfall_mm']
    humidity = row.get('humidity', 70)
    elevation = row.get('elevation', 1500)
    thunder = row['thunderstorm']

    rain_score = min(rain / 50, 1)
    humidity_score = min(humidity / 100, 1)
    elevation_score = min(elevation / 3000, 1)

    flood = 0.5*rain_score + 0.3*humidity_score + 0.2*(1 - elevation_score)
    landslide = 0.6*rain_score + 0.4*elevation_score
    storm = min(rain_score + (0.5 if thunder else 0), 1)

    return flood, landslide, storm

def risk_level(val):
    if val > 0.7:
        return "HIGH", "red"
    elif val > 0.4:
        return "MODERATE", "orange"
    else:
        return "LOW", "green"

# ---------------- TREND CHART ----------------
def generate_trend(df, station):
    data = df[df['station_name']==station].sort_values('timestamp').tail(3)
    fig, ax = plt.subplots()
    ax.plot(data['timestamp'], data['temperature'], marker='o')
    ax.set_title("Temp Trend")
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

# ---------------- CHIRPS ----------------
def download_chirps():
    today = datetime.datetime.utcnow().strftime("%Y.%m.%d")
    url = f"https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/tifs/p05/{today}.tif"
    path = os.path.join(sat_folder, "chirps.tif")
    try:
        r = requests.get(url)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            return path
    except:
        pass
    return None

# ---------------- MAIN LOOP ----------------
placeholder = st.empty()

while True:
    df = load_data()
    df_live = simulate_live_alerts(df)

    # AI risk
    df_live[['flood_risk','landslide_risk','storm_risk']] = df_live.apply(
        lambda r: pd.Series(compute_risk(r)), axis=1)

    df_live[['flood_level','flood_color']] = df_live['flood_risk'].apply(lambda x: pd.Series(risk_level(x)))
    df_live[['landslide_level','landslide_color']] = df_live['landslide_risk'].apply(lambda x: pd.Series(risk_level(x)))
    df_live[['storm_level','storm_color']] = df_live['storm_risk'].apply(lambda x: pd.Series(risk_level(x)))

    with placeholder.container():

        # Sidebar filters
        district = st.sidebar.selectbox("District", ["All"] + sorted(df['district'].unique().tolist()))
        stations = df['station_name'].unique().tolist()
        station = st.sidebar.selectbox("Station", ["All"] + stations)

        if district != "All":
            df_live = df_live[df_live['district']==district]
        if station != "All":
            df_live = df_live[df_live['station_name']==station]

        # Map
        m = folium.Map(location=[-1.94, 29.87], zoom_start=8)

        for _, row in df_live.iterrows():
            trend_img = generate_trend(df, row['station_name'])

            popup = f"""
            <b>{row['station_name']}</b><br>
            🌊 Flood: <span style='color:{row['flood_color']}'>{row['flood_level']}</span><br>
            ⛰️ Landslide: <span style='color:{row['landslide_color']}'>{row['landslide_level']}</span><br>
            ⚡ Storm: <span style='color:{row['storm_color']}'>{row['storm_level']}</span><br>
            <img src='data:image/png;base64,{trend_img}' width='150'>
            """

            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=8,
                color=row['flood_color'],
                fill=True,
                fill_opacity=0.7,
                popup=popup
            ).add_to(m)

        # Heatmap
        heat_data = [[r['latitude'], r['longitude'], r['rainfall_mm']] for _, r in df_live.iterrows()]
        HeatMap(heat_data).add_to(m)

        # Satellite
        chirps = download_chirps()
        if chirps:
            ds = rioxarray.open_rasterio(chirps)
            rain = ds.squeeze().values
            rain = np.nan_to_num(rain / np.nanmax(rain) * 255)

            bounds = [[float(ds.y.min()), float(ds.x.min())],
                      [float(ds.y.max()), float(ds.x.max())]]

            ImageOverlay(image=rain, bounds=bounds, opacity=0.5).add_to(m)

        st_folium(m, width=1400, height=700)

        # NATIONAL ALERT
        high = df_live[
            (df_live['flood_level']=="HIGH") |
            (df_live['landslide_level']=="HIGH") |
            (df_live['storm_level']=="HIGH")
        ]

        if not high.empty:
            stations = " | ".join(high['station_name'])
            st.markdown(f"""
            <marquee style='color:red; font-size:18px;'>
            🚨 HIGH RISK ALERT: {stations}
            </marquee>
            """, unsafe_allow_html=True)

    time.sleep(REFRESH_INTERVAL)