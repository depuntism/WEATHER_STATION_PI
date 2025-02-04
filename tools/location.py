import os
import ipdata

LAT = os.environ.get("LATITUDE")
LON = os.environ.get("LONGITUDE")
CITY = os.environ.get("CITY")
API_KEY = ("IPDATA_API_KEY")


def get_location():
    try:
        ipdata.api_key = API_KEY
        data = ipdata.lookup()
        if data["status"] == 200:
            return data["latitude"], data["longitude"], data["city"]
        else:
            return LAT, LON, CITY
    except Exception:
        return LAT, LON, CITY