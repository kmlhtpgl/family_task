"""The one navigation row, shared by the board and every other page.

The board used to hide this row and offer a single "Classic app" button
instead. That button described the implementation rather than the
destination, so from across a room the app read as having lost Reading,
Quran, Prayer and the rest. One row, rendered wherever you are, is what
makes the board a page of this app instead of a separate app with a door
in it.
"""
import streamlit as st

PAGES = (
    ("board", "", "Board"),
    ("parents", "", "Parents"),
    ("kids", "", "Kids"),
    ("reading", "", "Reading"),
    ("quran", "", "Quran"),
    ("prayer", "", "Prayer"),
    ("rewards", "", "Rewards"),
    ("meeting", "", "Meeting"),
    ("admin", "", "Admin"),
)


def render_nav(active: str) -> None:
    """Render the navigation row, marking `active` as the current page.

    Routing lives on `session_state.page` alone, so a click only has to set
    the page. An earlier version of the board also kept a shell flag, and
    the row was able to highlight Board while another page rendered, because
    those two pieces of state disagreed.
    """
    with st.container():
        # The .nav-scope marker is a styling hook only: it lets the
        # stylesheet target these buttons without leaking pill styling onto
        # every other button that happens to sit in a column.
        st.markdown('<div class="nav-scope"></div>', unsafe_allow_html=True)
        cols = st.columns(len(PAGES), gap="small")
        for col, (page_key, icon, label) in zip(cols, PAGES):
            btn_type = "primary" if page_key == active else "secondary"
            if col.button(
                label,
                key=f"nav_{page_key}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.page = page_key
                st.rerun()
