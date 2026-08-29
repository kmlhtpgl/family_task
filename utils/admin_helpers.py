import json
from pathlib import Path

import streamlit as st

from utils.supabase_client import get_supabase_client

ADMIN_SETTINGS_PATH = Path("data/admin_settings.json")
ADMIN_PASSWORD_KEY = "admin_password"


def _load_local_settings():
    try:
        if ADMIN_SETTINGS_PATH.exists():
            with open(ADMIN_SETTINGS_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_local_settings(settings):
    try:
        ADMIN_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ADMIN_SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception:
        return False


def _read_from_supabase():
    try:
        result = (
            get_supabase_client()
            .table("app_settings")
            .select("value")
            .eq("key", ADMIN_PASSWORD_KEY)
            .execute()
            .data
        )
        if result and result[0].get("value"):
            return result[0]["value"]
    except Exception:
        pass
    return None


def _write_to_supabase(password):
    try:
        get_supabase_client().table("app_settings").upsert(
            {"key": ADMIN_PASSWORD_KEY, "value": password},
        ).execute()
        return True
    except Exception:
        return False


def load_admin_password():
    """Return the shared admin password.

    Source of truth is Supabase so every device sees the same value.
    Falls back to the local file (offline cache), then to the default
    stored in Streamlit secrets, seeding upstream as needed.
    """
    default = st.secrets["ADMIN_PASSWORD"]

    # 1. Shared value in Supabase (covers all gadgets)
    from_supabase = _read_from_supabase()
    if from_supabase:
        _save_local_settings({ADMIN_PASSWORD_KEY: from_supabase})
        return from_supabase

    # 2. Local offline cache
    local = _load_local_settings().get(ADMIN_PASSWORD_KEY)
    if local:
        # Re-sync the shared store so other devices pick it up.
        _write_to_supabase(local)
        return local

    # 3. Default from secrets; seed the shared store and local cache.
    _write_to_supabase(default)
    _save_local_settings({ADMIN_PASSWORD_KEY: default})
    return default


def save_admin_password(password):
    """Persist the new admin password for every device."""
    _write_to_supabase(password)
    _save_local_settings({ADMIN_PASSWORD_KEY: password})