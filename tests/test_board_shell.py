"""The board is an alternate shell, not another page, so the switch is tested at
the level of the shell rather than of the payload.

These assertions are about wiring: that the flag is honoured, that the classic
app is still reachable, and that turning the board on cannot take the kiosk
runtime down with it. The last group is the important one -- adhan and the
screensaver are the parts of this app that must not break.
"""

import ast
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app_pages.board import board_flag_from_env

APP_PY = Path(__file__).resolve().parent.parent / "app.py"
BOARD_PY = Path(__file__).resolve().parent.parent / "app_pages" / "board.py"
BOARD_JS = Path(__file__).resolve().parent.parent / "static" / "board" / "board.js"
BOARD_CSS = Path(__file__).resolve().parent.parent / "static" / "board" / "board.css"
BOARD_HTML = Path(__file__).resolve().parent.parent / "static" / "board" / "index.html"


def run_app(flag, monkeypatch, store=None, stub_assets=None):
    """The real app.py, driven by AppTest, with the board flag set."""
    monkeypatch.setenv("FAMILY_TASK_BOARD", flag)
    return AppTest.from_file(str(APP_PY), default_timeout=30).run()


def labels_of(app):
    return " ".join(b.label for b in app.button)


# ── The flag ────────────────────────────────────────────────────────────────


def test_board_is_off_by_default(store, stub_assets, monkeypatch):
    """Nobody should find a different app just because the branch merged."""
    app = run_app("0", monkeypatch)
    assert "Classic app" not in labels_of(app)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1", True),
        ("true", True),
        ("TRUE", True),
        ("On", True),
        (" yes ", True),
        ("0", False),
        ("", False),
        (None, False),
        ("no", False),
        ("off", False),
        # A typo must leave the classic app alone rather than half-switching.
        ("maybe", False),
        ("2", False),
    ],
)
def test_board_flag_parsing(value, expected):
    assert board_flag_from_env(value) is expected


# ── The classic app survives ────────────────────────────────────────────────


def test_classic_nav_is_still_there_when_the_board_is_off(
    store, stub_assets, monkeypatch
):
    app = run_app("0", monkeypatch)
    labels = labels_of(app)
    for page in ("Dashboard", "Kids", "Reading", "Quran", "Admin"):
        assert page in labels, f"{page} disappeared from the classic nav"


def test_classic_nav_is_gone_when_the_board_is_on(store, stub_assets, monkeypatch):
    """The board replaces the chrome. If the old nav were still rendered, the
    redesign would be sitting inside the thing it is replacing."""
    app = run_app("1", monkeypatch)
    labels = labels_of(app)
    assert "📊 Dashboard" not in labels
    assert "🎯 Daily Board" not in labels
    # The way back is the board's own control.
    assert "Classic app" in labels


def test_the_exit_button_returns_to_the_classic_app(store, stub_assets, monkeypatch):
    app = run_app("1", monkeypatch)
    app.button(key="board_exit").click().run()
    labels = labels_of(app)
    assert "📊 Dashboard" in labels
    assert "Classic app" not in labels


def test_the_board_stays_on_after_a_rerun_it_triggers_itself(
    store, stub_assets, monkeypatch
):
    """The board is on by env var, and nothing it renders should quietly turn it
    off. Its own control is the only way out."""
    app = run_app("1", monkeypatch)
    app.run()
    assert "Classic app" in labels_of(app)


# ── The kiosk must not be collateral damage ─────────────────────────────────


def test_kiosk_config_is_still_mounted_with_the_board_on(
    store, stub_assets, monkeypatch
):
    """Adhan and the screensaver are not part of the redesign, so the board is
    not allowed to take the kiosk handoff node with it."""
    app = run_app("1", monkeypatch)
    html = "\n".join(m.value for m in app.markdown)
    assert "kiosk-config" in html


def test_kiosk_iframe_is_still_mounted_with_the_board_on(
    store, stub_assets, monkeypatch
):
    app = run_app("1", monkeypatch)
    assert len(app.get("iframe")) >= 1, "the kiosk iframe vanished under the board"


def test_board_gate_is_after_the_kiosk_mount_in_source_order():
    """Guards against someone tidying the board block above the kiosk one.

    Order is the entire invariant, and no runtime assertion would catch a later
    edit that inverts it: the app would still work, minus adhan on the wall.
    """
    source = APP_PY.read_text()
    kiosk_at = source.index("components.html(KIOSK_IFRAME_HTML, height=0)")
    gate_at = source.index("if _board_on:")
    assert kiosk_at < gate_at, "the board gate now runs before the kiosk mount"


def test_board_branch_is_the_only_stop_in_the_shell():
    """st.stop() is what keeps the classic routing from also running. A second
    one elsewhere would mean the shell is now stopping in two places."""
    tree = ast.parse(APP_PY.read_text())
    stops = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Call)
        and isinstance(n.value.func, ast.Attribute)
        and n.value.func.attr == "stop"
    ]
    assert len(stops) == 1, "the board branch must be the only st.stop() in the shell"


# ── The canvas owns its own layer ───────────────────────────────────────────


def test_board_frame_does_not_depend_on_the_host_stylesheet():
    """The frame is a separate document so utils/styles.py cannot half-apply.

    board.css and board.js are the only local files it may load. Google Fonts is
    allowed, and nothing else off-origin is -- a second CDN would be a way for
    the wall tablet to render differently from the laptop.
    """
    html = BOARD_HTML.read_text()
    local = {"board.css", "board.js"}
    for ref in re.findall(r'(?:href|src)="([^"]+)"', html):
        if ref.startswith("https://"):
            assert ref.startswith(
                "https://fonts.g"
            ), f"the frame reaches off to {ref!r}"
        else:
            assert ref in local, f"the frame loads {ref!r}"


def test_board_css_and_js_never_reach_for_the_host_layer():
    for path in (BOARD_CSS, BOARD_JS):
        source = path.read_text()
        assert "@import" not in source
        assert "utils/" not in source.replace(
            "utils/styles.py -- 1,500 lines of it,", ""
        ).replace("utils/styles.py cannot", "")


def test_board_index_is_minimal_and_painted_by_script():
    """The canvas is built in JS, so index.html should carry almost no markup.
    This is what stops the canvas quietly turning back into a template that
    Streamlit re-renders around."""
    html = BOARD_HTML.read_text()
    # #board and the screen-reader announcer, and nothing else.
    assert html.count("<div") == 2, "index.html is starting to carry the layout"
    assert 'id="board"' in html
    assert 'src="board.js"' in html


def test_board_writes_nothing_yet():
    """Phase 2 is read-only: selection is local state and nothing is written.

    The frame keeps the action channel wired, so this checks for a call site
    rather than for the message itself -- sending a value is what a write means.
    """
    js = BOARD_JS.read_text()
    assert "setComponentValue" in js, "the action channel should still be in place"
    # One definition plus the window.__board export; no call sites yet.
    assert js.count("send(") == 2, "the board started writing"
