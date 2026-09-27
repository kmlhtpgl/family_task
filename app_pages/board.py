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

from utils.board.actions import apply_action
from utils.board.bridge import render
from utils.board.payload import build_board_payload

# The board fills whatever the host viewport has left, and static/board/board.js
# measures that space through the same-origin host before reporting its own frame
# height. These are only a starting hint for the first paint.
BOARD_HEIGHT_HINT = 760

# Where the classic shell lands. Not "board": the classic shell is the way to
# the pages the board does not replace, so arriving on the board again would be
# arriving nowhere.
CLASSIC_LANDING = "parents"


TRUTHY = {"1", "true", "on", "yes"}


def flag_from_env(value: str | None) -> bool:
    """Whether an env value asks for something. Split out from `board_enabled`
    so the parsing is testable without a Streamlit session behind it."""
    return (value or "").strip().lower() in TRUTHY


def board_enabled() -> bool:
    """Whether the board is the shell.

    The board is the app, so it is on by default. The escape hatch is now
    FAMILY_TASK_CLASSIC rather than FAMILY_TASK_BOARD: a flag that has to be set
    to reach the main surface is a flag that gets left off, which is how this
    whole screen ended up invisible in the first place.
    """
    if "board_mode" in st.session_state:
        return bool(st.session_state.board_mode)
    return not flag_from_env(os.environ.get("FAMILY_TASK_CLASSIC"))


def toggle_board(enabled: bool) -> None:
    """Switch shells, and land somewhere that belongs to the new one.

    Leaving `page` alone would strand the classic shell on "board", whose only
    route renders the board again -- the way out would be a way back in.
    """
    st.session_state.board_mode = enabled
    st.session_state.page = "board" if enabled else CLASSIC_LANDING


FLASH_KEY = "board_flash"


def pop_flash() -> dict | None:
    """The last action's result, offered to the canvas exactly once.

    It rides in the payload for a single render and is then dropped, so a
    confirmation cannot stick to the wall saying "done" about a task that was
    undone an hour later.
    """
    return st.session_state.pop(FLASH_KEY, None)


def board_page(refetch):
    """Render the board, then apply whatever it asked for.

    `refetch` rather than a dict because the payload has to be rebuilt from the
    database *after* a write, and holding a dict would pin the state that write
    was meant to change.
    """
    data = refetch()
    payload = build_board_payload(data, flash=pop_flash())
    totals = payload["totals"]

    # One compact row, not two. Every pixel of chrome is a pixel of board, and a
    # wall tablet is watched from across the room. It is rendered before the
    # component because the frame measures how much room the host left above it.
    left, right = st.columns([3, 1], gap="small", vertical_alignment="center")
    with left:
        st.markdown(
            '<div class="board-flag">'
            '<span class="board-flag__dot"></span>'
            "<b>Board</b> "
            f"<span>{totals['open_today']} open today · "
            f"{totals['overdue']} past due</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    with right:
        if st.button("Classic app", key="board_exit", use_container_width=True):
            toggle_board(False)
            st.rerun()

    # The payload went out above, before the action is read, because the value
    # the component returns belongs to the interaction that has already
    # happened. A write therefore repaints on the next run, one cycle later.
    action = render(payload, height=BOARD_HEIGHT_HINT)
    result = apply_action(data, action)

    # Only a real write needs a repaint. A refusal, or an action Streamlit
    # replayed, has nothing new to show, and rerunning for those would cost a
    # round trip and flash a message at somebody who did nothing wrong.
    if result and not result.get("noop"):
        st.session_state[FLASH_KEY] = {
            "message": result.get("message", ""),
            "ok": result.get("ok", False),
            "points": result.get("points"),
        }
        st.rerun()
