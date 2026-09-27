"""The Board, the app's landing page.

Renders full-bleed rather than inside the narrower page body, so the whole
tablet is board. Navigation is the shared row from utils.nav rather than a
board-local door: the board used to hide the row and offer one "Classic app"
button, which read as the app having lost its other features.

What stays is what must not be disturbed: the kiosk iframe and its
#kiosk-config handoff are mounted by app.py above this, and they are
load-bearing for adhan and the screensaver. This page adds no iframe of its
own beyond the board component, and never touches the kiosk ones.
"""

import os

import streamlit as st

from utils.board.actions import apply_action
from utils.board.bridge import render
from utils.board.payload import build_board_payload
from utils.nav import render_nav

# The board fills whatever the host viewport has left, and static/board/board.js
# measures that space through the same-origin host before reporting its own frame
# height. These are only a starting hint for the first paint. It sits below the
# flag and nav rows, which cost about 90px of the host's height.
BOARD_HEIGHT_HINT = 690

# Where the app lands when the board is explicitly stood down with
# FAMILY_TASK_CLASSIC. The other pages live here too, and the shared nav row
# brings you straight back to the board.
CLASSIC_LANDING = "parents"


TRUTHY = {"1", "true", "on", "yes"}


def flag_from_env(value: str | None) -> bool:
    """Whether an env value asks for something. Split out from `board_enabled`
    so the parsing is testable without a Streamlit session behind it."""
    return (value or "").strip().lower() in TRUTHY


def board_enabled() -> bool:
    """Whether the app should land on the board.

    This is only the landing choice now. The board used to be a shell that
    stood the rest of the app down, and it carried a session flag to remember
    which shell you were in; routing on the page alone removed the need for
    that flag, and with it the way the nav could highlight one page while
    another rendered.

    FAMILY_TASK_CLASSIC stands the board down so the app opens on the parents
    page instead, which is how the audit and screenshot tools reach the
    remaining pages.
    """
    return not flag_from_env(os.environ.get("FAMILY_TASK_CLASSIC"))


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

    # Two compact rows, not three, and both rendered before the component
    # because the frame measures how much room the host left above it. The flag
    # is the board's identity and the nav row is how you reach the rest of the
    # app; every pixel of chrome is a pixel of board, and a wall tablet is
    # watched from across the room.
    st.markdown(
        '<div class="board-flag">'
        '<span class="board-flag__dot"></span>'
        "<b>Board</b> "
        f"<span>{totals['open_today']} open today · "
        f"{totals['overdue']} past due</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    render_nav("board")

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
