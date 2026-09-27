"""The Board, mounted as an alternate shell for the whole app.

Renders full-bleed rather than as one more entry in the nav bar. The point of
the redesign is that navigation stops being a row of page links, so bolting the
board onto the existing chrome would keep the thing being replaced.

What stays is what must not be disturbed: the kiosk iframe and its #kiosk-config
handoff are mounted by app.py above this, and they are load-bearing for adhan
and the screensaver. This page adds no iframe of its own beyond the board
component, and never touches the kiosk ones.
"""

import os

import streamlit as st

from utils.board.bridge import render
from utils.board.payload import build_board_payload

# The board fills whatever the host viewport has left, and static/board/board.js
# measures that space through the same-origin host before reporting its own frame
# height. These are only a starting hint for the first paint.
BOARD_HEIGHT_HINT = 760


TRUTHY = {"1", "true", "on", "yes"}


def board_flag_from_env(value: str | None) -> bool:
    """Whether an env value asks for the board. Split out from `board_enabled`
    so the parsing is testable without a Streamlit session behind it."""
    return (value or "").strip().lower() in TRUTHY


def board_enabled() -> bool:
    """Whether the board is the shell.

    Env var so a wall tablet can be pinned to it, with a session override so it
    can be compared against the classic app without a restart.
    """
    if "board_mode" in st.session_state:
        return bool(st.session_state.board_mode)
    return board_flag_from_env(os.environ.get("FAMILY_TASK_BOARD"))


def toggle_board(enabled: bool) -> None:
    st.session_state.board_mode = enabled


def board_page(data):
    payload = build_board_payload(data)
    totals = payload["totals"]

    # One compact row, not two. Every pixel of chrome is a pixel of board, and a
    # wall tablet is watched from across the room.
    left, right = st.columns([3, 1], gap="small", vertical_alignment="center")
    with left:
        st.markdown(
            '<div class="board-flag">'
            '<span class="board-flag__dot"></span>'
            "<b>Board</b> "
            f"<span>{totals['open_today']} open today · "
            f"{totals['overdue']} past due · read-only</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    with right:
        if st.button("Classic app", key="board_exit", use_container_width=True):
            toggle_board(False)
            st.rerun()

    render(payload, height=BOARD_HEIGHT_HINT)
