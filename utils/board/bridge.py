"""The JS <-> Python channel for the Board.

The Board renders inside a declared component rather than through Streamlit's
own widgets, because that is the only way to own the visual layer outright.

Why the payload does not travel as a component argument
-------------------------------------------------------
A declared component's widget id is computed from its JSON args
(`CustomComponent.create_instance` -> `compute_and_register_element_id(...,
json_args=serialized_json_args)`). A component whose args carry the payload
therefore gets a *new identity on every rerun*, and the value the browser set
on the previous identity is discarded -- the action channel silently delivers
None forever. This was measured, not assumed; tools/spike_check.py is the
regression test for it.

So the two directions use two different channels:

    Python -> JS   the payload, as JSON in a hidden #board-data node in the
                   host document, exactly as the kiosk runtime already receives
                   its config through #kiosk-config. The frame watches that node
                   with a MutationObserver, so new data paints as soon as it
                   lands rather than waiting for a component render cycle.

    JS -> Python   {"verb": ..., "seq": n}, returned as the component's value.
                   This only works because the component's own args are
                   constant, which keeps its widget id stable.

`seq` is monotonic per frame. Streamlit keeps a widget's value until it
changes, so the action that triggered a rerun is still there on the next one;
comparing `seq` against the last handled value is what makes each action land
exactly once. See utils/board/actions.py.
"""

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

BOARD_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "board"

_board = components.declare_component("family_board", path=str(BOARD_DIR))

# Constant across every render, on purpose. See the module docstring.
_ARGS = {"channel": "board", "version": 1}

DATA_NODE_ID = "board-data"
HANDLED_SEQ_KEY = "board_handled_seq"


def render(payload: dict, height: int = 900) -> dict | None:
    """Publish the payload, render the frame, and return the pending action.

    Order matters: the node has to exist in the host document before the frame
    is told to paint, so it is written first. The returned action belongs to the
    *previous* interaction, which is the only value available at this point.
    """
    st.markdown(
        f'<div id="{DATA_NODE_ID}" style="display:none">'
        f"{json.dumps(payload, separators=(',', ':'), default=str)}"
        f"</div>",
        unsafe_allow_html=True,
    )
    return _board(payload=_ARGS, default=None, key="family-board", height=height)


def is_new(action: dict | None) -> bool:
    """True when `action` has not been handled yet."""
    if not isinstance(action, dict) or "verb" not in action:
        return False
    seq = action.get("seq")
    if not isinstance(seq, int):
        return False
    return seq > st.session_state.get(HANDLED_SEQ_KEY, 0)


def mark_handled(action: dict) -> None:
    st.session_state[HANDLED_SEQ_KEY] = action["seq"]
