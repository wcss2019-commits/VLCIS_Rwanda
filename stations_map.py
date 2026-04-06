import pandas as pd
import folium

# File paths
stations_csv = r"C:\VLCIS\VLCIS_Rw\dashboard\data2\vlcis_stations_final_cleaned.csv"
map_html = r"C:\VLCIS\VLCIS_Rw\dashboard\data2\vlcis_stations_map.html"

# Load data
df = pd.read_csv(stations_csv)

# Create map
m = folium.Map(location=[-1.94, 29.88], zoom_start=8, tiles=None)

# Google Maps layer
folium.TileLayer(
    tiles='https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attr='Google',
    subdomains=['mt0', 'mt1', 'mt2', 'mt3']
).add_to(m)

# Add stations
for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=3,
        color='blue',
        fill=True,
        fill_opacity=0.7,
        popup=row['station_name']
    ).add_to(m)

# Save map
m.save(map_html)

print("✅ Map created!")
print("Open:", map_html)