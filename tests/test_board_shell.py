"""The board is the landing page and shares one navigation row with every other
page, so the switch is tested at the level of the app's wiring.

These assertions are about wiring: that the board is what you land on, that
every feature is one tap away from it, that the nav can get you back to the
board again, and that the board cannot take the kiosk runtime down with it. The
last group is the important one -- adhan and the screensaver are the parts of
this app that must not break.
"""

import ast
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app_pages.board import CLASSIC_LANDING, flag_from_env

APP_PY = Path(__file__).resolve().parent.parent / "app.py"
BOARD_PY = Path(__file__).resolve().parent.parent / "app_pages" / "board.py"
BOARD_JS = Path(__file__).resolve().parent.parent / "static" / "board" / "board.js"
BOARD_CSS = Path(__file__).resolve().parent.parent / "static" / "board" / "board.css"
BOARD_HTML = Path(__file__).resolve().parent.parent / "static" / "board" / "index.html"


def run_app(stand_down, monkeypatch, store=None, stub_assets=None):
    """The real app.py, driven by AppTest, with the board-landing flag set."""
    monkeypatch.setenv("FAMILY_TASK_CLASSIC", stand_down)
    return AppTest.from_file(str(APP_PY), default_timeout=30).run()


def labels_of(app):
    return " ".join(b.label for b in app.button)


# ── The flag ────────────────────────────────────────────────────────────────


def test_board_is_what_you_land_on_by_default(store, stub_assets, monkeypatch):
    """The board is the app. A flag that has to be set to reach the main surface
    is a flag that gets left off, which is how this screen spent a whole commit
    being invisible."""
    app = run_app("0", monkeypatch)
    html = "\n".join(m.value for m in app.markdown)
    assert 'id="board-data"' in html, "the board is not what you land on"
    assert app.session_state.page == "board"


def test_the_board_offers_every_feature_as_one_tap(store, stub_assets, monkeypatch):
    """The reason this change exists.

    The board used to hide the nav and offer a single "Classic app" button, which
    from across a room read as the new UI having lost Reading, Quran, Prayer and
    the rest. Every destination has to be named on the board itself.
    """
    app = run_app("0", monkeypatch)
    labels = labels_of(app)
    for page in ("Parents", "Kids", "Reading", "Quran", "Prayer", "Rewards", "Meeting", "Admin"):
        assert page in labels, f"{page} is not reachable from the board"
    assert "Classic app" not in labels, "the board still has a separate door to the rest of the app"


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
        # A typo must leave the board standing rather than half-switching.
        ("maybe", False),
        ("2", False),
    ],
)
def test_board_stand_down_flag_parsing(value, expected):
    assert flag_from_env(value) is expected


# ── The other pages are still reachable ────────────────────────────────────


def test_every_page_is_reachable_when_the_board_is_stood_down(
    store, stub_assets, monkeypatch
):
    app = run_app("1", monkeypatch)
    labels = labels_of(app)
    for page in ("Kids", "Parents", "Reading", "Quran", "Prayer", "Rewards", "Admin"):
        assert page in labels, f"{page} disappeared from the nav"


def test_the_retired_pages_are_gone_from_every_nav(store, stub_assets, monkeypatch):
    """The Daily Board duplicated the new one, and the old dashboard's week grid
    became the board's lanes. Neither is reachable any more, from anywhere."""
    for flag in ("0", "1"):
        labels = labels_of(run_app(flag, monkeypatch))
        assert "Daily Board" not in labels
        assert "Dashboard" not in labels


def test_the_board_and_the_other_pages_share_one_nav_row(store, stub_assets, monkeypatch):
    """One row, rendered in both places, each destination named exactly once.

    The board used to hide the row entirely and hand out a button instead. The
    row also has to stay singular: two copies on screen would mean the board is
    sitting inside the chrome it replaced.
    """
    for flag in ("0", "1"):
        labels = [b.label for b in run_app(flag, monkeypatch).button]
        for page in ("Board", "Parents", "Kids", "Reading", "Quran", "Prayer", "Rewards", "Meeting", "Admin"):
            count = sum(1 for label in labels if label.endswith(page))
            assert count == 1, f"{page} appears {count} times in the nav with flag={flag}"


def test_the_nav_row_has_exactly_one_implementation(store, stub_assets, monkeypatch):
    """Both halves call the shared renderer, so they cannot drift apart.

    A second hand-rolled copy of the row is how the board ended up hiding the nav
    in the first place.
    """
    from utils.nav import PAGES

    for path in (APP_PY, BOARD_PY):
        source = path.read_text()
        assert "render_nav(" in source, f"{path.name} does not use the shared nav row"
        for _, _, label in PAGES:
            assert f'"{label}"' not in source, f"{path.name} hard-codes its own nav entry {label!r}"


def test_a_nav_click_on_the_board_leaves_the_board(store, stub_assets, monkeypatch):
    app = run_app("0", monkeypatch)
    app.button(key="nav_reading").click().run()
    html = "\n".join(m.value for m in app.markdown)
    assert app.session_state.page == "reading"
    assert 'id="board-data"' not in html, "the board stayed on under another page"


def test_the_nav_row_gets_you_back_to_the_board(store, stub_assets, monkeypatch):
    """Regression: the row used to highlight Board while another page rendered.

    The nav set only `page`, and a separate shell flag decided what was actually
    drawn, so leaving the board and clicking Board again landed on the parents
    page with the nav claiming otherwise.
    """
    app = run_app("0", monkeypatch)
    app.button(key="nav_reading").click().run()
    app.button(key="nav_board").click().run()
    html = "\n".join(m.value for m in app.markdown)
    assert app.session_state.page == "board"
    assert 'id="board-data"' in html, "the board did not come back from the nav row"


def test_the_board_stays_on_after_a_rerun_it_triggers_itself(
    store, stub_assets, monkeypatch
):
    """A tick makes the board rerun itself, and that rerun must not quietly dump
    the wall tablet onto another page mid-write."""
    app = run_app("0", monkeypatch)
    app.run()
    html = "\n".join(m.value for m in app.markdown)
    assert 'id="board-data"' in html, "a rerun lost the board"


# ── The kiosk must not be collateral damage ─────────────────────────────────


def test_kiosk_config_is_still_mounted_with_the_board_on(
    store, stub_assets, monkeypatch
):
    """Adhan and the screensaver are not part of the redesign, so the board is
    not allowed to take the kiosk handoff node with it."""
    app = run_app("0", monkeypatch)
    html = "\n".join(m.value for m in app.markdown)
    assert "kiosk-config" in html


def test_kiosk_iframe_is_still_mounted_with_the_board_on(
    store, stub_assets, monkeypatch
):
    app = run_app("0", monkeypatch)
    assert len(app.get("iframe")) >= 1, "the kiosk iframe vanished under the board"


def test_board_gate_is_after_the_kiosk_mount_in_source_order():
    """Guards against someone tidying the board block above the kiosk one.

    Order is the entire invariant, and no runtime assertion would catch a later
    edit that inverts it: the app would still work, minus adhan on the wall.
    """
    source = APP_PY.read_text()
    kiosk_at = source.index("components.html(KIOSK_IFRAME_HTML, height=0)")
    gate_at = source.index("if _on_board:")
    assert kiosk_at < gate_at, "the board gate now runs before the kiosk mount"


def test_board_branch_is_the_only_stop_in_the_shell():
    """st.stop() is what keeps the other pages' routing from also running. A
    second one elsewhere would mean the app is now stopping in two places."""
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


def test_the_canvas_asks_rather_than_writes():
    """The frame's only way to change anything is the action channel.

    There is no database in the browser, and a tick is a question sent to Python
    rather than a fact asserted here. If a second channel ever appears -- a
    fetch, a form post, an optimistic local write -- this is what catches it.
    """
    js = BOARD_JS.read_text()
    assert "fetch(" not in js, "the canvas is talking to something other than the host"
    assert "XMLHttpRequest" not in js
    assert "localStorage" not in js
    # The two verbs the payload is allowed to ask for, and nothing else.
    verbs = set(re.findall(r'send\(\s*"([a-z]+)"', js))
    assert not verbs, f"hard-coded verbs in the canvas: {verbs}"


def test_rows_do_not_tick_themselves():
    """No optimistic update.

    The server decides whether a task may be completed, so a row that filled its
    own box would be claiming a result Python has not agreed to yet, and would
    have to take it back when the answer is no.
    """
    js = BOARD_JS.read_text()
    assert "task--done" not in js, "a row is marking itself done"


def test_every_css_variable_used_is_defined():
    """A var() naming a colour that does not exist resolves to nothing.

    The failure is invisible in review and invisible in a screenshot taken by
    someone who cannot see it: `border: 2px solid var(--nope)` is not a red
    border, it is no border at all, and the element quietly loses its outline.
    """
    css = BOARD_CSS.read_text()
    defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", css))
    used = set(re.findall(r"var\((--[a-z0-9-]+)", css))
    # Set from JavaScript on the element itself, so it cannot appear in :root.
    set_by_js = {"--person-accent"}
    missing = used - defined - set_by_js
    assert not missing, f"undefined CSS variables: {sorted(missing)}"


def test_js_only_sets_variables_the_stylesheet_uses():
    """The other half of the same contract, in the other direction."""
    js = BOARD_JS.read_text()
    css = BOARD_CSS.read_text()
    for name in set(re.findall(r"setProperty\(\"(--[a-z0-9-]+)\"", js)):
        assert f"var({name}" in css, f"{name} is set from JS but never used"
