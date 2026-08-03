import json
from pathlib import Path

import streamlit as st

ADMIN_SETTINGS_PATH = Path("data/admin_settings.json")


def load_admin_password():
    defaults = {"admin_password": st.secrets["ADMIN_PASSWORD"]}

    if ADMIN_SETTINGS_PATH.exists():
        with open(ADMIN_SETTINGS_PATH) as f:
            settings = {**defaults, **json.load(f)}
            if settings["admin_password"]:
                return settings["admin_password"]

    save_admin_password(defaults["admin_password"])
    return defaults["admin_password"]


def save_admin_password(password):
    ADMIN_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ADMIN_SETTINGS_PATH, "w") as f:
        json.dump({"admin_password": password}, f, indent=2)
