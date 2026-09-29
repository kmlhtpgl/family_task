"""The mode switch is three things that have to agree, and none are obvious.

A preference is stored per device, resolved into a mode, and painted on both the
app document and the Board frame. The Board owns the control; the app document
never has one and instead follows the shared key through the browser's `storage`
event. Each boundary is a place where the feature can half-work: the page goes
light while the Board stays dark, or "auto" means one thing in one document and
another in the other.

These tests pin the parts that would otherwise drift silently between files: the
two clocks, the shared key, and the shape of the one control that writes it. The
browser tools drive the whole path.
"""

import re
from pathlib import Path

import pytest

from utils import theme

REPO = Path(__file__).resolve().parent.parent
BOARD_JS = REPO / "static" / "board" / "board.js"
NAV_PY = REPO / "utils" / "nav.py"


# ── Auto is one rule, in two languages ───────────────────────────────────────


@pytest.mark.parametrize(
    "hour,expected",
    [
        (0, "night"),
        (6, "night"),
        (7, "day"),      # the boundary is inclusive at the start
        (12, "day"),
        (18, "day"),
        (19, "night"),   # and exclusive at the end
        (23, "night"),
    ],
)
def test_auto_is_daylight_between_the_two_hours(hour, expected):
    assert theme.resolve_mode("auto", hour) == expected


@pytest.mark.parametrize("preference", ["day", "night"])
def test_an_explicit_preference_ignores_the_clock(preference):
    for hour in range(24):
        assert theme.resolve_mode(preference, hour) == preference


def test_the_default_is_night():
    assert theme.DEFAULT_PREFERENCE == "night"
    assert theme.DEFAULT_PREFERENCE in theme.PREFERENCES
    assert set(theme.PREFERENCES) == {"day", "night", "auto"}


def test_the_board_resolves_auto_by_the_same_clock():
    """The Board cannot ask the app, so it carries a second copy of the rule.

    Two copies of "daylight" is exactly the kind of thing that drifts: one side
    gets a tasteful tweak, the other does not, and for two weeks a year the app
    is light while the wall behind it is dark. The Board's copy is an
    implementation detail only because there is this assertion.
    """
    js = BOARD_JS.read_text()
    key = re.search(r'var THEME_KEY = "([^"]+)"', js)
    day_from = re.search(r"var DAY_FROM = (\d+)", js)
    day_to = re.search(r"var DAY_TO = (\d+)", js)

    assert key and key.group(1) == theme.THEME_KEY
    assert day_from and int(day_from.group(1)) == theme.DAY_FROM_HOUR
    assert day_to and int(day_to.group(1)) == theme.DAY_TO_HOUR
    # Same fallback, for the same reason: it is what :root describes.
    assert '? stored' in js and '"night"' in js


# ── The app document paints itself, with no component in the loop ────────────


def test_the_app_paints_from_storage_before_it_is_told_anything():
    """Order is the whole trick: the script runs and paints on its own.

    Python cannot read localStorage, so there is no value for it to publish and
    nothing for the script to wait for. If it depended on a message, the page
    would open on the stylesheet default and swap once the message arrived -- a
    flash of night on a light screen, which is the thing the early paint exists
    to avoid.
    """
    source = theme._apply_source()
    assert "data-mode" in source
    assert theme.THEME_KEY in source
    assert "localStorage" in source
    assert "oklch" not in source, "it decides a mode, it does not decide a colour"


def test_the_app_follows_the_board_by_storage_event():
    """The two documents share one key, and the browser is the channel.

    The Board's control writing the key has to reach the app document without a
    reload, or changing the mode on the Board leaves the host chrome in the
    other lighting. The `storage` event is the browser's own notification and
    costs nothing.
    """
    source = theme._apply_source()
    assert '"storage"' in source
    assert "addEventListener" in source


def test_python_does_not_pretend_to_hold_the_preference():
    """The whole component bridge is gone, not left half-standing.

    It existed to feed a Streamlit control its value, and that control is on the
    Board now, written in JavaScript. A session key or a reporter frame left
    behind would be a second, stale source of truth for one setting.
    """
    for gone in ("render_switch", "_adopt", "current", "THEME_NODE_ID", "STATE_KEY"):
        assert not hasattr(theme, gone), f"theme.{gone} is dead weight"


# ── The control lives on the Board, and nowhere else ─────────────────────────


def test_the_board_owns_the_mode_control():
    js = BOARD_JS.read_text()
    assert "head__mode" in js, "the control was moved off the Board"
    assert "setPreference" in js
    assert "window.localStorage.setItem(THEME_KEY" in js, (
        "the Board draws a control that does not persist the choice"
    )


def test_the_control_offers_exactly_the_known_preferences():
    js = BOARD_JS.read_text()
    block = re.search(r"var THEME_OPTIONS = \[(.*?)\];", js, re.DOTALL)
    assert block, "no THEME_OPTIONS list in board.js"
    values = re.findall(r'\["([a-z]+)"', block.group(1))
    assert values == list(theme.PREFERENCES)


def test_the_nav_no_longer_carries_the_switch():
    """One control, on the Board. The nav is not a second place to set it."""
    source = NAV_PY.read_text()
    assert "render_switch" not in source
    assert "from utils import theme" not in source
