import streamlit as st
import requests
import base64
from pathlib import Path
import json


SETTINGS_PATH = Path("data/kiosk_settings.json")


def load_kiosk_settings():
    defaults = {
        "screensaver_enabled": True,
        "adhan_enabled": True,
        "idle_timeout": 5,
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


@st.cache_data(ttl=86400)
def get_prayer_times():
    try:
        response = requests.get(
            "https://api.aladhan.com/v1/timingsByCity",
            params={
                "city": "Cambridge",
                "country": "United Kingdom",
                "method": 3
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            timings = data["data"]["timings"]
            date_info = data["data"]["date"]
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
    except Exception:
        return None


@st.cache_data(ttl=3600)
def load_audio_files():
    adhan_dir = Path("static/adhan")
    prayers = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    audio_data = {}
    if not adhan_dir.exists():
        return audio_data
    for prayer in prayers:
        found = list(adhan_dir.glob(f"{prayer}.*"))
        if found:
            filepath = found[0]
            with open(filepath, "rb") as f:
                audio_bytes = f.read()
                b64 = base64.b64encode(audio_bytes).decode()
                ext = filepath.suffix[1:].lower()
                mime = {"mp3": "mpeg", "wav": "wav", "ogg": "ogg", "m4a": "mp4"}
                audio_data[prayer] = f"data:audio/{mime.get(ext, 'mpeg')};base64,{b64}"
    return audio_data


@st.cache_data(ttl=3600)
def load_background_images():
    bg_dir = Path("static/backgrounds")
    images = []
    if not bg_dir.exists():
        return images
    for filepath in sorted(bg_dir.iterdir()):
        if filepath.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            with open(filepath, "rb") as f:
                img_bytes = f.read()
                ext = filepath.suffix[1:].lower()
                mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}
                b64 = base64.b64encode(img_bytes).decode()
                images.append(f"data:image/{mime.get(ext, 'jpeg')};base64,{b64}")
    return images


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
    prayers = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    result = {}
    for prayer in prayers:
        found = list(adhan_dir.glob(f"{prayer}.*"))
        if found:
            result[prayer] = found[0].name
    return result


def get_kiosk_config():
    settings = load_kiosk_settings()
    prayer_times = get_prayer_times()

    screensaver_enabled = st.session_state.get("kiosk_screensaver_enabled", settings["screensaver_enabled"])
    adhan_enabled = st.session_state.get("kiosk_adhan_enabled", settings["adhan_enabled"])
    idle_timeout = st.session_state.get("kiosk_idle_timeout", settings["idle_timeout"])

    config = {
        "screensaver_enabled": screensaver_enabled,
        "adhan_enabled": adhan_enabled,
        "idle_timeout_ms": idle_timeout * 60 * 1000,
        "trigger_screensaver": st.session_state.pop("kiosk_test_screensaver", False),
        "prayer_times": prayer_times,
        "audio_files": get_audio_filenames(),
        "background_files": get_background_filenames(),
        "static_base": "/app/static",
    }
    return config


def get_prayer_names():
    return {
        "Fajr": "Fajr",
        "Dhuhr": "Dhuhr",
        "Asr": "Asr",
        "Maghrib": "Maghrib",
        "Isha": "Isha",
    }
