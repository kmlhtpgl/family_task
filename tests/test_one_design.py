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
    """Every `--name: oklch(...)` declaration in a block of CSS, as hex."""
    found = {}
    for name, spec in re.findall(r"(--[\w-]+):\s*(oklch\([^)]*\))", source):
        found[name.lstrip("-")] = oklch_to_hex(spec)
    return found


# ── The app and the Board are the same palette ───────────────────────────────


def test_the_board_and_the_app_paint_the_same_colours():
    """The reason this file exists.

    Two documents, two stylesheets, one palette. The Board's flag row was once
    written out again inside app.py with its own oklch values, and the two
    copies drifted without anybody noticing, because nothing compared them.
    """
    board = read_oklch(BOARD_CSS.read_text())
    app = read_oklch(STYLES_PY.read_text())

    mismatched = []
    for board_name, app_name in BOARD_ALIASES.items():
        if board_name not in board:
            continue
        assert app_name in app, f"the app no longer defines --{app_name}"
        if board[board_name] != app[app_name]:
            mismatched.append(
                f"--{board_name} is {board[board_name]} on the Board but "
                f"--{app_name} is {app[app_name]} in the app"
            )
    assert not mismatched, "the two palettes have drifted:\n  " + "\n  ".join(mismatched)


def test_every_colour_the_board_names_is_accounted_for():
    """A new colour on the Board has to be compared, or deliberately not.

    Otherwise adding a token to board.css is silently outside the contract above:
    the mapping is a hand-written list, and a hand-written list that nobody checks
    for completeness is how a token ends up in one file and not the other.
    """
    board = read_oklch(BOARD_CSS.read_text())
    unmapped = set(board) - set(BOARD_ALIASES) - NOT_COMPARED
    assert not unmapped, (
        f"the Board defines {sorted(unmapped)} and the app is not held to them; "
        f"map them in BOARD_ALIASES or excuse them in NOT_COMPARED"
    )


def test_streamlits_own_theme_is_the_same_palette():
    """Widgets the stylesheet cannot reach are themed from config.toml.

    The file uploader's drop zone, the slider track, the toggle and the sidebar
    are all React components that read this file, so a stale value here is a
    light island in a dark app -- which is most of what the old board button was
    being blamed for.
    """
    app = read_oklch(STYLES_PY.read_text())
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


# ── There is no second design to drift back towards ──────────────────────────


def test_there_is_one_theme_and_it_is_the_boards():
    """The light/dark duality is gone, not deprecated.

    `dark_mode` was set once in app.py and never read by anything, so the app
    was always light while the stylesheet carried a second palette that no
    screen could reach. Two palettes is how a design stops being one design.
    """
    from utils import styles

    assert not hasattr(styles, "_LIGHT_TOKENS")
    assert not hasattr(styles, "_DARK_TOKENS")
    assert "dark_mode" not in STYLES_PY.read_text()
    assert "dark_mode" not in APP_PY.read_text()

    # No argument to pass, so no way to ask for the other one.
    import inspect

    assert list(inspect.signature(styles.apply_custom_styles).parameters) == []
    assert list(inspect.signature(styles._build_css).parameters) == []


def test_the_stylesheet_defines_no_colour_of_its_own():
    """A literal in a component rule is a colour that skipped the palette.

    This is the check that would have caught the old theme spreading back out: a
    hex in a rule is how the next design gets in, and the palette block above it
    is the only place a colour is supposed to be decided. Comments are stripped
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


@pytest.mark.parametrize(
    "text_token",
    ["text-primary", "text-secondary", "text-tertiary", "accent", "success", "warning", "danger"],
)
@pytest.mark.parametrize("surface_token", ["surface-0", "surface-1", "surface-2", "surface-3"])
def test_text_colours_are_legible_on_every_surface(text_token, surface_token):
    """4.5:1 for body copy, on the darkest and the lightest thing it can land on.

    Held as a number rather than a description because the failure is invisible
    to anybody who can see the screen: the old theme's #999 on white was
    2.85:1, and it looked fine.
    """
    tokens = read_oklch(STYLES_PY.read_text())
    ratio = contrast(tokens[text_token], tokens[surface_token])
    assert ratio >= 4.5, (
        f"--{text_token} on --{surface_token} is {ratio:.2f}:1, under the 4.5:1 floor"
    )


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


def test_the_filled_primary_button_can_be_read():
    """The one place the app puts a label on top of the accent.

    The light theme's white-on-blue was fine there because its accent was dark.
    This accent is a bright cyan, and white on it measures 1.98:1, so the label
    is the page colour instead.
    """
    tokens = read_oklch(STYLES_PY.read_text())
    assert contrast(tokens["accent-fg"], tokens["accent"]) >= 4.5, (
        "the primary button's label does not clear 4.5:1 on the accent"
    )
