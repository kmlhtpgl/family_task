import json
from html import escape

import streamlit as st
import streamlit.components.v1 as components
from utils.db_helpers import get_all_data
from utils.styles import apply_custom_styles
from utils.kiosk_helpers import get_kiosk_bootstrap, KIOSK_IFRAME_HTML
from utils.admin_helpers import load_admin_password
from app_pages.kids_profiles import kids_profiles_page
from app_pages.parents_profiles import parents_profiles_page
from app_pages.reading_library import reading_library_page
from app_pages.surah_memorization import surah_memorization_page
from app_pages.rewards import rewards_page
from app_pages.meeting import meeting_page
from app_pages.admin import admin_page
from app_pages.prayer import prayer_page
from app_pages.board import (
    CLASSIC_LANDING,
    board_enabled,
    board_page,
)
from utils.nav import render_nav

st.set_page_config(
    page_title="Family Task Tracker",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# One stylesheet for the whole app, mounted before anything renders so every
# page below inherits the same design. There is no theme argument: the Board's
# palette is the only one (utils/styles.py).
apply_custom_styles()

st.markdown("""<div class="family-bg"></div>""", unsafe_allow_html=True)

# ── Page resolution ─────────────────────────────────────────────────────────
# Resolved before any chrome is rendered, because the page decides the chrome:
# the board needs its own full-bleed styling, everything else gets the title bar.
# Deciding it afterwards is what let the nav row highlight Board while a
# different page rendered, because the two halves disagreed.
_lands_on_board = board_enabled()

if "page" not in st.session_state:
    st.session_state.page = "board" if _lands_on_board else CLASSIC_LANDING

# The compact workspace flag on the other pages is a link back to the board.
if st.query_params.get("nav") == "board":
    st.session_state.page = "board"
    st.query_params.clear()

page = st.session_state.page
_on_board = page == "board"

# ── Kiosk Module (screensaver + adhan) ──
# The runtime lives in static/kiosk/kiosk.js and is loaded by a CONSTANT
# iframe. Config is handed over as JSON in a hidden node rather than being
# interpolated into the iframe HTML: the iframe string must never change, or
# Streamlit recreates the frame and takes the audio element down with it.
#
# This runs on every page, board included. Adhan and the screensaver are not
# part of the redesign and must keep working on the wall tablet, so the board is
# not allowed to take this over.
_kiosk_cfg = json.dumps(get_kiosk_bootstrap())

st.markdown(
    f'<div id="kiosk-config" style="display:none">{escape(_kiosk_cfg, quote=False)}</div>',
    unsafe_allow_html=True,
)

components.html(KIOSK_IFRAME_HTML, height=0)

if _on_board:
    # Streamlit's own header and block padding would otherwise frame the board
    # in a page it is trying to replace. Scoped to the board: the other pages
    # keep their header and their padded body.
    #
    # Layout only. The board's colours come from utils/styles.py like
    # everything else's; they used to be written out again here, which is how
    # the same Board ended up two palettes depending on which file you read.
    st.markdown(
        """
        <style>
        header[data-testid="stHeader"], #MainMenu, footer { display: none; }
        [data-testid="stToolbar"] { display: none; }
        /* Streamlit's wide layout caps the block container at 1200px and centres
           it, which leaves a 40px gutter down each side of a wall display. The
           attribute selector is needed to beat the rule Streamlit sets on the
           same element. */
        div[data-testid="stMainBlockContainer"] {
            padding: 0 !important;
            max-width: none !important;
            width: 100% !important;
        }
        /* No global gap: app.py mounts several zero-height containers for the
           kiosk handoff above the board, and a gap charges 8px for each one even
           when it renders nothing. That was 48px of dead space on a wall
           display. */
        [data-testid="stVerticalBlock"] { gap: 0; }
        [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"]
            > [data-testid="stLayoutWrapper"] { margin-top: 10px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    board_page(get_all_data)
    st.stop()

# The board and the old Daily Board are gone from here: the board is the app's
# landing page in its own right, and the Daily Board duplicated it. The row
# itself is shared with the board, so the two halves cannot drift apart.
#
# Rendered before the fetch: a click reruns the script, and the whole of
# get_all_data would otherwise be spent on a run that is thrown away.
render_nav(page)

data = get_all_data()

# Route to pages
if page == "board":
    # Unreachable in practice: the board returned at the top of the file. Kept so
    # a page value that lands here still draws the board rather than falling
    # through to a blank branch.
    board_page(get_all_data)

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
