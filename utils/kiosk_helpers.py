import streamlit as st
import requests
from pathlib import Path
import json
from datetime import date, datetime


SETTINGS_PATH = Path("data/kiosk_settings.json")


def load_kiosk_settings():
    defaults = {
        "screensaver_enabled": True,
        "adhan_enabled": True,
        "idle_timeout": 1,
        "weather_enabled": True,
        "weather_city": "Cambridge",
        "weather_unit": "celsius",
    }
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH) as f:
            return {**defaults, **json.load(f)}
    return defaults


def save_kiosk_settings(**kwargs):
    current = load_kiosk_settings()
    current.update(kwargs)
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(current, f, indent=2)


PRAYER_TIMES_CACHE_PATH = Path("data/prayer_times_cache.json")

ALADHAN_URL = "https://api.aladhan.com/v1/timings"
ISLAMIC_APP_URL = "https://api.islamic.app/v1/timings/today"

PRAYER_LAT = 52.2053
PRAYER_LON = 0.1218
PRAYER_TIMEZONE = "Europe/London"
PRAYER_CITY = "Cambridge"
PRAYER_COUNTRY = "United Kingdom"
PRAYER_COUNTRY_CODE = "GB"
PRAYER_METHOD = 15
PRAYER_SCHOOL = 1

PRAYER_KEYS = ["fajr", "dhuhr", "asr", "maghrib", "isha"]

# Cambridge Central Mosque calls the adhan for Fajr ahead of sunrise rather
# than at the calculated Fajr time. Negative = lead time, in minutes.
FAJR_OFFSET_MIN = -10

# The iframe that loads static/kiosk/kiosk.js. This string MUST stay
# byte-identical on every rerun: Streamlit hashes each component, and an
# unchanged hash means the iframe element is reused instead of recreated.
# A recreated iframe destroys every timer and the audio element, which is
# exactly how the previous adhan implementation kept going silent.
KIOSK_IFRAME_HTML = '<script src="/app/static/kiosk/kiosk.js"></script>'


def _parse_timings(data):
    timings = data["timings"]
    date_info = data["date"]
    return {
        "Fajr": timings["Fajr"],
        "Sunrise": timings["Sunrise"],
        "Dhuhr": timings["Dhuhr"],
        "Asr": timings["Asr"],
        "Maghrib": timings["Maghrib"],
        "Isha": timings["Isha"],
        "date": date_info["readable"],
        "hijri_date": date_info["hijri"]["date"],
    }


@st.cache_data(ttl=3600)
def _fetch_aladhan():
    try:
        response = requests.get(
            f"{ALADHAN_URL}/{date.today().strftime('%d-%m-%Y')}",
            params={
                "latitude": PRAYER_LAT,
                "longitude": PRAYER_LON,
                "method": PRAYER_METHOD,
                "school": PRAYER_SCHOOL,
                "timezone": PRAYER_TIMEZONE,
            },
            timeout=10,
        )
        if response.status_code == 200:
            return _parse_timings(response.json()["data"])
    except Exception:
        pass
    return None


@st.cache_data(ttl=21600)
def _fetch_islamic_app():
    try:
        response = requests.get(
            ISLAMIC_APP_URL,
            params={
                "city": PRAYER_CITY,
                "country": PRAYER_COUNTRY_CODE,
                "method": PRAYER_METHOD,
                "school": PRAYER_SCHOOL,
            },
            timeout=10,
        )
        if response.status_code == 200:
            return _parse_timings(response.json()["data"])
    except Exception:
        pass
    return None


def _today_key():
    return date.today().strftime("%d-%m-%Y")


def _days_since(cache_date_str):
    try:
        d = datetime.strptime(cache_date_str, "%d-%m-%Y").date()
        return (date.today() - d).days
    except (ValueError, TypeError):
        return 999


def _load_prayer_times_cache():
    if PRAYER_TIMES_CACHE_PATH.exists():
        try:
            with open(PRAYER_TIMES_CACHE_PATH) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_prayer_times_cache(payload):
    try:
        PRAYER_TIMES_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PRAYER_TIMES_CACHE_PATH, "w") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        pass


def get_prayer_times():
    today_key = _today_key()
    cache = _load_prayer_times_cache()

    # 1. Fresh cached copy for today (fast, offline-safe)
    if cache.get("date") == today_key and cache.get("timings"):
        return cache["timings"]

    # 2. Fetch from providers, in order; only accept today's data
    for fetch in (_fetch_aladhan, _fetch_islamic_app):
        timings = fetch()
        if timings and timings.get("date") == today_key:
            _save_prayer_times_cache({"date": today_key, "timings": timings})
            return timings

    # 3. Last resort: recent cached copy (within ~2 days) so the screen
    #    still shows times during a long outage.
    if cache.get("timings") and _days_since(cache.get("date", "")) <= 2:
        return cache["timings"]

    return None


WMO_CONDITIONS = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    56: ("Freezing drizzle", "🌧️"),
    57: ("Freezing drizzle", "🌧️"),
    61: ("Light rain", "🌦️"),
    63: ("Rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Freezing rain", "🌧️"),
    67: ("Freezing rain", "🌧️"),
    71: ("Light snow", "🌨️"),
    73: ("Snow", "🌨️"),
    75: ("Heavy snow", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Light showers", "🌦️"),
    81: ("Showers", "🌧️"),
    82: ("Violent showers", "⛈️"),
    85: ("Snow showers", "🌨️"),
    86: ("Snow showers", "🌨️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm", "⛈️"),
    99: ("Thunderstorm", "⛈️"),
}


@st.cache_data(ttl=1800)
def get_weather(city="Cambridge", unit="celsius"):
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        if geo.status_code != 200 or not geo.json().get("results"):
            return None
        result = geo.json()["results"][0]
        lat = result["latitude"]
        lon = result["longitude"]
        country = result.get("country", "")

        unit_map = {"celsius": "celsius", "fahrenheit": "fahrenheit"}
        model_unit = unit_map.get(unit, "celsius")

        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "temperature_unit": model_unit,
                "wind_speed_unit": "kmh",
                "timezone": "auto",
                "forecast_days": 1,
            },
            timeout=10,
        )
        if response.status_code != 200:
            return None
        current = response.json()["current"]
        code = current["weather_code"]
        condition, icon = WMO_CONDITIONS.get(code, ("", "🌡️"))
        temp = round(current["temperature_2m"])
        temp_unit = "°C" if model_unit == "celsius" else "°F"
        return {
            "city": city,
            "country": country,
            "temp": temp,
            "unit": temp_unit,
            "condition": condition,
            "icon": icon,
            "humidity": current.get("relative_humidity_2m"),
            "wind": current.get("wind_speed_10m"),
        }
    except Exception:
        return None


def get_background_filenames():
    bg_dir = Path("static/backgrounds")
    files = []
    if bg_dir.exists():
        for f in sorted(bg_dir.iterdir()):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
                files.append(f.name)
    return files


def get_audio_filenames():
    adhan_dir = Path("static/adhan")
    result = {}
    for prayer in PRAYER_KEYS:
        found = list(adhan_dir.glob(f"{prayer}.*"))
        if found:
            result[prayer] = found[0].name
    return result


def get_audio_bytes(prayer):
    """Raw bytes for a single adhan file, for st.audio previews only.

    Playback in the browser streams straight from /app/static/adhan/, so
    nothing in the runtime path needs base64 any more.
    """
    adhan_dir = Path("static/adhan")
    found = list(adhan_dir.glob(f"{prayer}.*"))
    if not found:
        return None
    return found[0].read_bytes()


def get_kiosk_bootstrap():
    """Config for static/kiosk/kiosk.js, serialised into #kiosk-config.

    Deliberately small. The client fetches prayer times itself (both APIs
    send `Access-Control-Allow-Origin: *`) and streams adhan audio and
    background images from /app/static/, so none of that is embedded here.
    That is what keeps the iframe payload constant across reruns.
    """
    settings = load_kiosk_settings()

    screensaver_enabled = st.session_state.get("kiosk_screensaver_enabled", settings["screensaver_enabled"])
    adhan_enabled = st.session_state.get("kiosk_adhan_enabled", settings["adhan_enabled"])
    idle_timeout = st.session_state.get("kiosk_idle_timeout", settings["idle_timeout"])
    weather_enabled = st.session_state.get("kiosk_weather_enabled", settings["weather_enabled"])
    weather_city = st.session_state.get("kiosk_weather_city", settings["weather_city"])
    weather_unit = st.session_state.get("kiosk_weather_unit", settings["weather_unit"])

    return {
        "screensaver_enabled": bool(screensaver_enabled),
        "adhan_enabled": bool(adhan_enabled),
        "idle_timeout_ms": int(idle_timeout) * 60 * 1000,
        "trigger_screensaver": st.session_state.pop("kiosk_test_screensaver", False),
        "trigger_adhan": st.session_state.pop("kiosk_test_adhan", None),
        "diagnostics": bool(st.session_state.get("kiosk_diagnostics", False)),
        "adhan_files": get_audio_filenames(),
        "backgrounds": get_background_filenames(),
        "lat": PRAYER_LAT,
        "lon": PRAYER_LON,
        "method": PRAYER_METHOD,
        "school": PRAYER_SCHOOL,
        "fajr_offset_min": FAJR_OFFSET_MIN,
        "weather_enabled": bool(weather_enabled),
        "weather": get_weather(weather_city or "Cambridge", weather_unit) if weather_enabled else None,
    }
