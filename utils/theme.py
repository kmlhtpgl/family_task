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
be synchronised over a channel that can be interrupted. Python is not in this
loop at all: it cannot read localStorage, and it does not need to, because this
script paints the attribute on load and then follows the key for the rest of the
session. The browser's `storage` event is what keeps the two documents in step,
and it costs nothing: the Board's control writes the key, the app document
receives the event, and both repaint. A mode change never remounts the Board,
which would tear down the audio element the adhan plays through.

The control itself lives on the Board (static/board/board.js) because the Board
is the page that is left running and the one anybody wants to dim. Because the
value is shared, a change made there reaches every other page's next paint for
free.
"""
from __future__ import annotations

from datetime import datetime

import streamlit as st

# Shared with static/board/board.js. The Board resolves "auto" for itself rather
# than asking the app, because it is a separate document that has to boot and
# paint correctly before anything has been said to it. tests/test_theme.py pins
# the two copies to each other, which is the only reason duplicating two integers
# is safe here.
THEME_KEY = "family-task-theme"

DAY_FROM_HOUR = 7
DAY_TO_HOUR = 19

PREFERENCES = ("day", "night", "auto")
DEFAULT_PREFERENCE = "night"


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


# Written as a plain template and substituted rather than an f-string. The braces
# are real JavaScript, and doubling every one of them by hand is how two of them
# end up unbalanced and the whole script becomes a syntax error. The same reason
# the kiosk watchdog is a template.
_APPLY_JS = """
(function () {
    var KEY = %(key)s;
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

    function apply() {
        var next = resolve(read());
        if (document.documentElement.getAttribute("data-mode") !== next) {
            document.documentElement.setAttribute("data-mode", next);
        }
    }

    /* Painted from storage before anything else, so the earliest frame is
       already right instead of flashing the stylesheet default. */
    apply();

    /* The Board's control is a separate document, so its write arrives here as
       a `storage` event rather than as a call. Following it is what makes one
       control on the Board reach the whole app. */
    if (window.addEventListener) {
        window.addEventListener("storage", function (event) {
            if (event.key === KEY || event.key === null) apply();
        });
    }

    /* Only "auto" needs this, and only at the two boundaries, but re-resolving
       every minute means a tablet left on a wall crosses into night within a
       minute of sunset without anyone touching it. */
    window.setInterval(function () {
        if (read() === "auto") apply();
    }, 60000);
})();
"""


def _apply_source() -> str:
    """The script with its constants substituted, ready to place on the page."""
    return _APPLY_JS % {
        "key": f'"{THEME_KEY}"',
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
    """Put the mode on the page, once, on every page including the Board.

    Mounted from app.py rather than from the nav, because the Board is the page
    that most needs it to be unconditional -- it is the one that is left running
    on a wall -- and the nav is not rendered until the shell has decided which
    page it is on.
    """
    _apply_script()
