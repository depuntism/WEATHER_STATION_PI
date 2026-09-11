# -*- coding:utf-8 -*-
import locale
import time
import requests

# Timeout par défaut : 5s (connexion) / 15s (lecture)
DEFAULT_TIMEOUT = (5, 15)

try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    pass

BASE_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Correspondance codes WMO -> icônes/détails (jour)
WMO_DAY = {
    0: ("sun", "Beau temps"),
    1: ("25_clouds", "Peu nuageux"),
    2: ("50_clouds", "Nuageux"),
    3: ("100_clouds", "Couvert"),
    45: ("atm", "Brouillard"),
    48: ("atm", "Brouillard"),
    51: ("drizzle", "Bruine"),
    53: ("drizzle", "Bruine"),
    55: ("drizzle", "Bruine"),
    56: ("drizzle", "Bruine"),
    57: ("drizzle", "Bruine"),
    61: ("rain", "Pluie"),
    63: ("rain", "Pluie"),
    65: ("rain", "Pluie"),
    66: ("rain", "Pluie"),
    67: ("rain", "Pluie"),
    71: ("snow", "Neige"),
    73: ("snow", "Neige"),
    75: ("snow", "Neige"),
    77: ("snow", "Neige"),
    80: ("rain", "Pluie"),
    81: ("rain", "Pluie"),
    82: ("rain", "Pluie"),
    85: ("snow", "Neige"),
    86: ("snow", "Neige"),
    95: ("thunder", "Orage"),
    96: ("thunder", "Orage"),
    99: ("thunder", "Orage"),
}

# Correspondance codes WMO -> icônes/détails (nuit)
WMO_NIGHT = dict(WMO_DAY)
WMO_NIGHT[0] = ("moon", "Beau temps")
WMO_NIGHT[1] = ("26_cloudy_night", "Peu nuageux")


class Weather:
    def __init__(self, latitude, longitude, api_id=None):
        self.latitude = latitude
        self.longitude = longitude
        self.prevision = [0, [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]]
        self.data = self._fetch()
        self.sunrise = self.data["daily"]["sunrise"][0]
        self.sunset = self.data["daily"]["sunset"][0]
        self.prevision[0] = self.data["daily"]["time"][0]
        self.prevision[1][6] = [
            round(self.data["current"]["pressure_msl"]),
            round(self.data["current"]["temperature_2m"]),
        ]

    def _fetch(self):
        params = (
            f"latitude={self.latitude}&longitude={self.longitude}"
            "&current=temperature_2m,relative_humidity_2m,cloud_cover,"
            "pressure_msl,wind_speed_10m,wind_direction_10m,weather_code"
            "&minutely_15=precipitation&forecast_minutely_15=4"
            "&hourly=temperature_2m,precipitation_probability,weather_code"
            "&daily=weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,sunrise,sunset"
            "&models=best_match&timezone=auto&timeformat=unixtime"
        )
        response = requests.get(f"{BASE_URL}?{params}", timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def update(self):
        self.data = self._fetch()
        self.sunrise = self.data["daily"]["sunrise"][0]
        self.sunset = self.data["daily"]["sunset"][0]
        return self.data

    def current_time(self):
        return time.strftime(
            "%d/%m/%Y %H:%M", time.localtime(self.data["current"]["time"])
        )

    def current_temp(self):
        return "{:.0f}".format(self.data["current"]["temperature_2m"]) + "°C"

    def current_hum(self):
        return "{:.0f}".format(self.data["current"]["relative_humidity_2m"]) + "%"

    def current_cloud_cov(self):
        return "{:.0f}".format(self.data["current"]["cloud_cover"]) + "%"

    def current_sunrise(self):
        return time.strftime("%H:%M", time.localtime(self.sunrise))

    def current_sunset(self):
        return time.strftime("%H:%M", time.localtime(self.sunset))

    def current_wind(self):
        deg = self.data["current"]["wind_direction_10m"]
        if deg < 30 or deg >= 330:
            direction = "Nord"
        elif 30 <= deg < 60:
            direction = "Nord Est"
        elif 60 <= deg < 120:
            direction = "Est"
        elif 120 <= deg < 150:
            direction = "Sud Est"
        elif 150 <= deg < 210:
            direction = "Sud"
        elif 210 <= deg < 240:
            direction = "Sud Ouest"
        elif 240 <= deg < 300:
            direction = "Ouest"
        elif 300 <= deg < 330:
            direction = "Nord Ouest"
        else:
            direction = "N/A"
        # Open-Meteo renvoie déjà le vent en km/h
        return "{:.0f}".format(self.data["current"]["wind_speed_10m"]) + "km/h", direction

    def current_weather(self):
        return self.data["current"]["weather_code"]

    def rain_next_hour(self):
        rain_data = []
        minutely = self.data.get("minutely_15")
        if minutely and len(minutely.get("time", [])) > 0:
            labels = ["15'", "30'", "45'", "1h"]
            for i in range(min(4, len(minutely["time"]))):
                precipitation = minutely["precipitation"][i] or 0
                rain_data.append((labels[i], precipitation))
        elif "hourly" in self.data and len(self.data["hourly"]["time"]) > 0:
            idx = self._now_index()
            for offset in range(1, 7):
                pos = idx + offset
                if pos < len(self.data["hourly"]["time"]):
                    precipitation = self.data["hourly"]["precipitation"][pos] or 0
                    rain_data.append((f"{offset}h", precipitation))
        else:
            rain_data.append(("Erreur", 0))
        return rain_data

    def _now_index(self):
        now = self.data["current"]["time"]
        times = self.data["hourly"]["time"]
        index = 0
        for i, ts in enumerate(times):
            if ts <= now:
                index = i
            else:
                break
        return index

    def hourly_forecast(self):
        hourly = {
            "+3h": {"temp": "", "pop": "", "id": ""},
            "+6h": {"temp": "", "pop": "", "id": ""},
            "+12h": {"temp": "", "pop": "", "id": ""},
        }
        base = self._now_index()
        for key, offset in (("+3h", 3), ("+6h", 6), ("+12h", 12)):
            pos = base + offset
            hourly[key]["temp"] = (
                "{:.0f}".format(self.data["hourly"]["temperature_2m"][pos]) + "°C"
            )
            pop = self.data["hourly"]["precipitation_probability"][pos] or 0
            hourly[key]["pop"] = "{:.0f}".format(pop) + "%"
            hourly[key]["id"] = self.data["hourly"]["weather_code"][pos]
        return hourly

    def daily_forecast(self):
        daily = {
            "+24h": {"date": "", "min": "", "max": "", "pop": "", "id": ""},
            "+48h": {"date": "", "min": "", "max": "", "pop": "", "id": ""},
            "+72h": {"date": "", "min": "", "max": "", "pop": "", "id": ""},
            "+96h": {"date": "", "min": "", "max": "", "pop": "", "id": ""},
        }
        i = 1
        for key in daily.keys():
            daily[key]["date"] = time.strftime(
                "%A", time.localtime(self.data["daily"]["time"][i])
            )
            daily[key]["min"] = (
                "{:.0f}".format(self.data["daily"]["temperature_2m_min"][i]) + "°C"
            )
            daily[key]["max"] = (
                "{:.0f}".format(self.data["daily"]["temperature_2m_max"][i]) + "°C"
            )
            pop = self.data["daily"]["precipitation_probability_max"][i] or 0
            daily[key]["pop"] = "{:.0f}".format(pop) + "%"
            daily[key]["id"] = self.data["daily"]["weather_code"][i]
            i += 1
        return daily

    def graph_p_t(self):
        today = self.data["daily"]["time"][0]
        if self.prevision[0] != today:
            self.prevision[0] = today
            self.prevision = [self.prevision[0], self.prevision[1][1:]]
            self.prevision[1].append(
                [
                    round(self.data["current"]["pressure_msl"]),
                    round(self.data["current"]["temperature_2m"]),
                ]
            )

    def weather_description(self, id):
        current_time = time.strftime("%H:%M", time.localtime())
        if "08:00" <= current_time <= "20:00":
            icon, weather_detail = WMO_DAY.get(id, ("sun", "Beau temps"))
        else:
            icon, weather_detail = WMO_NIGHT.get(id, ("moon", "Beau temps"))
        return icon, weather_detail

    def alert(self):
        # Open-Meteo ne fournit pas d'alertes officielles
        return 0


class Pollution:
    def __init__(self):
        self.max_lvl_pollution = {
            "co": 10000,
            "no": None,
            "no2": 40,
            "o3": 120,
            "so2": 50,
            "pm2_5": 20,
            "pm10": 30,
            "nh3": None,
        }

    def update(self, lattitude, longitude, api_id=None):
        params = (
            f"latitude={lattitude}&longitude={longitude}"
            "&current=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,"
            "sulphur_dioxide,ozone&timezone=auto"
        )
        response = requests.get(f"{AIR_QUALITY_URL}?{params}", timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        self.data = response.json()
        return self.data

    def co(self):
        return self.data["current"]["carbon_monoxide"]

    def no(self):
        # Non fourni par Open-Meteo
        return 0

    def no2(self):
        return self.data["current"]["nitrogen_dioxide"]

    def o3(self):
        return self.data["current"]["ozone"]

    def so2(self):
        return self.data["current"]["sulphur_dioxide"]

    def pm2_5(self):
        return self.data["current"]["pm2_5"]

    def pm10(self):
        return self.data["current"]["pm10"]

    def nh3(self):
        # Non fourni par Open-Meteo
        return 0
