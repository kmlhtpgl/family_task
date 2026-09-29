"""There is one design, and this is what holds it there.

The Board was rebuilt as its own visual system while the rest of the app stayed
on the light palette it had grown up with, so tapping Board in the nav row moved
you into a different-looking application. The palettes are now the same values,
which is only worth anything if something stops them drifting again -- and
nothing in the language does, because the Board is a separate document with its
own copy of the palette in its own stylesheet.

So the contract is asserted here, at the level of the files:

- the app and the Board agree on every colour they both name
- Streamlit's own theme agrees with both, since it styles the widgets the
  stylesheet cannot reach
- there is no second palette to drift back towards, and no file is allowed to
  carry a colour of its own
"""

import math
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
STYLES_PY = REPO / "utils" / "styles.py"
BOARD_CSS = REPO / "static" / "board" / "board.css"
APP_PY = REPO / "app.py"
CONFIG_TOML = REPO / ".streamlit" / "config.toml"

# The two modes, in the order they are read. Everything in this file that holds a
# palette to a standard is parametrised over these, because a standard that is
# only checked in one mode is a standard for half a design.
MODES = ("night", "day")

# The Board's names for the same colours. The app's semantic names are the ones
# its component rules use, so this is the mapping between the two vocabularies.
BOARD_ALIASES = {
    "surface-0": "surface-0",
    "surface-1": "surface-1",
    "surface-2": "surface-2",
    "surface-3": "surface-3",
    "hairline": "border-subtle",
    "hairline-strong": "border-strong",
    "text": "text-primary",
    "muted": "text-secondary",
    "faint": "text-tertiary",
    "accent": "accent",
    "good": "success",
    "warn": "warning",
    "late": "danger",
}

# Every colour the Board names is either mapped above or excused here, and
# test_every_colour_the_board_names_is_accounted_for keeps that true. The list is
# empty: the app splits a colour into a text/subtle/border family, but it uses the
# same value for the text part, so there is nothing to excuse yet.
NOT_COMPARED: set[str] = set()


# ── oklch, so two spellings of one colour can be compared ────────────────────


def oklch_to_hex(spec: str) -> str:
    """Convert an `oklch(L C H)` string to the hex a browser would paint.

    The comparison below is only meaningful if both sides go through the same
    conversion, and oklch is what both files are written in. Out-of-gamut values
    are clamped, which is also what a canvas does, so this matches what the
    audit measures in the browser.
    """
    numbers = [float(n) for n in re.findall(r"-?[\d.]+", spec)]
    lightness, chroma, hue = numbers[0], numbers[1], numbers[2]
    a = chroma * math.cos(math.radians(hue))
    b = chroma * math.sin(math.radians(hue))

    l_ = lightness + 0.3963377774 * a + 0.2158037573 * b
    m_ = lightness - 0.1055613458 * a - 0.0638541728 * b
    s_ = lightness - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_**3, m_**3, s_**3

    linear = (
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )
    encoded = [
        12.92 * c if c <= 0.0031308 else 1.055 * max(c, 0.0) ** (1 / 2.4) - 0.055
        for c in linear
    ]
    return "#" + "".join(f"{round(min(1.0, max(0.0, c)) * 255):02X}" for c in encoded)


def read_oklch(source: str) -> dict:
    """Every `--name: oklch(...)` declaration in a block of CSS, as hex.

    Deliberately a block scanner and not a file scanner. Now that there are two
    palettes, a file-wide scan reads both of them, and the later block silently
    overwrites the earlier one -- so `test_the_board_and_the_app_paint_the_same_colours`
    would go on passing while checking only the day values against a Board, and
    night could rot unnoticed. That is a test that reads as if it covers both
    modes and covers one, which is worse than no test. The two readers below are
    the only way to get a palette out of a file.
    """
    found = {}
    for name, spec in re.findall(r"(--[\w-]+):\s*(oklch\([^)]*\))", source):
        found[name.lstrip("-")] = oklch_to_hex(spec)
    return found


def _python_token_block(source: str, variable: str) -> str:
    match = re.search(rf'^{variable} = """\n(.*?)^"""', source, re.DOTALL | re.MULTILINE)
    assert match, f"{variable} is not a triple-quoted block in styles.py"
    return match.group(1)


def read_app_palette(mode: str) -> dict:
    """The app's palette for one mode, out of the single block that applies to it."""
    source = STYLES_PY.read_text()
    return read_oklch(_python_token_block(source, "_TOKENS_DAY" if mode == "day" else "_TOKENS"))


def _board_block(mode: str) -> str:
    """The Board's token block for one mode, as source.

    Night is kept in the unscoped `:root` and day in a `[data-theme="day"]`
    block, which is the same shape the app uses and the same attribute
    index.html already carries. Night is therefore "the file with the day block
    taken out", so a stray unscoped declaration still lands in the night palette
    and is still compared rather than quietly ignored.
    """
    css = BOARD_CSS.read_text()
    day_block = re.search(r'^\[data-theme="day"\][^{]*\{(.*?)^\}', css, re.DOTALL | re.MULTILINE)
    if mode == "day":
        assert day_block, 'board.css has no [data-theme="day"] block, so the Board cannot go light'
        return day_block.group(1)
    return re.sub(
        r'^\[data-theme="day"\][^{]*\{.*?^\}', "", css, flags=re.DOTALL | re.MULTILINE
    )


def read_board_palette(mode: str) -> dict:
    """The Board's colours for one mode."""
    return read_oklch(_board_block(mode))


def read_board_number(mode: str, name: str) -> float:
    """A bare-number token, such as `--person-lightness: 0.74`.

    read_oklch only sees oklch() declarations, so a scalar token is invisible to
    it and reading one through the palette returns a KeyError that looks like the
    token is missing from the file.
    """
    match = re.search(rf"--{re.escape(name)}:\s*([0-9.]+)\s*;", _board_block(mode))
    assert match, f'{mode}: --{name} is not a number in board.css'
    return float(match.group(1))


# ── The app and the Board are the same palette ───────────────────────────────


@pytest.mark.parametrize("mode", MODES)
def test_the_board_and_the_app_paint_the_same_colours(mode):
    """The reason this file exists.

    Two documents, two stylesheets, one palette. The Board's flag row was once
    written out again inside app.py with its own oklch values, and the two
    copies drifted without anybody noticing, because nothing compared them.

    Now the same argument runs twice, because a drift in either mode is a drift.
    A Board that went light against a night app is exactly the original bug in
    new clothes.
    """
    board = read_board_palette(mode)
    app = read_app_palette(mode)

    mismatched = []
    for board_name, app_name in BOARD_ALIASES.items():
        if board_name not in board:
            continue
        assert app_name in app, f"the app no longer defines --{app_name}"
        if board[board_name] != app[app_name]:
            mismatched.append(
                f"{mode}: --{board_name} is {board[board_name]} on the Board but "
                f"--{app_name} is {app[app_name]} in the app"
            )
    assert not mismatched, "the two palettes have drifted:\n  " + "\n  ".join(mismatched)


@pytest.mark.parametrize("mode", MODES)
def test_every_colour_the_board_names_is_accounted_for(mode):
    """A new colour on the Board has to be compared, or deliberately not.

    Otherwise adding a token to board.css is silently outside the contract above:
    the mapping is a hand-written list, and a hand-written list that nobody checks
    for completeness is how a token ends up in one file and not the other. In day
    mode it is how a token ends up in one *mode* and not the other.
    """
    board = read_board_palette(mode)
    unmapped = set(board) - set(BOARD_ALIASES) - NOT_COMPARED
    assert not unmapped, (
        f"the Board defines {sorted(unmapped)} in {mode} and the app is not held to them; "
        f"map them in BOARD_ALIASES or excuse them in NOT_COMPARED"
    )


def test_streamlits_own_theme_is_the_same_palette():
    """Widgets the stylesheet cannot reach are themed from config.toml.

    The file uploader's drop zone, the slider track, the toggle and the sidebar
    are all React components that read this file, so a stale value here is a
    light island in a dark app -- which is most of what the old board button was
    being blamed for.

    Held against night on purpose, and this is the one place a mode cannot be
    checked twice. config.toml is read once when the server starts and there is
    no supported way to rewrite it from a running app, so it can only ever hold
    one set of values. It is pinned to night for two reasons: night is the mode
    the app opens in, so those values are the ones a first paint uses before the
    mode script has run anything; and if this file were pointed at the day
    palette instead, every unstyled React surface would be light on arrival and
    would then go dark under the custom stylesheet, which is a visible flash on
    every load.

    The cost of that decision is that day mode's uncovered widget chrome is
    driven entirely by CSS. That is not free, and it is exactly why
    `test_the_day_mode_reaches_the_widget_chrome_the_stylesheet_misses` exists
    below: the fix is more rules in _COMPONENT_CSS, not a second config file.
    """
    app = read_app_palette("night")
    config = CONFIG_TOML.read_text()

    for token, key in (
        ("accent", "primaryColor"),
        ("surface-0", "backgroundColor"),
        ("surface-1", "secondaryBackgroundColor"),
        ("text-primary", "textColor"),
    ):
        match = re.search(rf'^{key}\s*=\s*"([^"]+)"', config, re.MULTILINE)
        assert match, f"{key} is not set in config.toml"
        assert match.group(1).upper() == app[token], (
            f"{key} is {match.group(1)} but --{token} is {app[token]}"
        )


# ── Two modes, one design ─────────────────────────────────────────────────────


def test_both_modes_describe_the_same_design():
    """A second palette is only a second *design* if it agrees about the design.

    Same names, same count. If day mode introduced `--card` while night called it
    `--surface-1`, or quietly dropped a token, then a rule written against the
    pair would resolve differently in the two modes and the two would stop being
    the same app wearing two coats.

    This is what replaces the old ban on a second palette. The ban was not
    wrong about the risk -- two palettes really is how one design becomes two --
    it was wrong about the remedy, because keeping the file monochrome kept the
    app from ever being readable in daylight. Holding both to one set of names is
    the version of the same idea that survives the feature.
    """
    night = read_app_palette("night")
    day = read_app_palette("day")

    assert set(night) == set(day), (
        "the two modes do not describe the same design: night only "
        f"{sorted(set(night) - set(day))}, day only {sorted(set(day) - set(night))}"
    )


def test_the_mode_actually_changes_the_palette():
    """Otherwise the switch is a control that does nothing.

    Guarded on the surface and text ramps specifically. It is not enough to
    assert the two dictionaries differ somewhere: a palette that is identical
    except for one decorative token passes that, and a page that never changes
    tone is indistinguishable from a mode that is wired up wrongly.
    """
    night = read_app_palette("night")
    day = read_app_palette("day")

    for token in (
        "surface-0",
        "surface-1",
        "surface-2",
        "surface-3",
        "text-primary",
        "text-tertiary",
        "accent",
    ):
        assert night[token] != day[token], f"--{token} is {night[token]} in both modes"


def test_the_mode_is_an_attribute_and_not_an_argument():
    """How the mode is selected, and why nothing takes one.

    `_build_css()` and `apply_custom_styles()` still take no arguments, and that
    is now load-bearing rather than incidental. Both palettes are in every
    stylesheet, always; choosing between them is one attribute on <html>. If a
    parameter were added here, the stylesheet would depend on a value that only
    exists on a rerun -- which is how the mode would come to lag a click, and how
    the Board would end up needing a remount to follow the app.

    `dark_mode` stays banned for a different reason than it was. It used to be a
    variable nothing read, so the app was light while the stylesheet carried a
    palette no screen could reach. The mode is real now and genuinely read; a
    token by that name would be a second, parallel, unread way of saying the
    same thing.
    """
    import inspect

    from utils import styles

    assert list(inspect.signature(styles.apply_custom_styles).parameters) == []
    assert list(inspect.signature(styles._build_css).parameters) == []
    assert "dark_mode" not in STYLES_PY.read_text()
    assert "dark_mode" not in APP_PY.read_text()


def test_the_stylesheet_defines_no_colour_of_its_own():
    """A literal in a component rule is a colour that skipped the palette.

    This is the check that would have caught the old theme spreading back out: a
    hex in a rule is how the next design gets in, and the token blocks are the
    only place a colour is supposed to be decided. Comments are stripped
    first, because prose is allowed to name a colour it is talking about.

    The kiosk block is exempt by design and by its own comment -- the
    screensaver and adhan paint on their own near-black backdrop and their
    z-index and pointer-events are load-bearing.
    """
    source = STYLES_PY.read_text()
    kiosk_at = source.index("_KIOSK_CSS = ")
    themed = re.sub(r"/\*.*?\*/", "", source[:kiosk_at], flags=re.DOTALL)

    literals = re.findall(r"#[0-9A-Fa-f]{3,8}\b|rgba?\(", themed)
    assert not literals, f"hard-coded colour(s) {literals[:4]} outside the token block"

    # The hex check above cannot see an oklch literal, which is the notation this
    # file actually uses -- so on its own it would pass a rule that decided its
    # own colour. Both token blocks are excluded explicitly rather than by
    # position, because there are two of them now and "the block above" is no
    # longer a place a rule could accidentally land in.
    outside = themed
    for variable in ("_SHARED_TOKENS", "_TOKENS", "_TOKENS_DAY"):
        match = re.search(rf'^{variable} = """\n.*?^"""', outside, re.DOTALL | re.MULTILINE)
        assert match, f"{variable} is missing; the palette is not where it should be"
        outside = outside.replace(match.group(0), "")

    # A real oklch() always starts with a number, because L always does. Requiring
    # one is what keeps prose out: styles.py has a comment that says the browser
    # "could not read oklch() at all", the comment stripper above only knows
    # about /* */, and a looser match swallows every comment between that bare
    # oklch() and the next closing bracket in the file.
    stray = re.findall(r"oklch\(\s*[\d][^)]*\)", outside)
    assert not stray, (
        f"oklch literal(s) {stray[:3]} outside the token blocks; a colour decided "
        f"in a rule is a second palette forming"
    )


def test_the_shell_carries_no_palette():
    """app.py decides which page renders; it does not decide what one looks like.

    The Board's colours lived here once, in a style block inside the board
    branch, which meant the same Board had two palettes depending on which file
    you read. Only layout may live in the shell.
    """
    source = APP_PY.read_text()
    assert not re.search(r"#[0-9A-Fa-f]{3,8}\b|rgba?\(|oklch\(", source), (
        "app.py has a colour in it; the design belongs in utils/styles.py"
    )


def test_the_board_chrome_is_styled_from_the_shared_stylesheet():
    """The Board's flag row is the app's flag row, and it is token-driven.

    It used to be a style block inside app.py, quoting the Board's own values.
    """
    from utils import styles

    css = styles._build_css()
    assert ".board-flag" in css, "the flag row is not in the shared stylesheet"
    assert "board-flag" not in APP_PY.read_text(), (
        "the flag row is styled in the shell again"
    )

    rules = re.findall(r"\.board-flag[^{]*\{[^}]*\}", css)
    assert rules, "no .board-flag rule found"
    for rule in rules:
        colours = re.findall(r"#[0-9A-Fa-f]{3,8}\b|rgba?\(|oklch\(", rule)
        assert not colours, f"the flag row quotes a colour instead of a token: {rule}"
        assert "var(--" in rule, f"the flag row is not reading the palette: {rule}"


# ── The palette is legible, not just consistent ──────────────────────────────


def relative_luminance(hex_color: str) -> float:
    def channel(c: int) -> float:
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(int(hex_color[i : i + 2], 16)) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize(
    "text_token",
    ["text-primary", "text-secondary", "text-tertiary", "accent", "success", "warning", "danger"],
)
@pytest.mark.parametrize("surface_token", ["surface-0", "surface-1", "surface-2", "surface-3"])
def test_text_colours_are_legible_on_every_surface(text_token, surface_token, mode):
    """4.5:1 for body copy, on the darkest and the lightest thing it can land on.

    Held as a number rather than a description because the failure is invisible
    to anybody who can see the screen: the old theme's #999 on white was
    2.85:1, and it looked fine.

    In both modes, and the day run is the one that earns its keep. Every status
    colour has to darken for daylight, because a saturated hue carries very
    little luminance and the day surfaces are light. Getting that wrong looks
    correct -- a bright cyan on white is a perfectly recognisable cyan, just an
    illegible one -- so nothing short of this number catches it.
    """
    tokens = read_app_palette(mode)
    ratio = contrast(tokens[text_token], tokens[surface_token])
    assert ratio >= 4.5, (
        f"{mode}: --{text_token} on --{surface_token} is {ratio:.2f}:1, "
        f"under the 4.5:1 floor"
    )


def test_a_persons_colour_says_who_they_are_and_not_what_light_it_is():
    """The payload must not carry a finished colour.

    The six person accents are identities: the same six people, in the same
    order, on every render. What is *not* an identity is the lightness -- that is
    a property of the room the Board is in. Sending a whole oklch() string
    freezes the lighting into the payload, and the only way to light the Board
    for daylight becomes editing a string in a Python file that a human reads as
    a list of colours.

    So the payload carries chroma, hue and a small per-person lift, and
    --person-lightness in the stylesheet carries the mode. Asserted as a shape
    because a finished string here is a silent failure, not a crash: it still
    renders, it is just unreadable in one of the two modes.
    """
    from utils.board.payload import ACCENT_HUES

    assert ACCENT_HUES, "the Board has no person colours at all"
    for accent in ACCENT_HUES:
        assert "oklch" not in str(accent), (
            f"{accent} is a finished colour; send chroma, hue and lift and let "
            f"--person-lightness hold the mode"
        )
        assert set(accent) == {"chroma", "hue", "lift"}, (
            f"{accent} is not exactly chroma/hue/lift"
        )
        assert 0.0 < accent["chroma"] <= 0.4
        assert 0 <= accent["hue"] <= 360


@pytest.mark.parametrize("mode", MODES)
def test_every_persons_colour_is_legible_in_both_modes(mode):
    """Each of the six, on each surface it can land on, in each mode.

    This is the check that the Board never had and could not have had. The accents
    were authored once, at one lightness, against a dark wall -- and with no day
    mode there was nothing for them to be wrong *about*, so they stayed perfect
    and were carried into daylight measuring between 2.08:1 and 2.59:1. Every one
    of the six was still recognisably that colour and none of them was readable.

    Recomputing the colour from the payload's hue and the stylesheet's base means
    the assertion follows the two halves rather than a literal, so re-tuning the
    night palette or the day base moves the test with it instead of freezing one
    answer.
    """
    from utils.board.payload import ACCENT_HUES

    board = read_board_palette(mode)
    base = read_board_number(mode, "person-lightness")

    for i, accent in enumerate(ACCENT_HUES):
        # Same composition the Board does, in oklch(L C H) order.
        lightness = base + accent["lift"]
        assert 0.0 <= lightness <= 1.0, f"person {i}: lightness {lightness} is out of range"
        colour = oklch_to_hex(f"oklch({lightness} {accent['chroma']} {accent['hue']})")
        for surface_token in ("surface-0", "surface-1", "surface-2"):
            ratio = contrast(colour, board[surface_token])
            assert ratio >= 4.5, (
                f"{mode}: person {i} on --{surface_token} is {ratio:.2f}:1, "
                f"under the 4.5:1 floor (base {base}, lift {accent['lift']})"
            )


def test_the_night_board_still_looks_the_way_it_did():
    """Moving the lightness into a token must not have moved the night colours.

    --person-lightness at 0.73 with the original lifts reproduces the six values
    this file was written against -- 0.72, 0.76, 0.72, 0.74, 0.71, 0.78 -- so
    this pins the night wall to the colours people are used to and catches a
    future retune that quietly changes it.
    """
    assert read_board_number("night", "person-lightness") == 0.73

    from utils.board.payload import ACCENT_HUES

    assert [round(0.73 + a["lift"], 2) for a in ACCENT_HUES] == [
        0.72, 0.76, 0.72, 0.74, 0.71, 0.78,
    ]


def test_button_labels_take_the_buttons_size():
    """A button's size rule has to reach the text inside it.

    Streamlit renders a button's label as its own markdown paragraph, nested three
    elements deep, and that container re-establishes 1rem. So every label in the
    app rendered at 16px whatever the button asked for, and the nav row measured
    16px next to a 13px button box -- the one thing on the page you would have
    looked at first. Nothing about the stylesheet said 16px; the label just never
    inherited.
    """
    from utils import styles

    css = styles._build_css()
    for selector in (
        '[data-testid="stButton"] [data-testid="stMarkdownContainer"]',
        '[data-testid="stDownloadButton"] [data-testid="stMarkdownContainer"]',
        '[data-testid="stLinkButton"] [data-testid="stMarkdownContainer"]',
    ):
        assert selector in css, f"no rule lets a button label inherit: {selector}"
    assert re.search(
        r'\[data-testid="stButton"\][^{]*stMarkdownContainer[^{]*\{[^}]*'
        r"font-size:\s*inherit",
        css,
        re.DOTALL,
    ), "the button's markdown container is not inheriting the button's font-size"


@pytest.mark.parametrize("mode", MODES)
def test_the_filled_primary_button_can_be_read(mode):
    """The one place the app puts a label on top of the accent.

    The light theme's white-on-blue was fine there because its accent was dark.
    This accent is a bright cyan, and white on it measures 1.98:1, so the label
    is the page colour instead.

    Both modes invert this token against each other, and the inversion is easy to
    get half-done: --accent-fg and --accent move together, and a day palette that
    darkened the accent but left a near-black label behind would produce a
    primary button nobody can read.
    """
    tokens = read_app_palette(mode)
    assert contrast(tokens["accent-fg"], tokens["accent"]) >= 4.5, (
        f"{mode}: the primary button's label does not clear 4.5:1 on the accent"
    )
