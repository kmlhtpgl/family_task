import streamlit as st
import requests
import hashlib
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
#
# The ?v= is a cache-buster derived from the file's own content. Streamlit
# serves static assets with a one-year max-age, so a browser that loaded the
# runtime once kept running that copy forever -- every fix pushed to kiosk.js
# was invisible on the wall tablet and on the deployed app, which is why local
# runs kept passing while the real deployment never changed.
#
# The runtime is INLINED rather than referenced, and that is deliberate. Loading
# it from /app/static/ meant the whole feature depended on a separate request
# succeeding: behind a login, behind nosniff, behind whatever headers the
# deployment adds. When that one request failed the runtime simply never ran,
# and every control in Admin went inert while the page still looked correct.
# The symptom was a status strip frozen on "connecting...", which is written by
# Python -- so the app rendered perfectly and the feature was simply absent.
# Inlining removes the request, the MIME check, the cache and the auth gate.
#
# It still satisfies the constant-iframe invariant: the file only changes when
# the code is deployed, so within a deploy the string is byte-identical on every
# rerun and Streamlit reuses the frame instead of destroying the audio element.
KIOSK_JS_PATH = Path("static/kiosk/kiosk.js")

# A plain identifier, not a hyphenated one: this is written into the inlined
# script as window.<NAME>, and "window.kiosk-runtime-failed" is a syntax error
# rather than a property access, which threw before the runtime ever ran.
KIOSK_RUNTIME_FAILED = "KIOSK_RUNTIME_FAILED"


def _kiosk_runtime_version():
    try:
        return hashlib.sha256(KIOSK_JS_PATH.read_bytes()).hexdigest()[:12]
    except OSError:
        return "0"


def _kiosk_runtime_source():
    """The runtime, inlined, with a version marker and a failure tripwire.

    The tripwire is what makes a dead runtime reportable. If the runtime throws
    on its first line, nothing in the page can tell the difference between "not
    loaded yet" and "loaded and working", because the code that would answer is
    the code that died. The marker is written before the runtime runs and the
    watchdog reads it, so the failure is visible on the page itself rather than
    only in a console nobody can open on a wall tablet.
    """
    try:
        source = KIOSK_JS_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        # Still emit the watchdog. A missing file is exactly the case the
        # watchdog exists to turn into a visible diagnosis.
        return (
            f'<script>window.{KIOSK_RUNTIME_FAILED} = "runtime file missing: {exc}";'
            f'window.KIOSK_RUNTIME_VERSION = "missing";</script>'
            + _kiosk_watchdog()
        )
    # A literal </script> anywhere in the source would close the tag early and
    # leave the rest of the file as page text.
    source = source.replace("</script", "<\\/script")
    return (
        # Armed before the runtime runs.
        f'<script>window.{KIOSK_RUNTIME_FAILED} = "runtime did not start";'
        f'window.KIOSK_RUNTIME_VERSION = "{_kiosk_runtime_version()}";</script>'
        f"<script>{source}</script>"
        # Disarmed only if the runtime actually finished wiring itself up. This
        # is a separate <script>, so it still runs when the runtime above throws,
        # which is the entire reason the failure can be reported at all.
        # Probed on the PARENT, because that is where the runtime installs
        # window.Kiosk. Checking this frame's own window always looks empty, so
        # the tripwire fires on a perfectly healthy runtime.
        f"<script>if (window.parent.Kiosk) {{ window.{KIOSK_RUNTIME_FAILED} = null; }}"
        f'else {{ window.{KIOSK_RUNTIME_FAILED} = "runtime failed to start"; }}'
        "window.parent.KIOSK_RUNTIME_BOOTED = window.parent.Kiosk ? 1 : 0;</script>"
        # The watchdog. It lives outside the runtime on purpose: when the runtime
        # dies, this is the only code left that can still speak. It writes the
        # reason into the Admin status strip, so "connecting..." is replaced by an
        # actual diagnosis instead of sitting there looking like slow loading.
        + _kiosk_watchdog()
    )


# Written as a plain template and substituted rather than an f-string. The
# braces here are real JavaScript, and doubling every one of them by hand is how
# two of them ended up unbalanced and the watchdog silently became a syntax
# error -- the one piece of code that has to survive the runtime dying.
_KIOSK_WATCHDOG_TEMPLATE = """
(function () {
    var parent = window.parent;
    var doc = parent.document;

    function report() {
        if (parent.Kiosk) return;
        var strip = doc.getElementById('kiosk-status');
        if (!strip) return;
        var runtime = strip.querySelector('[data-part="runtime"]');
        if (!runtime) return;
        /* Re-entrant on purpose. Streamlit redraws the strip on every rerun,
         * resetting it to "connecting…", so a one-shot latch would report once
         * and then leave a healthy-looking placeholder on screen forever. Only
         * the untouched placeholder is rewritten. */
        if (runtime.textContent.indexOf('connecting') === -1) return;
        var why = window.__FAILED__ || 'runtime script did not execute';
        runtime.textContent = 'RUNTIME NOT LOADED';
        runtime.setAttribute('data-tone', 'err');
        var version = strip.querySelector('[data-part="version"]');
        if (version) {
            version.textContent = why;
            version.setAttribute('data-tone', 'err');
        }
    }

    /* The strip does not exist yet when this runs. The iframe is mounted on
     * every page, but #kiosk-status is only rendered once the Kiosk tab is
     * opened -- often long after a one-shot timer would have fired and given
     * up. Watching the document means the check happens when the strip
     * actually appears, and again on every Streamlit rerun that redraws it. */
    if (parent.MutationObserver && doc.body) {
        new parent.MutationObserver(report).observe(doc.body, {
            childList: true,
            subtree: true
        });
    }
    setTimeout(report, 1500);
    setTimeout(report, 5000);
    setTimeout(report, 12000);
})();
"""


def _kiosk_watchdog():
    return (
        "<script>"
        + _KIOSK_WATCHDOG_TEMPLATE.replace("__FAILED__", KIOSK_RUNTIME_FAILED)
        + "</script>"
    )


KIOSK_IFRAME_HTML = _kiosk_runtime_source()


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
