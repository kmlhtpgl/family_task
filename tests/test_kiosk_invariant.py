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

# kiosk.js is fetched from /app/static, which Streamlit serves because
# enableStaticServing = true in .streamlit/config.toml. The URL carries a
# ?v= cache-buster; KIOSK_RUNTIME_PATH pins the part that must not move.
KIOSK_RUNTIME_PATH = "/app/static/kiosk/kiosk.js"

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


def test_iframe_html_inlines_the_runtime_and_is_stable():
    """The runtime must be INLINED, and the HTML must not vary per rerun.

    The inlining is the whole point. Referencing the runtime as a separate
    /app/static request meant the entire feature hinged on that one request
    succeeding: behind a login, behind nosniff, behind deployment headers. When
    it failed the runtime simply never ran, every control went inert, and the
    status strip stayed on the "connecting..." that Python renders -- so the
    app looked healthy while the feature was absent.

    The stability half still matters: if this string varies per rerun, Streamlit
    recreates the frame and the audio element dies with it. The runtime only
    changes on deploy, so within a deploy this stays byte-identical.
    """
    from utils.kiosk_helpers import KIOSK_IFRAME_HTML

    assert KIOSK_RUNTIME_PATH not in KIOSK_IFRAME_HTML, (
        "the kiosk runtime is being fetched from /app/static again; a separate "
        "request is what made the whole feature fail silently in deployment"
    )
    assert "<script src=" not in KIOSK_IFRAME_HTML, (
        "the kiosk iframe must not depend on any externally loaded script"
    )

    # The runtime's own source must actually be inlined, verbatim.
    assert KIOSK_JS.read_text(encoding="utf-8") in KIOSK_IFRAME_HTML, (
        "the runtime body is not inlined into the iframe; the version marker and "
        "the watchdog are no substitutes for the code that draws the screensaver"
    )

    # A literal </script> inside the inlined source would close the tag early
    # and leave the rest of the runtime as page text. The runtime must therefore
    # survive intact inside ONE block.
    blocks = re.findall(r"<script>(.*?)</script>", KIOSK_IFRAME_HTML, re.S)
    assert KIOSK_JS.read_text(encoding="utf-8") in blocks, (
        "the inlined runtime is not intact inside a single <script> block, so a "
        "</script> in the source is truncating it"
    )

    # Import it a second time: recomputing must yield the same string, so a
    # rerun reuses the iframe instead of tearing it down.
    from utils.kiosk_helpers import KIOSK_IFRAME_HTML as again

    assert again == KIOSK_IFRAME_HTML, "the iframe HTML is not stable across imports"


def test_runtime_failure_is_reported_on_the_page():
    """A dead runtime must say so, in the page, without a console.

    The runtime is the only code that can report success, so when it dies
    nothing is left to distinguish "still loading" from "broken" -- which is
    exactly how this stayed hidden. Two independent tripwires are required:

      * a marker armed before the runtime runs and disarmed only by a separate
        script that runs even when the runtime throws, and
      * a watchdog outside the runtime that rewrites the status strip.

    Both probe window.parent.Kiosk, because that is where the runtime installs
    itself. Probing this frame's own window always reads empty and would report
    a false failure on a healthy runtime.
    """
    from utils.kiosk_helpers import KIOSK_IFRAME_HTML, KIOSK_RUNTIME_FAILED

    assert KIOSK_RUNTIME_FAILED.isidentifier(), (
        "the failure marker is interpolated as window.<NAME>, so a hyphenated "
        "name is a syntax error rather than a property access"
    )
    assert KIOSK_RUNTIME_FAILED in KIOSK_IFRAME_HTML, (
        "the failure marker is never set, so a dead runtime cannot be detected"
    )
    assert "RUNTIME NOT LOADED" in KIOSK_IFRAME_HTML, (
        "the watchdog must overwrite the status strip with a diagnosis"
    )
    # The strip is rendered when the Kiosk tab opens, long after the iframe
    # mounted on the landing page. A single timer therefore fires long before
    # there is anything to fix, and the diagnosis never appears.
    assert "MutationObserver" in KIOSK_IFRAME_HTML, (
        "the watchdog must observe the document; a one-shot timer runs before the "
        "Kiosk tab renders #kiosk-status and then gives up"
    )
    # Streamlit redraws the strip on every rerun, resetting it to the
    # placeholder, so the watchdog has to be able to fire more than once.
    assert "connecting" in KIOSK_IFRAME_HTML, (
        "the watchdog must re-check the untouched placeholder, or the first "
        "Streamlit rerun restores 'connecting…' over the diagnosis"
    )
    assert "window.parent.Kiosk" in KIOSK_IFRAME_HTML, (
        "the tripwire/watchdog must probe window.parent.Kiosk; the runtime "
        "installs itself on the parent, so probing this frame reports a false "
        "failure on a healthy runtime"
    )
    assert "KIOSK_RUNTIME_BOOTED" in KIOSK_IFRAME_HTML, (
        "the boot flag is how a browser check distinguishes a live runtime"
    )

    # The watchdog is the only code left when the runtime dies, so it must be
    # syntactically sound. Balanced braces catch the failure mode that already
    # bit this once: a hand-doubled f-string brace that never parsed.
    blocks = re.findall(r"<script>(.*?)</script>", KIOSK_IFRAME_HTML, re.S)
    for block in blocks:
        assert block.count("{") == block.count("}"), (
            "unbalanced braces in an inlined script block; the block will not "
            f"parse: {block[:120]!r}"
        )


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


def test_the_screensaver_actually_advances():
    """The slideshow must move. Showing one picture forever is not a slideshow.

    This is the shape of the bug that shipped: paintImage() special-cased
    "the first image" with `K.pos === 0 ? K.order[0] : nextIndex()`, but K.pos
    was initialised to 0 and that branch never incremented it, so every later
    call took the same branch and returned order[0] again. The screensaver
    looked random exactly once, on the first load, and then held a single
    picture for the rest of the session.
    """
    source = KIOSK_JS.read_text()

    paint = source[source.index("function paintImage") :]
    paint = paint[: paint.index("\n    function nextPrayerInfo")]

    assert "K.pos === 0" not in paint, (
        "paintImage() still special-cases the first image; that branch never "
        "advances K.pos, so the same picture is shown for the whole session"
    )
    assert "nextIndex()" in paint, (
        "paintImage() must advance through the shuffled order on every paint"
    )
    assert "K.pos = -1" in source, (
        "K.pos must start before the first element, so the opening picture is "
        "reached by the same increment as every other one"
    )
    # A reshuffle is allowed to put the previous picture first, which reads as
    # "stuck" on a wall display nobody is watching.
    assert "K.order[0] === previous" in source, (
        "the reshuffle must avoid repeating the previous picture back to back"
    )


def test_a_failed_background_does_not_stick():
    """One unreadable file must not turn the screensaver into a text screen.

    The fallback added its class and its text on the image error path and
    nothing ever removed them, so a single bad file pinned "Kiosk mode active"
    on the display until the page was reloaded.
    """
    source = KIOSK_JS.read_text()

    paint = source[source.index("function paintImage") :]
    paint = paint[: paint.index("\n    function nextPrayerInfo")]

    assert "classList.remove('kiosk-screensaver-images--fallback')" in paint, (
        "paintImage() must clear the fallback class; otherwise one failed image "
        "leaves 'Kiosk mode active' on the wall display permanently"
    )
    assert "removeAttribute('aria-label')" in paint, (
        "the fallback aria-label must be cleared alongside the class"
    )
    # The fallback still has to exist: a black page is worse than a caption.
    assert "kiosk-screensaver-images--fallback" in paint, (
        "an image that fails to load must still produce a deliberate surface "
        "rather than an unexplained black screen"
    )
    assert "K.bgFailed" in source, (
        "a background that fails to load is invisible on the wall tablet unless "
        "it is counted in the diagnostics panel"
    )


def test_assets_are_requested_with_the_runtime_version():
    """Backgrounds and adhan files must carry the runtime's ?v=.

    kiosk.js is static content, so a browser will happily reuse the images and
    audio it cached on an earlier deploy. If the runtime keeps the assets
    versioned but forgets to version these, the screensaver comes up showing
    last month's picture set and the adhan plays a stale file, which reads as
    "the screensaver does not work".
    """
    source = KIOSK_JS.read_text()

    asset = source[source.index("function asset(p)") :]
    asset = asset[: asset.index("\n    }")]
    assert "RUNTIME_VERSION" in asset, (
        "asset() no longer appends the runtime version, so backgrounds and adhan "
        "are served from whatever the browser cached first"
    )
    assert "currentScript" not in source, (
        "kiosk.js is INLINED into the iframe, so there is no script URL and no "
        "usable currentScript; the version must come from the value the inliner "
        "sets on this frame's window"
    )
    assert "window.KIOSK_RUNTIME_VERSION" in source, (
        "the runtime version must be read from window.KIOSK_RUNTIME_VERSION, "
        "which the inliner sets on the iframe window before this file runs"
    )
    # Reading it off the parent instead silently degrades every asset to an
    # unversioned URL, which looks like a caching bug and is not one.
    assert "win.KIOSK_RUNTIME_VERSION" not in source, (
        "the runtime version must not be read from the parent realm; the value "
        "only exists on the iframe window and reading it from win yields 0"
    )


def test_the_runtime_version_is_shown_on_the_admin_page():
    """A stale cache has to be visible without a console.

    The wall tablet cannot open devtools, and the deployed app sits behind a
    login, so the only place a stale runtime can be diagnosed is on the page.
    """
    admin = (REPO_ROOT / "app_pages" / "admin.py").read_text()
    assert 'data-part="version"' in admin, "the Kiosk tab no longer shows the runtime version"

    source = KIOSK_JS.read_text()
    assert "setStatus('version'" in source, (
        "the runtime version chip is never filled, so a stale cache looks "
        "identical to a working runtime"
    )


def test_there_is_only_one_set_of_adhan_test_controls():
    """The runtime buttons and the file-check players must not compete.

    A second heading called "Test adhan playback" sat below the real controls
    with Streamlit's own audio players, and its heading anchor made it look
    like a separate page. Two ways to "test the adhan" is why the controls read
    as broken: people clicked the players, which never touch the runtime.
    """
    admin = (REPO_ROOT / "app_pages" / "admin.py").read_text()
    assert "### Test adhan playback" not in admin, (
        "the duplicate adhan test section is back; it is a Streamlit audio "
        "player and does not exercise the kiosk runtime at all"
    )
    assert "### Adhan files" in admin, (
        "the adhan file-check section should be labelled as a file check, not a "
        "second set of test controls"
    )


def test_static_serving_is_enabled():
    """The screensaver backgrounds and adhan files still need this flag.

    The runtime no longer does -- it is inlined -- but the images and audio it
    points at are still fetched from /app/static, so the flag stays on.
    """
    config = (REPO_ROOT / ".streamlit" / "config.toml").read_text()
    assert "enableStaticServing = true" in config, (
        "enableStaticServing must stay on or the backgrounds and adhan 404 and "
        "the screensaver comes up blank"
    )


def test_streamlit_version_is_pinned():
    """Local and deployed Streamlit must be the same version.

    An unpinned `streamlit` installs whatever is newest in the cloud, so a fix
    verified locally can be running against a different Streamlit than the one
    that was tested. That is not a hypothetical: it is how a fully passing local
    suite left the deployed app visibly unchanged.
    """
    requirements = (REPO_ROOT / "requirements.txt").read_text().splitlines()
    pins = [line for line in requirements if line.strip().startswith("streamlit")]
    assert pins, "streamlit is not listed in requirements.txt at all"
    assert all("==" in line for line in pins), (
        f"streamlit is not pinned: {pins!r}. Local verification then runs against "
        "a different Streamlit than the deployment does."
    )


def test_the_unlock_nag_does_not_cover_the_board():
    """An idle kiosk must not shout at the family task list.

    The runtime is mounted on every page, and the unlock hint used to fire from
    the config-sync loop whenever audio was merely locked. Until the first
    gesture, that is always, so the Board carried a permanent "Tap anywhere
    once to enable the adhan" banner over the task list. It may only appear
    when an adhan is actually stuck waiting for a tap.
    """
    source = KIOSK_JS.read_text()

    sync = source[source.index("if (c.trigger_adhan)") :]
    assert "unlockHint(true" not in sync, (
        "the sync loop raises the unlock hint again; it fires on every page, so "
        "an idle Board shows a permanent adhan banner"
    )
    # The hint is still raised where it matters, at the moment autoplay is
    # actually refused, so a blocked adhan is never silent.
    assert "unlockHint(true, 'Tap anywhere once to let the adhan sound')" in source, (
        "a refused adhan must still be reported; the nag was only ever wrong "
        "while the kiosk was idle"
    )
    # And it is cleared as soon as the session is unlocked.
    assert "if (K.unlocked && K.pendingRetry) unlockHint(false);" in source, (
        "the hint must be dismissed once the media session unlocks"
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
