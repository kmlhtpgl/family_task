"""Day and night, and the one place either of them is decided.

There are three things to get right about a mode switch, and they are not the
same three things a colour switch usually worries about.

**Where the choice lives.** Per device, in the browser's localStorage, because
that is the only storage a Streamlit app can reach that belongs to the screen
rather than to the session or the account. A wall tablet in a bright kitchen and
a phone in bed want opposite modes, and a shared setting could not give them
that without one of them giving it up. It is localStorage rather than the
Supabase settings table the admin password uses, and the difference is the whole
reason: that table is a household fact, this is a fact about a screen.

**What "auto" means.** Daylight, from `DAY_FROM_HOUR` to `DAY_TO_HOUR`. The clock
is the only input that exists on every device without asking for anything, and
the boundary is a plain hour rather than a sunrise calculation because a location
lookup would be a permission prompt on a wall tablet in exchange for a
twenty-minute difference in when the board goes dark.

**How it reaches the pixels.** Both documents read the same localStorage key.
The app document and the Board frame are same-origin -- board.js already reads
`parent.document` for the payload -- so this is one value, not two that have to
be synchronised over a channel that can be interrupted. The browser's `storage`
event then keeps them in step for free, and a mode change never remounts the
Board, which would tear down the audio element the adhan plays through.

The one thing Python cannot do is read localStorage, so a tiny component frame
does exactly that and reports the stored preference back on its first render
(static/theme/index.html). That is what lets the control in the nav row show the
right answer on a page that was just opened on a device set to day, instead of
showing night while the screen behind it is white. The URL is not used for this:
Streamlit only reruns on a history change that alters the path or hash, so a
query-string-only edit is invisible to it and the control never catches up. The
component is a real channel and needs no reload.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# Shared with static/board/board.js. The Board resolves "auto" for itself rather
# than asking the app, because it is a separate document that has to boot and
# paint correctly before anything has been said to it. tests/test_theme.py pins
# the two copies to each other, which is the only reason duplicating two integers
# is safe here.
THEME_KEY = "family-task-theme"
THEME_NODE_ID = "theme-mode"
STATE_KEY = "theme_preference"
SEEN_KEY = "theme_reported_seen"
COMPONENT_KEY = "family-theme"

DAY_FROM_HOUR = 7
DAY_TO_HOUR = 19

PREFERENCES = ("day", "night", "auto")
DEFAULT_PREFERENCE = "night"
LABELS = {"day": "Day", "night": "Night", "auto": "Auto"}

# The bridge from the browser back to Python. See static/theme/index.html for the
# other half and the module docstring for why this exists at all.
THEME_DIR = Path(__file__).resolve().parent.parent / "static" / "theme"
_theme = components.declare_component("family_theme", path=str(THEME_DIR))


def resolve_mode(preference: str, hour: int | None = None) -> str:
    """Turn a preference into the mode that is actually painted.

    Always one of "day" or "night". "auto" is a preference, not a mode: it is
    resolved once, here, and nothing downstream should ever have to ask what
    "auto" means. The Board carries its own copy of this rule for the reason
    given on DAY_FROM_HOUR.
    """
    if preference in ("day", "night"):
        return preference
    if hour is None:
        hour = datetime.now().hour
    return "day" if DAY_FROM_HOUR <= hour < DAY_TO_HOUR else "night"


def current() -> str:
    """The preference for this session.

    The session is the authority, seeded from the browser once by `boot()` and
    never overwritten again. It cannot be re-read on every rerun, because for the
    moment a rerun takes the browser still holds the previous value, and obeying
    it would snap the control back and make the switch impossible to turn off.
    """
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = DEFAULT_PREFERENCE
    return st.session_state[STATE_KEY]


def _adopt(reported: str | None) -> None:
    """Take the browser's preference as ours, the first time we are told it.

    Called with the component's value, which lags a render: it is the preference
    the frame held when it was last looked at, and None until the frame has
    loaded once. Only a *change* is adopted. After the user presses the control,
    the frame catches up to Python and reports the same value back, which is then
    not a change and is ignored -- so a click is never undone by a stale report.
    """
    if reported not in PREFERENCES or reported == st.session_state.get(SEEN_KEY):
        return
    st.session_state[STATE_KEY] = reported
    st.session_state[SEEN_KEY] = reported


def render_switch() -> str:
    """The Day / Night / Auto control, in the nav row.

    Its own row rather than a tenth column in the grid. Nine columns already fill
    the width at 390px, so a tenth would leave a control too narrow to read or
    tap; and the grid is measured by tools/board_grid_check.py, which is right to
    be strict about it. Above the buttons, inside the same nav-scope container, it
    still belongs to the nav.

    No `default` is passed: the control takes its value from session_state, which
    `boot()` has already seeded, and passing both would be two sources of truth
    for one control.

    `required` so a tap on the option already lit does not clear the control.
    Without it a segmented_control deselects on a second tap and hands back None,
    which would drop the screen to the default: pressing Day while already on Day
    would darken the room.
    """
    current()  # make sure session_state holds a value before the control reads it
    choice = st.segmented_control(
        "Mode",
        options=list(PREFERENCES),
        format_func=lambda value: LABELS[value],
        key=STATE_KEY,
        required=True,
        label_visibility="collapsed",
    )
    if choice is None:
        # The control is cleared while the session resets. Night is the mode the
        # stylesheet's unscoped :root describes, so falling back to it leaves a
        # correct page rather than an unstyled one.
        choice = DEFAULT_PREFERENCE
        st.session_state[STATE_KEY] = choice
    return choice


def _publisher_html(preference: str) -> str:
    return (
        f'<div id="{THEME_NODE_ID}" data-preference="{preference}" '
        f'style="display:none"></div>'
    )


# Written as a plain template and substituted rather than an f-string. The braces
# are real JavaScript, and doubling every one of them by hand is how two of them
# end up unbalanced and the whole script becomes a syntax error. The same reason
# the kiosk watchdog is a template.
_APPLY_JS = """
(function () {
    var KEY = %(key)s;
    var NODE = %(node)s;
    var DAY_FROM = %(day_from)d;
    var DAY_TO = %(day_to)d;
    var DEFAULT = %(default)s;
    var PREFERENCES = %(preferences)s;

    function read() {
        try {
            var v = window.localStorage.getItem(KEY);
            return PREFERENCES.indexOf(v) === -1 ? DEFAULT : v;
        } catch (e) {
            /* Private browsing, or storage turned off: a screen that cannot
               remember a choice can still obey one. */
            return DEFAULT;
        }
    }

    function resolve(preference) {
        if (preference !== "auto") return preference;
        var hour = new Date().getHours();
        return hour >= DAY_FROM && hour < DAY_TO ? "day" : "night";
    }

    function paint(preference) {
        var next = resolve(preference);
        if (document.documentElement.getAttribute("data-mode") !== next) {
            document.documentElement.setAttribute("data-mode", next);
        }
    }

    function persist(preference) {
        try {
            window.localStorage.setItem(KEY, preference);
        } catch (e) { /* still applies for this page view */ }
    }

    /* Whether this is the first run of the script in this document. The flag is
       on the window, so it survives the reruns that replace the script element:
       only the load that actually first paints is "first". */
    var firstEver = !window.__familyThemeBooted;
    window.__familyThemeBooted = true;

    /* Painted from storage before anything else, so the earliest frame is
       already right. On a rerun this is harmless: the node below, which holds
       Python's answer, paints over it in the same turn. */
    paint(read());

    var last = null;

    function sync() {
        var node = document.getElementById(NODE);
        if (!node) return;
        var published = node.getAttribute("data-preference");
        if (PREFERENCES.indexOf(published) === -1) return;

        if (last === null) {
            last = published;
            /* On the very first load this node says the default, because Python
               has not heard from the component yet. The device's stored value is
               the truth here, not this -- the component reports it and Python
               will publish it on the next rerun. */
            if (firstEver && published !== read()) {
                paint(read());
                return;
            }
        } else if (published === last) {
            return;
        } else {
            last = published;
        }

        /* Everywhere else the node is authoritative: it is either the value the
           component reported from storage, or the option a person just pressed.
           Persisting it here is what keeps the Board and the next cold load in
           step without either of them asking Python. */
        persist(published);
        paint(published);
    }

    /* Observed on the body rather than on the node, because Streamlit replaces
       the node on every rerun and an observer bound to it would be left watching
       a detached element. Re-entrant for the same reason the kiosk watchdog is:
       a rerun produces a burst of mutations and only a real change does work. */
    if (window.MutationObserver && document.body) {
        new MutationObserver(sync).observe(document.body, {
            childList: true,
            subtree: true
        });
    } else {
        window.setInterval(sync, 1000);
    }

    /* Only "auto" needs this, and only at the two boundaries, but re-resolving
       every minute means a tablet left on a wall crosses into night within a
       minute of sunset without anyone touching it. */
    window.setInterval(function () {
        if (last === "auto") paint("auto");
    }, 60000);
})();
"""


def _apply_source() -> str:
    """The script with its constants substituted, ready to place on the page."""
    return _APPLY_JS % {
        "key": f'"{THEME_KEY}"',
        "node": f'"{THEME_NODE_ID}"',
        "day_from": DAY_FROM_HOUR,
        "day_to": DAY_TO_HOUR,
        "default": f'"{DEFAULT_PREFERENCE}"',
        "preferences": "[" + ", ".join(f'"{p}"' for p in PREFERENCES) + "]",
    }


def _apply_script() -> None:
    # Wrapped in <script> because st.html parses its argument as HTML. Handed a
    # bare IIFE it inserts the source as text and never runs it, which fails
    # silently: no error, no attribute, and the page simply stays in night.
    # unsafe_allow_javascript is what lets that tag execute at all.
    st.html(f"<script>{_apply_source()}</script>", unsafe_allow_javascript=True)


def boot() -> None:
    """Put the mode on the page. Once, on every page, including the Board.

    Mounted from app.py rather than from the nav, because the Board is the page
    that most needs it to be unconditional -- it is the one that is left running
    on a wall -- and the nav is not rendered until the shell has decided which
    page it is on.

    Order matters twice over. The reporter is consulted before the control is
    drawn, so a value it brings back is in the session by the time the control
    reads it; and the node and script come after, so the mode is painted on the
    same render without waiting for the component to load.
    """
    _adopt(_theme(preference=current(), default=None, key=COMPONENT_KEY, height=0))
    st.markdown(_publisher_html(current()), unsafe_allow_html=True)
    _apply_script()
