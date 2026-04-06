import os
import requests
import xarray as xr
import pandas as pd
from datetime import datetime, timedelta

# --- Set NASA Earthdata credentials via environment variables ---
username = os.getenv("VLCIS_EARTHDATA_USERNAME")
token = os.getenv("VLCIS_EARTHDATA_TOKEN")

if username is None or token is None:
    raise ValueError("NASA Earthdata credentials not set in environment variables")

# Example: pull GPM rainfall (3-hourly) for a village
# Replace with your village coordinates
village_lat = -1.957  # Example: Kigali
village_lon = 30.061

# Define GPM data URL (using OpenDAP)
# NASA GPM IMERG Late Run: 0.1° global 30-min precipitation
# You can customize date/time window
end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=3)  # last 3 hours

# Format times for GPM API
time_str = end_time.strftime("%Y%m%d%H%M")

# Example dataset URL (adjust as needed)
gpm_url = f"https://gpm1.gesdisc.eosdis.nasa.gov/opendap/hdf5/GPM_Late/IMERG/{end_time.year}/{end_time.month:02d}/3B-HHR-L.MS.MRG.3IMERG.{time_str}-S000000-E235959.V06.nc4"

# Use requests with basic auth to check URL
response = requests.get(gpm_url, auth=(username, token))
if response.status_code == 200:
    print("✅ GPM data accessible!")
else:
    print(f"❌ Failed to access GPM: {response.status_code}")

# Optional: open the dataset with xarray
# ds = xr.open_dataset(gpm_url)
# Extract rainfall at nearest lat/lon
# rainfall = ds['precipitationCal'].sel(lat=village_lat, lon=village_lon, method='nearest')
# print("Rainfall (mm):", float(rainfall))