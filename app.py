import json
from datetime import date
from html import escape

import streamlit as st
import streamlit.components.v1 as components
from utils.db_helpers import get_all_data
from utils.styles import apply_custom_styles
from utils.kiosk_helpers import get_kiosk_bootstrap, KIOSK_IFRAME_HTML
from utils.admin_helpers import load_admin_password
from app_pages.dashboard import dashboard_page
from app_pages.kanban import kanban_page
from app_pages.kids_profiles import kids_profiles_page
from app_pages.parents_profiles import parents_profiles_page
from app_pages.reading_library import reading_library_page
from app_pages.surah_memorization import surah_memorization_page
from app_pages.rewards import rewards_page
from app_pages.meeting import meeting_page
from app_pages.admin import admin_page
from app_pages.prayer import prayer_page

st.set_page_config(
    page_title="Family Task Tracker",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark mode toggle
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Apply custom styles based on dark mode
apply_custom_styles(dark_mode=st.session_state.dark_mode)

st.markdown("""
    <style>
    .family-bg {
        position: fixed;
        bottom: 0;
        right: 0;
        width: 260px;
        height: 260px;
        opacity: 0.05;
        pointer-events: none;
        z-index: -1;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 400'%3E%3Cg fill='%233879FA'%3E%3Ccircle cx='200' cy='80' r='25'/%3E%3Cpath d='M175 130 Q200 110 225 130 L220 180 Q200 170 180 180 Z'/%3E%3Cpath d='M160 180 L145 240 L170 240 L180 190 Z'/%3E%3Cpath d='M240 180 L255 240 L230 240 L220 190 Z'/%3E%3C/g%3E%3Cg fill='%237AACFC'%3E%3Ccircle cx='130' cy='140' r='18'/%3E%3Cpath d='M112 180 Q130 165 148 180 L144 220 Q130 215 116 220 Z'/%3E%3Cpath d='M104 220 L95 270 L115 270 L112 230 Z'/%3E%3Cpath d='M156 220 L165 270 L145 270 L148 230 Z'/%3E%3C/g%3E%3Cg fill='%237AACFC'%3E%3Ccircle cx='270' cy='140' r='18'/%3E%3Cpath d='M252 180 Q270 165 288 180 L284 220 Q270 215 256 220 Z'/%3E%3Cpath d='M244 220 L235 270 L255 270 L252 230 Z'/%3E%3Cpath d='M296 220 L305 270 L285 270 L288 230 Z'/%3E%3C/g%3E%3Ccircle cx='100' cy='300' r='30' fill='%233879FA' opacity='0.5'/%3E%3Ccircle cx='300' cy='320' r='25' fill='%237AACFC' opacity='0.5'/%3E%3C/svg%3E");
        background-size: contain;
        background-repeat: no-repeat;
    }
    </style>

    <div class="family-bg"></div>
""", unsafe_allow_html=True)

# Portable date: '%-d' is a glibc-only strftime flag and renders literally as
# "-d" on macOS/BSD, so the day number is formatted separately.
_today = date.today()
_today_label = f"{_today:%a} {_today.day} {_today:%b %Y}"

st.markdown(f"""
    <div class="top-navbar">
        <a href="?nav=dashboard" class="navbar-brand">
            <h1>Family Task</h1>
        </a>
        <div class="navbar-actions">
            <div class="nav-date">{_today_label}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── Kiosk Module (screensaver + adhan) ──
# The runtime lives in static/kiosk/kiosk.js and is loaded by a CONSTANT
# iframe. Config is handed over as JSON in a hidden node rather than being
# interpolated into the iframe HTML: the iframe string must never change, or
# Streamlit recreates the frame and takes the audio element down with it.
_kiosk_cfg = json.dumps(get_kiosk_bootstrap())

st.markdown(
    f'<div id="kiosk-config" style="display:none">{escape(_kiosk_cfg, quote=False)}</div>',
    unsafe_allow_html=True,
)

components.html(KIOSK_IFRAME_HTML, height=0)

# Page navigation bar
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

pages = [
    ("dashboard", "📊", "Dashboard"),
    ("kanban", "🎯", "Daily Board"),
    ("parents", "👨‍👩‍👧", "Parents"),
    ("kids", "🧒", "Kids"),
    ("reading", "📚", "Reading"),
    ("quran", "📖", "Quran"),
    ("prayer", "🕌", "Prayer"),
    ("rewards", "💰", "Rewards"),
    ("meeting", "👪", "Meeting"),
    ("admin", "⚙️", "Admin"),
]

# Create navigation buttons. The .nav-scope marker is a styling hook only: it
# lets the stylesheet target these buttons without leaking pill styling onto
# every other button that happens to sit in a column.
with st.container():
    st.markdown('<div class="nav-scope"></div>', unsafe_allow_html=True)
    cols = st.columns(len(pages), gap="small")
    for col, (page_key, icon, label) in zip(cols, pages):
        is_active = page_key == st.session_state.page
        btn_type = "primary" if is_active else "secondary"

        if col.button(
            f"{icon} {label}",
            key=f"nav_{page_key}",
            use_container_width=True,
            type=btn_type,
        ):
            st.session_state.page = page_key
            st.rerun()

# Handle nav query param (clicking the Family Task header)
if st.query_params.get("nav") == "dashboard":
    st.session_state.page = "dashboard"
    st.query_params.clear()
    st.rerun()

data = get_all_data()

# Determine page from session state
page = st.session_state.get("page", "dashboard")

# Route to pages
if page == "dashboard":
    dashboard_page(data)

elif page == "kanban":
    kanban_page(data)

elif page == "parents":
    parents_profiles_page(data)

elif page == "kids":
    kids_profiles_page(data)

elif page == "reading":
    reading_library_page(data)

elif page == "quran":
    surah_memorization_page(data)

elif page == "prayer":
    prayer_page(data)

elif page == "rewards":
    rewards_page(data)

elif page == "meeting":
    meeting_page(data)

elif page == "admin":
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        st.warning("🔒 Admin section is password-protected.")
        with st.form("admin_login"):
            pwd = st.text_input("Enter admin password", type="password")
            if st.form_submit_button("Unlock"):
                if pwd == load_admin_password():
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
    else:
        admin_page(data)
