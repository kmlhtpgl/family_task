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

from app_pages.board import CLASSIC_LANDING, flag_from_env, within_picker

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


# ── The day picker ──────────────────────────────────────────────────────────


def test_the_picker_reaches_every_day_the_strip_offers():
    """A tap on a visible day has to be accepted.

    The strip grew to seven days while this bound stayed at one either side, so
    the canvas sent a day and the page silently dropped it and repainted today:
    the tap looked like it did nothing, which is how the wider strip stayed
    unreachable however inviting it looked.
    """
    from datetime import date, timedelta

    from utils.board.payload import DISPLAY_ARC_FUTURE, DISPLAY_ARC_PAST

    today = date(2026, 9, 28)
    for offset in range(-DISPLAY_ARC_PAST, DISPLAY_ARC_FUTURE + 1):
        day = today + timedelta(days=offset)
        assert within_picker(day, today), offset
    assert not within_picker(today + timedelta(days=DISPLAY_ARC_FUTURE + 1), today)
    assert not within_picker(today - timedelta(days=DISPLAY_ARC_PAST + 1), today)


def test_the_strip_and_the_picker_bound_are_the_same_window():
    """A day rendered as tappable and rejected on arrival is a broken board."""
    from datetime import date

    from utils.board.payload import (
        DISPLAY_ARC_FUTURE,
        DISPLAY_ARC_PAST,
        build_board_payload,
    )
    from tests.fixtures import sample_data

    arc = build_board_payload(sample_data(), on_date=date.today())["arc"]
    assert len(arc) == DISPLAY_ARC_PAST + DISPLAY_ARC_FUTURE + 1
    assert all(within_picker(date.fromisoformat(d["date"]), date.today()) for d in arc)


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
    """Neither file may depend on the host's stylesheet.

    Comments are stripped before checking, because a comment cannot be a
    dependency. This started as a list of two allowed phrases -- the header
    comments in both files talk about utils/styles.py by name, and the test
    failed every time either file was reworded. Pinning prose meant the next
    person to explain themselves in a comment had to edit a test, which is how a
    guard like this quietly gets switched off. The dependency is in the code.
    """
    for path in (BOARD_CSS, BOARD_JS):
        source = path.read_text()
        source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
        source = re.sub(r"^\s*//.*$", "", source, flags=re.MULTILINE)
        assert "@import" not in source
        assert "utils/" not in source


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

    localStorage is now allowed, for exactly one thing, and the shape of the
    allowance matters more than the fact of it. The display mode is a per-device
    preference with no server state behind it, and the frame and the app document
    have to agree on it or the app is white around a night Board. The frame
    therefore only ever *reads* it: it holds no copy of anything the server owns,
    it takes the mode from the key the app writes, and it follows changes through
    the browser's own `storage` event. So the write verbs are still banned
    outright, and the one read is pinned to the key utils/theme.py owns.
    """
    js = BOARD_JS.read_text()
    assert "fetch(" not in js, "the canvas is talking to something other than the host"
    assert "XMLHttpRequest" not in js
    for verb in ("setItem", "removeItem", "clear"):
        assert f"localStorage.{verb}" not in js, (
            f"the canvas is writing to localStorage ({verb}); it holds no state of its own"
        )

    from utils import theme

    keys = set(re.findall(r'localStorage\.getItem\(\s*([A-Za-z_$][\w$]*)', js))
    assert keys == {"THEME_KEY"}, (
        f"the canvas reads localStorage keys {sorted(keys)}; it should read only the "
        f"mode key, and get it from utils/theme.py rather than hard-coding the string"
    )
    # And the key it reads is the one the app writes.
    assert f'var THEME_KEY = "{theme.THEME_KEY}"' in js, (
        "board.js's key is not utils/theme.THEME_KEY; the frame and the app would "
        "read different keys and the Board would not follow the mode"
    )
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


def test_js_only_reads_variables_the_stylesheet_defines():
    """And the third direction: a var() the JS composes has to exist too.

    setPersonAccent builds `oklch(calc(var(--person-lightness) + ...) ...)` as a
    string and hands it to the browser, so the variable it depends on never
    appears in the stylesheet next to the property it sets. If that name is ever
    typo'd or the token is renamed, the person accents resolve to nothing -- the
    browser drops the declaration and the lanes lose their colours, silently,
    in a file no CSS parser in this suite reads.
    """
    js = BOARD_JS.read_text()
    css = BOARD_CSS.read_text()
    defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", css))
    used = set(re.findall(r"var\((--[a-z0-9-]+)", js))
    missing = used - defined
    assert not missing, f"JS reads CSS variables that are not defined: {sorted(missing)}"
