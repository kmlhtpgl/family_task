"""The mode switch is three things that have to agree, and none are obvious.

A preference is stored per device, resolved into a mode, painted on the app
document and on the Board frame, and reported back to Python through a component.
Each boundary is a place where the feature can half-work: the page goes light
while the control stays on night, or the Board follows a mode the app does not,
or "auto" means one thing in one document and another in the other.

The browser tools drive the whole path. These tests pin the parts that would
otherwise drift silently between files: the two clocks, the shared key, and the
rule that decides when a report from the browser is allowed to change the
session.
"""

import re
from pathlib import Path

import pytest

from utils import theme

REPO = Path(__file__).resolve().parent.parent
BOARD_JS = REPO / "static" / "board" / "board.js"
THEME_HTML = REPO / "static" / "theme" / "index.html"


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


def test_the_component_directory_is_where_the_bridge_expects_it():
    """declare_component fails at import if the path has no index.html."""
    assert THEME_HTML.exists(), THEME_HTML
    assert THEME_HTML.parent == theme.THEME_DIR


def test_the_reporting_frame_speaks_the_component_protocol():
    """A frame that misses the handshake is loaded and never heard."""
    html = THEME_HTML.read_text()
    assert theme.THEME_KEY in html
    assert "streamlit:componentReady" in html
    assert "streamlit:setComponentValue" in html
    assert "streamlit:render" in html
    assert "data-mode" in html, "the frame has to be able to repaint the app document"


def test_the_app_paints_before_it_is_told_anything():
    """Order is the whole trick: the node and script run without the component.

    If the script depended on the component having loaded, the page would open
    on the stylesheet default and swap once the frame arrived -- a flash of night
    on a light screen, which is the thing the early paint exists to avoid.
    """
    source = theme._apply_source()
    assert "data-mode" in source
    assert theme.THEME_NODE_ID in source
    # It decides a mode, it does not decide a colour.
    assert "oklch" not in source


# ── Adopting a report without letting a stale one undo a press ────────────────


@pytest.fixture
def session(monkeypatch):
    state: dict = {}
    monkeypatch.setattr(theme.st, "session_state", state)
    return state


def test_a_reported_preference_becomes_the_session(session):
    theme._adopt("day")
    assert session[theme.STATE_KEY] == "day"
    assert session[theme.SEEN_KEY] == "day"


def test_nothing_reported_changes_nothing(session):
    theme._adopt(None)
    theme._adopt("banana")
    assert theme.STATE_KEY not in session


def test_a_repeat_report_is_ignored(session):
    """The frame echoes a press back, and that echo must not be re-adopted.

    The component's value lags a render, so after a press it briefly still holds
    the previous answer. Adopting only a *change* is what stops that stale value
    from flicking the screen back to where it was.
    """
    theme._adopt("day")
    session[theme.STATE_KEY] = "night"          # a press
    theme._adopt("day")                          # the lagging report arrives
    assert session[theme.STATE_KEY] == "night", "a stale report undid a press"


def test_a_new_report_after_a_press_is_taken(session):
    theme._adopt("day")
    session[theme.STATE_KEY] = "night"          # a press
    theme._adopt("night")                        # the frame catches up
    assert session[theme.STATE_KEY] == "night"
    assert session[theme.SEEN_KEY] == "night"


def test_current_falls_back_to_the_default(session):
    assert theme.current() == theme.DEFAULT_PREFERENCE


def test_current_keeps_the_session_value(session):
    session[theme.STATE_KEY] = "auto"
    assert theme.current() == "auto"


def test_the_control_cannot_be_cleared():
    """A second tap on the lit option must not empty the control.

    segmented_control deselects on a repeat tap unless required, and a cleared
    control would fall back to the default -- pressing Day while on Day would
    darken the room.
    """
    import inspect

    source = inspect.getsource(theme.render_switch)
    assert "required=True" in source
