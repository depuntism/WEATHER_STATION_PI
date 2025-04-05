import os
import ipdata

from dotenv import load_dotenv

load_dotenv()

LAT = os.environ.get("LATITUDE")
LON = os.environ.get("LONGITUDE")
CITY = os.environ.get("CITY")
IPDATA_KEY = os.environ.get("IPDATA_API_KEY")
is_location_enabled = os.environ.get("ENABLE_WEATHER_LOCATION")

def get_location():
    if is_location_enabled:
        try:
            ipdata.api_key = IPDATA_KEY
            data = ipdata.lookup()
            if data["status"] == 200:
                return data["latitude"], data["longitude"], data["city"]
            else:
                return LAT, LON, CITY
        except Exception:
            return LAT, LON, CITY
    
    return LAT, LON, CITY