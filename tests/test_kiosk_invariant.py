"""The adhan runtime must survive the rewrite.

`static/kiosk/kiosk.js` plays the adhan, runs the screensaver and holds the
screen awake on a wall-mounted tablet. It is loaded through an iframe whose
HTML string is deliberately constant: if that string changes on any rerun,
Streamlit tears the frame down and takes the audio element with it, and adhan
stops playing silently.

The mechanism is documented in app.py and utils/kiosk_helpers.py, but nothing
enforced it. These tests do. If one of these fails, the rewrite has broken
adhan and that is the first thing to fix.
"""

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_PY = REPO_ROOT / "app.py"
STYLES_PY = REPO_ROOT / "utils" / "styles.py"
KIOSK_JS = REPO_ROOT / "static" / "kiosk" / "kiosk.js"
KIOSK_HELPERS = REPO_ROOT / "utils" / "kiosk_helpers.py"

# The exact string app.py must keep passing to components.html(). kiosk.js is
# fetched from /app/static, which Streamlit serves because
# enableStaticServing = true in .streamlit/config.toml.
EXPECTED_IFRAME_HTML = '<script src="/app/static/kiosk/kiosk.js"></script>'

# The kiosk overlay stack, from lowest to highest. The app's own chrome sits
# below all of these; the adhan overlay has to sit above the app, and the
# diagnostics panel above the adhan. Reordering these silently breaks the
# overlay, so the exact values are pinned.
KIOSK_Z_INDEX = {
    ".kiosk-unlock-hint": 99998,
    ".kiosk-screensaver": 99999,
    ".kiosk-screensaver-footer": 100000,
    ".kiosk-audio-status": 100001,
    ".kiosk-diagnostics": 100003,
}


def app_tree():
    return ast.parse(APP_PY.read_text())


def test_iframe_html_constant_is_exactly_as_documented():
    from utils.kiosk_helpers import KIOSK_IFRAME_HTML

    assert KIOSK_IFRAME_HTML == EXPECTED_IFRAME_HTML


def test_app_passes_the_constant_not_a_string():
    """The invariant, enforced structurally.

    Interpolating anything into the iframe HTML -- an f-string, a concatenation,
    a formatted call -- makes the string vary per rerun and kills adhan. So this
    asserts on the shape of the argument node, not merely on its value.
    """
    calls = [
        node
        for node in ast.walk(app_tree())
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "html"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "components"
    ]
    assert calls, "app.py no longer renders the kiosk iframe through components.html"

    for call in calls:
        assert call.args, "components.html called with no html argument"
        first = call.args[0]
        assert isinstance(first, ast.Name), (
            "the kiosk iframe argument must be the bare KIOSK_IFRAME_HTML name, "
            f"but it is {type(first).__name__}. Interpolation here changes the "
            "iframe string on every rerun and stops adhan from playing."
        )
        assert first.id == "KIOSK_IFRAME_HTML"


def test_kiosk_config_travels_in_a_hidden_node_not_the_iframe():
    """Bootstrap JSON must reach kiosk.js through #kiosk-config.

    Checked on the tree rather than the source text, so an import statement
    mentioning the function cannot trip it.
    """
    tree = app_tree()
    source = APP_PY.read_text()

    assert "kiosk-config" in source, "the #kiosk-config handoff node is gone"

    bootstrap_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "get_kiosk_bootstrap"
    ]
    assert bootstrap_calls, "app.py no longer builds the kiosk bootstrap payload"

    # The payload is rendered into the DOM by st.markdown, and that rendered
    # markup is the only place it may appear.
    markdown_args = [
        arg
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "markdown"
        for arg in node.args
    ]
    assert markdown_args, "app.py no longer renders the #kiosk-config node"

    html_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "html"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "components"
    ]
    for call in html_calls:
        for arg in call.args:
            assert not (
                isinstance(arg, ast.Call)
                and isinstance(arg.func, ast.Name)
                and arg.func.id == "get_kiosk_bootstrap"
            ), "bootstrap config must not be passed into the iframe"

    # And the node that carries it must be hidden, since kiosk.js reads it.
    assert re.search(r'id="kiosk-config"[^>]*display:\s*none', source) or re.search(
        r'style="display:\s*none"[^>]*id="kiosk-config"', source
    ), "the #kiosk-config node must be hidden; kiosk.js parses it as text"


def test_kiosk_js_reads_config_from_the_hidden_node():
    source = KIOSK_JS.read_text()
    assert "kiosk-config" in source, (
        "kiosk.js no longer looks for #kiosk-config; the Python handoff is broken"
    )


def test_kiosk_z_index_stack_is_unchanged():
    """The overlay ordering is load-bearing and is pinned value by value."""
    css = STYLES_PY.read_text()
    block = css[css.index('_KIOSK_CSS = """') : css.index('_RESPONSIVE_CSS = """')]

    found = {
        selector: int(value)
        for selector, value in re.findall(
            r"([.#][\w\-]+)\s*\{[^}]*?z-index:\s*(\d+)", block, re.S
        )
    }

    assert found == KIOSK_Z_INDEX, (
        "the kiosk overlay z-index stack changed. Adhan draws above the app and "
        "diagnostics above adhan; reordering or renumbering these will either "
        "bury the adhan banner under the UI or put the app on top of it."
    )


def test_app_chrome_sits_below_the_kiosk_overlay():
    """Nothing in the app's own styles may reach into the kiosk z-index range."""
    css = STYLES_PY.read_text()
    app_block = css[css.index('_BASE_CSS = """') : css.index('_KIOSK_CSS = """')]

    offenders = [
        int(v)
        for v in re.findall(r"z-index:\s*(\d+)", app_block)
        if int(v) >= 99998
    ]
    assert not offenders, (
        f"app chrome uses z-index {offenders}, which collides with the kiosk "
        "overlay stack"
    )


@pytest.mark.parametrize(
    "asset",
    [
        "static/kiosk/kiosk.js",
        "static/adhan/fajr.mp3",
        "static/adhan/dhuhr.mp3",
        "static/adhan/asr.mp3",
        "static/adhan/maghrib.mp3",
        "static/adhan/isha.mp3",
    ],
)
def test_kiosk_assets_exist(asset):
    path = REPO_ROOT / asset
    assert path.is_file(), f"{asset} is missing; adhan or the screensaver cannot load it"
    assert path.stat().st_size > 0, f"{asset} is empty"


def test_screensaver_has_backgrounds():
    backgrounds = list((REPO_ROOT / "static" / "backgrounds").glob("*.jpeg")) + list(
        (REPO_ROOT / "static" / "backgrounds").glob("*.jpg")
    )
    assert len(backgrounds) >= 10, (
        f"only {len(backgrounds)} screensaver backgrounds; the kiosk screensaver "
        "cycles through these"
    )


def test_static_serving_is_enabled():
    """kiosk.js is fetched from /app/static, which needs this flag."""
    config = (REPO_ROOT / ".streamlit" / "config.toml").read_text()
    assert "enableStaticServing = true" in config, (
        "enableStaticServing must stay on or kiosk.js 404s and adhan never arms"
    )


def test_a_preview_cannot_be_dismissed_by_activity():
    """The Admin preview must survive the pointer, or the button looks broken.

    The idle screensaver is meant for a wall display nobody touches and is
    dismissed by the first mousemove, scroll or click. Reusing that behaviour
    for the test is what made "Preview screensaver" flash for about a second
    and vanish: the tester's cursor is live and Streamlit fires scroll events
    while the page settles. activity() must therefore bail out while a preview
    is up, and only the overlay's own tap may close it.
    """
    source = KIOSK_JS.read_text()

    activity = source[source.index("function activity()") :]
    activity = activity[: activity.index("\n    }")]
    assert "ssPreview" in activity, (
        "activity() no longer checks ssPreview, so the Admin preview is "
        "dismissed by ordinary mouse movement and reads as a dead button"
    )
    assert "hideScreensaver" in activity, (
        "activity() should still dismiss the IDLE screensaver, which is correct "
        "for a wall display; only previews are exempt"
    )


def test_preview_mode_is_reachable_from_the_admin_controls():
    """The Admin controls must dispatch straight to the runtime.

    They are plain elements carrying data-kiosk-action, not st.button. An
    st.button has to rerun the script and hand the request over as a one-shot
    flag in #kiosk-config for the 500ms poll to find, and that hand-off fails
    silently on a deployed browser.
    """
    admin = (REPO_ROOT / "app_pages" / "admin.py").read_text()
    assert 'data-kiosk-action="preview"' in admin, (
        "the Admin Kiosk tab no longer offers a preview control the runtime "
        "can act on"
    )
    assert 'data-kiosk-action="adhan"' in admin, (
        "the Admin Kiosk tab no longer offers an adhan test control"
    )
    assert "kiosk_preview_button" not in admin, (
        "the preview control went back to st.button + st.rerun, which is the "
        "hand-off that silently fails on the deployed app"
    )

    source = KIOSK_JS.read_text()
    handler = source[source.index("function handleKioskControl") :]
    handler = handler[: handler.index("\n    }")]
    assert "'preview'" in handler, "the runtime does not dispatch the preview action"
    assert "showScreensaver({ preview: true })" in handler, (
        "the preview control must open preview mode, or it inherits the idle "
        "auto-dismiss and vanishes immediately"
    )


def test_prime_never_interrupts_a_playing_adhan():
    """prime() must stand down while an adhan is live.

    The controls dispatch from a capture-phase listener, so prime() runs on the
    very same tap that started the adhan. If it does not stand down it pauses
    the element and strips its source 90ms later, and the test reports nothing
    at all.
    """
    source = KIOSK_JS.read_text()
    prime = source[source.index("function prime()") :]
    prime = prime[: prime.index("\n    }")]
    assert "K.playing" in prime, "prime() will clobber a live adhan on the same tap"

    play = source[source.index("function playAdhan") :]
    play = play[: play.index("\n    }")]
    assert "K.playing = true" in play, (
        "playAdhan must latch K.playing before a.el.play(), otherwise the flag "
        "is not set in time to protect the playback"
    )


def test_the_admin_status_strip_is_present_and_filled():
    """The runtime must report its own state on the page.

    A control that silently does nothing is indistinguishable from a broken
    one, and a wall tablet has no console to read. Both the markup and the
    runtime side are pinned so the strip cannot quietly stop updating.
    """
    admin = (REPO_ROOT / "app_pages" / "admin.py").read_text()
    assert 'id="kiosk-status"' in admin, "the Kiosk tab no longer renders a status strip"

    source = KIOSK_JS.read_text()
    assert "function renderStatus()" in source, "the runtime no longer reports status"
    for part in ("runtime", "assets", "state"):
        assert f"'{part}'" in source, f"the status strip never fills the {part} chip"
