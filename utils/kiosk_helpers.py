import streamlit as st
import requests
import base64
from pathlib import Path
import json


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


def get_kiosk_config():
    prayer_times = get_prayer_times()
    audio_data = load_audio_files()
    background_images = load_background_images()

    config = {
        "screensaver_enabled": st.session_state.get("kiosk_screensaver_enabled", True),
        "adhan_enabled": st.session_state.get("kiosk_adhan_enabled", True),
        "idle_timeout_ms": st.session_state.get("kiosk_idle_timeout", 5) * 60 * 1000,
        "prayer_times": prayer_times,
        "audio_data": audio_data,
        "background_images": background_images,
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
