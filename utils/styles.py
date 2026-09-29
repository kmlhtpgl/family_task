"""Design system for the Family Task Tracker UI.

Everything visual lives here as plain CSS strings so the stylesheet stays
readable and diffable.

There is one theme, and it is the Board's. The Board was built as its own
visual system first, in ``static/board/board.css``, and the rest of the app
was still wearing the light Todoist palette it had grown up with, so tapping
Board in the nav row moved you into a different-looking application. The
tokens below are now the Board's, re-expressed under the semantic names this
file's component rules already use, so the whole app is restyled by editing
one block.

That block is the only place a colour is defined. Pages reference classes,
never literals, which is what lets a palette change reach every page at once.

Layout note: Streamlit components live in the same document as this stylesheet,
so components reference semantic custom properties (``var(--surface-1)``)
instead of hardcoded colors. The board is the exception: it is a separate
document with its own copy of the same palette, and inherits nothing from
here. ``tests/test_one_design.py`` holds the two to the same values.
"""

import streamlit as st

# ── Design tokens ────────────────────────────────────────────────────────────
# NOTE: the @import below must stay the first rule in the emitted stylesheet or
# the browser discards it and the app silently falls back to system fonts.

_FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700;800&"
    "family=JetBrains+Mono:wght@400;600&display=swap');"
)

# Theme-independent scales: type, radii, motion, layout.
_SHARED_TOKENS = """
:root {
    --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
            'Helvetica Neue', Arial, sans-serif;
    --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;

    /* The Board's ramp: 400 for body copy, 500 for labels, 600 for titles, and
     * 700/800 reserved for figures big enough to be read across a room. */
    --weight-regular: 400;
    --weight-medium: 500;
    --weight-semibold: 600;
    --weight-bold: 700;
    --weight-display: 800;

    --leading-body: 1.6;
    --leading-tight: 1.25;

    /* The Board's radii. Larger than the light theme's, and deliberately so:
     * the roundness is most of what makes the same controls read as the same
     * product on two different pages. */
    --radius-xs: 6px;
    --radius-sm: 10px;
    --radius: 16px;
    --radius-lg: 24px;
    --radius-full: 9999px;

    --transition: 160ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 260ms cubic-bezier(0.16, 1, 0.3, 1);
    --ease-out: cubic-bezier(0.16, 1, 0.3, 1);

    --max-width: 1200px;
}
"""

# The Board's palette, on the semantic names the component rules below already
# use. Authored in oklch so the accent hues stay perceptually even as lightness
# is swept for hover and pressed states, and so every contrast ratio here is a
# number that can be checked rather than guessed.
#
# Muted text is held at or above 4.5:1 on every surface it can land on, which
# is why --text-tertiary is 0.68 and not "the same colour, dimmer": the old
# light theme's mid grey measured 2.85:1 on white. tools/audit.py measures
# this, and now
# genuinely can -- it could not read oklch() at all until this palette landed,
# so the Board's own contrast pass had been vacuous.
#
#   surface-0 0.17    the page floor, near-black
#   surface-1 0.212   a card sitting on it
#   surface-2 0.256   a raised header, a hover
#   surface-3 0.305   pressed, and the highest step
#
# Depth comes from these steps rather than from shadows: at rest a card is a
# hairline, and a shadow means something is genuinely floating.
_TOKENS = """
:root {
    --surface-0: oklch(0.17 0.018 265);
    --surface-1: oklch(0.212 0.021 265);
    --surface-2: oklch(0.256 0.024 265);
    --surface-3: oklch(0.305 0.026 265);

    --border-subtle: oklch(0.97 0 0 / 0.09);
    --border-default: oklch(0.97 0 0 / 0.12);
    --border-strong: oklch(0.97 0 0 / 0.16);

    /* Chroma rises as the neutral darkens, the same progression the Board uses:
     * a darker grey needs a little colour in it to read as a colour. */
    --text-primary: oklch(0.97 0.004 265);
    --text-secondary: oklch(0.775 0.012 265);
    --text-tertiary: oklch(0.68 0.014 265);

    --accent: oklch(0.78 0.16 232);
    /* Lighter on hover, darker pressed: the same hue held even as lightness
     * moves, which a hex ramp cannot do. */
    --accent-hover: oklch(0.84 0.15 232);
    --accent-active: oklch(0.73 0.16 232);
    --accent-subtle: oklch(0.25 0.055 232);
    --accent-border: oklch(0.36 0.08 232);
    /* Near-black on the accent, not white. The accent is a bright cyan on a
     * dark surface and white on it measures 1.98:1. */
    --accent-fg: oklch(0.17 0.018 265);
    --accent-shadow: oklch(0.78 0.16 232 / 0.28);
    --on-gradient: oklch(0.17 0.018 265);

    --gold: oklch(0.85 0.13 92);
    --gold-subtle: oklch(0.26 0.05 92);
    --gold-border: oklch(0.36 0.065 92);

    --success: oklch(0.82 0.17 152);
    --success-subtle: oklch(0.24 0.045 152);
    --success-border: oklch(0.34 0.06 152);

    --warning: oklch(0.84 0.15 82);
    --warning-subtle: oklch(0.25 0.05 82);
    --warning-border: oklch(0.35 0.065 82);

    --danger: oklch(0.72 0.19 22);
    --danger-subtle: oklch(0.25 0.06 22);
    --danger-border: oklch(0.35 0.08 22);

    /* Info is the accent. The Board has exactly one accent, and two of them is
     * how a palette starts looking like a design system nobody chose. */
    --info: oklch(0.78 0.16 232);
    --info-subtle: oklch(0.25 0.055 232);
    --info-border: oklch(0.36 0.08 232);

    /* Nothing is floating at rest. These are for the two things that do:
     * dialogs and menus, and the keyboard focus ring's cast. */
    --shadow-xs: none;
    --shadow-sm: none;
    --shadow-md: 0 18px 48px oklch(0 0 0 / 0.45);
    --shadow-lg: 0 24px 64px oklch(0 0 0 / 0.55);
    --scrim: oklch(0.97 0 0 / 0.04);

    /* The two washes behind the page, from .family-bg in app.py. They are
     * decoration, not a surface and not text, so nothing measures them -- which
     * is exactly why they are tokens. A wash is a colour, and a colour left as a
     * literal is a palette that only exists in the mode it was tuned for: these
     * two were picked against a dark page and would have read as a stain on a
     * white one. Their hues sit either side of the accent on purpose, so the
     * page has some depth behind it that is not the same blue as everything
     * else. */
    --bloom-blue: oklch(0.5 0.15 258 / 0.26);
    --bloom-teal: oklch(0.48 0.14 195 / 0.2);

    /* The one place white is still allowed: the travelling sheen on a filling
     * progress bar, which is a highlight and not a surface. */
    --shine: oklch(1 0 0 / 0.22);
}
"""


# Day mode, and the reason this is a second block of *values* rather than a
# second set of *names*. Every selector and every semantic in the file above is
# unchanged: a card is still `--surface-1`, the accent is still `--accent`, and
# a rule written once still covers both modes. Only the numbers behind the names
# differ. That is the whole difference between a day mode and a second design,
# and it is what lets tests/test_one_design.py hold both to one standard instead
# of letting them drift into two apps that happen to share a repo.
#
# The two palettes mirror each other deliberately. Depth still comes from the
# surface ramp, never from shadows at rest, but the ramp runs the other way:
# night goes lighter as it rises (0.17 to 0.305) because a bright plane is the
# most prominent thing on a dark page, and day goes darker as it rises (0.985 to
# 0.912) for the same reason. A rule that picks --surface-3 to mean "the highest
# step" therefore means the same thing in both modes.
#
# Selector is :root[data-mode="day"], not [data-mode="day"], on purpose. The
# attribute lands on <html>, so a bare [data-mode="day"] would be the same
# specificity as the :root block above and would win only by source order. This
# one wins on specificity, so the mode cannot be undone by the order the two
# blocks happen to be emitted in.
_TOKENS_DAY = """
:root[data-mode="day"] {
    --surface-0: oklch(0.985 0.002 265);
    --surface-1: oklch(0.962 0.004 265);
    --surface-2: oklch(0.940 0.005 265);
    --surface-3: oklch(0.912 0.006 265);

    /* Borders invert to black at low alpha: the same hairline, drawn with the
     * ink rather than the light. */
    --border-subtle: oklch(0.20 0.01 265 / 0.10);
    --border-default: oklch(0.20 0.01 265 / 0.14);
    --border-strong: oklch(0.20 0.01 265 / 0.22);

    /* Chroma rises as the neutral darkens, the same progression the Board uses:
     * a lighter grey needs a little colour in it to read as a colour. */
    --text-primary: oklch(0.24 0.012 265);
    --text-secondary: oklch(0.37 0.012 265);
    --text-tertiary: oklch(0.45 0.012 265);

    /* The accent is a deep cyan here, not the bright one. A saturated hue
     * carries very little luminance, and --accent is a text colour as often as
     * it is a fill: the night value on a white surface measures 2.6:1. */
    --accent: oklch(0.45 0.14 232);
    /* Darker on hover, deeper pressed: the same inversion the night block
     * makes, and the same hue held as lightness moves. */
    --accent-hover: oklch(0.39 0.14 232);
    --accent-active: oklch(0.52 0.14 232);
    --accent-subtle: oklch(0.935 0.035 232);
    --accent-border: oklch(0.78 0.09 232);
    /* Near-white on the accent, the inversion of the night's near-black. The
     * accent is a deep cyan by day and near-black on it measures 2.7:1. */
    --accent-fg: oklch(0.99 0 0);
    --accent-shadow: oklch(0.45 0.14 232 / 0.30);
    --on-gradient: oklch(0.99 0 0);

    /* Still one gold. A paler day gold is the same gold in daylight. */
    --gold: oklch(0.45 0.12 75);
    --gold-subtle: oklch(0.950 0.040 75);
    --gold-border: oklch(0.82 0.08 75);

    --success: oklch(0.44 0.13 152);
    --success-subtle: oklch(0.940 0.040 152);
    --success-border: oklch(0.80 0.08 152);

    --warning: oklch(0.45 0.12 70);
    --warning-subtle: oklch(0.950 0.045 80);
    --warning-border: oklch(0.82 0.08 80);

    --danger: oklch(0.45 0.18 25);
    --danger-subtle: oklch(0.940 0.045 25);
    --danger-border: oklch(0.80 0.09 25);

    /* Info is the accent, in both modes. The Board has exactly one accent, and
     * two of them is how a palette starts looking like a design system nobody
     * chose. */
    --info: oklch(0.45 0.14 232);
    --info-subtle: oklch(0.935 0.035 232);
    --info-border: oklch(0.78 0.09 232);

    /* Day mode is where shadows are allowed to be shadows, because there is a
     * paper-coloured surface underneath for them to fall across. They stay off
     * the resting card, which is still a hairline. */
    --shadow-xs: 0 1px 2px oklch(0.20 0.02 265 / 0.07);
    --shadow-sm: 0 2px 8px oklch(0.20 0.02 265 / 0.09);
    --shadow-md: 0 18px 48px oklch(0.20 0.02 265 / 0.15);
    --shadow-lg: 0 24px 64px oklch(0.20 0.02 265 / 0.22);
    --scrim: oklch(0.20 0.01 265 / 0.04);

    /* The two washes behind the page. Inverted, not just faded: on a dark page a
     * wash is a mid-tone glow on black, and on a light page the same numbers are
     * a stain. So day is a pale, low-chroma tint carried at a higher alpha --
     * less pigment, spread the same distance. */
    --bloom-blue: oklch(0.90 0.055 258 / 0.6);
    --bloom-teal: oklch(0.92 0.045 195 / 0.55);

    --shine: oklch(1 0 0 / 0.55);
}
"""

# ── App chrome ───────────────────────────────────────────────────────────────

_BASE_CSS = """
* {
    font-family: var(--font);
}

/* Streamlit ships its own body font (Source Sans) and wins the cascade over a
 * bare `*` selector. Without this the design renders in the wrong typeface
 * even though the token is correct. */
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stSidebar"], [data-testid="stMain"] {
    font-family: var(--font) !important;
}

html, body,
.stApp,
[data-testid="stAppViewContainer"] {
    background: var(--surface-0) !important;
    color: var(--text-primary);
}

/* Scrollbars, the native text-selection handles and any control the browser
 * draws for itself are themed by the browser, not by us, and it asks this
 * property rather than our tokens. Without it a Day page keeps a dark scrollbar
 * down the right edge, which is the kind of seam that makes a mode look
 * unfinished. Night is the default so the app is correct before any script runs;
 * the day value has to match the :root[data-mode="day"] selector above, because
 * CSS inherits `color-scheme` but a bare [data-mode] would not be specific
 * enough to beat the default it sits beside. */
html { color-scheme: dark; }
html[data-mode="day"] { color-scheme: light; }

[data-testid="stAppViewContainer"] .block-container,
.block-container {
    /* Board is full-bleed. Classic routes use the same stage now instead of
     * shrinking into the old centered 1200px application shell. */
    width: 100% !important;
    max-width: none !important;
    padding: 1rem clamp(1rem, 4vw, 4rem) 3rem !important;
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="collapsedControl"] { z-index: 100; }

/* ── The page behind the page ──
   Two very wide, very soft washes, and the same answer the Board gives to a
   large dark surface: depth you can feel rather than a texture that fights the
   type. This replaces a 5%-opacity SVG of three people that had been sitting in
   app.py since before the redesign, drawn in the old theme's blue -- invisible
   on a near-black page, and a second palette besides. */
.family-bg {
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    overflow: hidden;
}
.family-bg::before,
.family-bg::after {
    content: "";
    position: absolute;
    border-radius: 50%;
    filter: blur(90px);
}
.family-bg::before {
    width: 60vw;
    height: 46vh;
    top: -16vh;
    left: -10vw;
    background: radial-gradient(
        circle at 50% 50%,
        var(--bloom-blue),
        transparent 70%
    );
}
.family-bg::after {
    width: 52vw;
    height: 42vh;
    bottom: -18vh;
    right: -8vw;
    background: radial-gradient(
        circle at 50% 50%,
        var(--bloom-teal),
        transparent 70%
    );
}

/* ── Typography ── */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font);
    color: var(--text-primary);
    font-weight: var(--weight-semibold);
    letter-spacing: -0.02em;
    line-height: 1.25;
}
h1 { font-size: 1.75rem; font-weight: var(--weight-bold); letter-spacing: -0.03em; }
h2 { font-size: 1.3125rem; }
h3 { font-size: 1.0625rem; }
h4 { font-size: 0.9375rem; }
h5, h6 { font-size: 0.875rem; }

p, li {
    color: var(--text-secondary);
    /* Todoist runs body copy at 1.75. The extra leading is most of what makes
     * a dense dashboard feel calm rather than cramped. */
    line-height: var(--leading-body);
    font-size: 0.9375rem;
    letter-spacing: 0.005em;
}
strong, b { color: var(--text-primary); font-weight: var(--weight-semibold); }

hr {
    border: 0;
    height: 1px;
    background: var(--border-subtle);
    margin: 1.5rem 0;
}

[data-testid="stCaptionContainer"],
.stCaption {
    color: var(--text-tertiary) !important;
    font-size: 0.8125rem !important;
}

/* ── Widget labels ── */
[data-testid="stWidgetLabel"] label,
.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stDateInput label,
.stRadio label,
.stSlider label,
.stForm label {
    color: var(--text-secondary) !important;
    font-size: 0.8125rem !important;
    font-weight: var(--weight-medium) !important;
    letter-spacing: 0.005em;
}

/* ── Scrollbars ── */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: var(--border-strong);
    border-radius: var(--radius-full);
    border: 3px solid var(--surface-0);
}
::-webkit-scrollbar-thumb:hover { background: var(--text-tertiary); }
"""

_NAV_CSS = """
.nav-scope { display: none; }

/* The header on every page except the Board, and it is the Board's flag row in
   another costume: one compact line, one hairline, nothing floating. It used to
   be a 4.25rem rounded card with a border and a shadow, which is the light
   theme's idea of a header and the clearest single reason the two halves of
   this app looked like two products. */
.top-navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    background: transparent;
    border: 0;
    border-bottom: 1px solid var(--border-subtle);
    border-radius: 0;
    padding: 0 0 0.75rem;
    margin-bottom: 1rem;
    min-height: 0;
    position: relative;
    z-index: 10;
}

.navbar-brand {
    display: flex;
    align-items: baseline;
    gap: 0.625rem;
    text-decoration: none;
    color: inherit;
    cursor: pointer;
}
.navbar-brand::before {
    content: "";
    width: 0.5rem;
    height: 0.5rem;
    flex: 0 0 auto;
    border-radius: 50%;
    background: var(--success);
}
.top-navbar a[href*="nav"] {
    text-decoration: none;
    color: inherit;
    cursor: pointer;
}
.navbar-brand h1 {
    font-size: 1.1875rem;
    font-weight: var(--weight-bold);
    margin: 0;
    letter-spacing: -0.03em;
    white-space: nowrap;
    /* Flat, in the Board's text colour. This was an accent-to-white gradient
     * clipped to the type, which is not in the Board's language and cannot be
     * contrast-checked: the audit reads a painted colour or nothing. */
    color: var(--text-primary);
}
.navbar-brand span {
    color: var(--text-tertiary);
    font-size: 0.75rem;
    font-weight: var(--weight-regular);
    border-left: 1px solid var(--border-default);
    padding-left: 0.625rem;
}
.navbar-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0;
}
/* The Board's small-caps label, on the date rather than on the page name. */
.navbar-actions .nav-date {
    color: var(--text-tertiary);
    font-size: 0.6875rem;
    font-weight: var(--weight-semibold);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
.page-heading {
    display: grid;
    align-content: end;
    gap: 0.35rem;
    min-height: 220px;
    margin: 0.5rem 0 1.5rem;
    padding: 2rem 2.25rem;
    border: 1px solid var(--border-default);
    border-radius: 28px;
    background:
        linear-gradient(115deg, var(--surface-1) 0%, var(--surface-0) 66%),
        var(--surface-1);
    position: relative;
    overflow: hidden;
}
.page-heading::after {
    content: "";
    position: absolute;
    width: 28rem;
    height: 28rem;
    right: -7rem;
    top: -15rem;
    border-radius: 50%;
    border: 1px solid var(--accent-border);
    background: transparent;
    box-shadow: 0 0 0 28px var(--accent-subtle),
        /* The outer ring is the accent at 4%. It was written as a literal, which
         * pinned it to the night accent: a faint bright cyan is right on black
         * and invisible on white. Deriving it from the token means it follows
         * the mode for free, and the two rings stay the same ring. */
        0 0 0 58px color-mix(in oklch, var(--accent) 4%, transparent);
    filter: none;
}
.page-heading__signal {
    position: absolute;
    right: 4rem;
    top: 2.1rem;
    display: flex;
    align-items: end;
    gap: 0.35rem;
    height: 5rem;
    opacity: 0.8;
}
.page-heading__signal span { width: 0.32rem; border-radius: 99px; background: var(--accent); }
.page-heading__signal span:nth-child(1) { height: 2rem; opacity: 0.35; }
.page-heading__signal span:nth-child(2) { height: 4.3rem; }
.page-heading__signal span:nth-child(3) { height: 3rem; opacity: 0.6; }
.page-heading__eyebrow {
    color: var(--accent);
    font: 600 0.68rem var(--font);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    position: relative;
    z-index: 1;
}
.page-heading__title {
    color: var(--text-primary);
    font: 700 clamp(2.35rem, 6vw, 4.5rem)/0.95 var(--font);
    letter-spacing: -0.065em;
    position: relative;
    z-index: 1;
}
.page-heading__description {
    max-width: 44rem;
    color: var(--text-secondary);
    font-size: 0.96rem;
    position: relative;
    z-index: 1;
}
.page-heading__mode {
    position: absolute;
    top: 2rem;
    left: 2.25rem;
    color: var(--text-tertiary);
    font: 600 0.64rem var(--font-mono);
    letter-spacing: 0.14em;
    z-index: 1;
}
.page-heading__mode b { color: var(--accent); font-weight: 600; }
.route-stat-strip {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.65rem;
    margin: 0.75rem 0 1.15rem;
}
.route-stat {
    padding: 0.9rem 1rem;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    background: var(--surface-1);
}
.route-stat__value {
    color: var(--text-primary);
    font: 700 1.45rem/1 var(--font-mono);
    letter-spacing: -0.04em;
}
.route-stat__label {
    margin-top: 0.5rem;
    color: var(--text-secondary);
    font-size: 0.78rem;
    font-weight: 600;
}
.route-stat__hint {
    margin-top: 0.15rem;
    color: var(--text-tertiary);
    font-size: 0.68rem;
}
.profile-identity {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 1rem;
    padding: 1rem 0 1.1rem;
    border-bottom: 1px solid var(--border-subtle);
}
.profile-identity__role {
    color: var(--accent);
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}
.profile-identity__name {
    margin-top: 0.25rem;
    color: var(--text-primary);
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.04em;
}
.profile-identity__detail { color: var(--text-secondary); font-size: 0.8rem; }
.profile-identity__rank {
    padding: 0.45rem 0.7rem;
    border: 1px solid var(--gold-border);
    border-radius: var(--radius-full);
    background: var(--gold-subtle);
    color: var(--gold);
    font-size: 0.72rem;
    font-weight: 600;
    white-space: nowrap;
}
.focus-panel {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 1.5rem;
    margin: 1rem 0 1.25rem;
    padding: 1.35rem 1.5rem;
    border: 1px solid var(--accent-border);
    border-radius: 22px;
    background: linear-gradient(105deg, var(--accent-subtle), var(--surface-1) 62%);
    overflow: hidden;
    position: relative;
}
.focus-panel::after {
    content: "";
    width: 11rem;
    height: 11rem;
    position: absolute;
    right: -4rem;
    bottom: -7rem;
    border: 1px solid var(--accent);
    border-radius: 50%;
    opacity: 0.45;
}
.focus-panel__label { color: var(--accent); font: 600 0.65rem var(--font-mono); letter-spacing: 0.13em; text-transform: uppercase; }
.focus-panel__title { margin-top: 0.35rem; color: var(--text-primary); font-size: 1.25rem; font-weight: 650; letter-spacing: -0.03em; }
.focus-panel__detail { margin-top: 0.25rem; color: var(--text-secondary); font-size: 0.8rem; }
.focus-panel__value { color: var(--text-primary); font: 700 2.2rem/1 var(--font-mono); position: relative; z-index: 1; text-align: right; }
.focus-panel__value small { display: block; margin-top: 0.35rem; color: var(--text-tertiary); font: 0.65rem var(--font); }
.profile-command-grid,
.profile-wide-module,
.profile-achievement-deck {
    margin-top: 1.25rem;
    padding: 1.25rem;
    border: 1px solid var(--border-subtle);
    border-radius: 22px;
    background: linear-gradient(145deg, var(--surface-1), var(--surface-0));
}
.profile-command-grid > [data-testid="stHorizontalBlock"] { gap: 1.25rem; }
.profile-module-title { color: var(--text-primary); font-size: 1.15rem; font-weight: 700; letter-spacing: -0.035em; }
.profile-module-subtitle { margin-top: 0.25rem; color: var(--text-tertiary); font-size: 0.76rem; }
.profile-module-count { margin: 1rem 0 0.65rem; color: var(--accent); font: 600 0.7rem var(--font-mono); letter-spacing: 0.04em; text-transform: uppercase; }
.profile-module-count--muted { color: var(--text-tertiary); }
.profile-task-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin: 0.45rem 0;
    padding: 0.85rem 0.95rem;
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    background: var(--surface-2);
}
.profile-task-card--done { opacity: 0.65; border-left: 3px solid var(--success); }
.profile-task-card__meta { color: var(--text-tertiary); font: 0.68rem var(--font-mono); white-space: nowrap; }
.profile-achievement-deck { min-height: 5rem; }
.profile-weekly-heading {
    display: flex;
    align-items: baseline;
    gap: 0.65rem;
    margin: 1.5rem 0 0.75rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-default);
    color: var(--text-primary);
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: -0.025em;
}
.profile-weekly-heading span { color: var(--accent); font: 600 0.68rem var(--font-mono); }
.profile-weekly-heading small { color: var(--text-tertiary); font-size: 0.7rem; font-weight: 400; }
.profile-week-task {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin: 0.45rem 0;
    padding: 0.9rem 1rem;
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    background: var(--surface-2);
}
.reading-shelf-heading,
.reading-archive-heading {
    display: grid;
    gap: 0.25rem;
    margin: 1.25rem 0 0.75rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-default);
}
.reading-shelf-heading span,
.reading-archive-heading span { color: var(--accent); font: 600 0.64rem var(--font-mono); letter-spacing: 0.14em; }
.reading-shelf-heading strong,
.reading-archive-heading strong { color: var(--text-primary); font-size: 1.3rem; letter-spacing: -0.035em; }
.reading-shelf-heading small,
.reading-archive-heading small { color: var(--text-tertiary); font-size: 0.74rem; }
.book-card {
    display: flex;
    gap: 1.1rem;
    margin: 0.7rem 0;
    padding: 1.1rem;
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    background: linear-gradient(110deg, var(--surface-1), var(--surface-2));
    transition: transform var(--transition), border-color var(--transition);
}
.book-card:hover { transform: translateY(-2px); border-color: var(--accent-border); }
.book-card__cover {
    display: grid;
    place-content: center;
    flex: 0 0 4.25rem;
    height: 5.5rem;
    border-radius: 11px;
    background: var(--accent-subtle);
    border: 1px solid var(--accent-border);
    color: var(--accent);
    font: 700 1.55rem/1 var(--font-mono);
    text-align: center;
}
.book-card__cover small { font: 0.65rem var(--font); color: var(--text-tertiary); }
.book-card__body { flex: 1; min-width: 0; }
.book-card__top, .book-card__progress-label { display: flex; justify-content: space-between; gap: 0.75rem; }
.book-card__title { color: var(--text-primary); font-size: 1rem; font-weight: 700; }
.book-card__writer { margin-top: 0.22rem; color: var(--text-tertiary); font-size: 0.74rem; }
.book-card__language { color: var(--accent); font: 600 0.65rem var(--font-mono); text-transform: uppercase; }
.book-card__progress-label { margin-top: 1.35rem; color: var(--text-secondary); font: 0.7rem var(--font-mono); }
.book-card__meta { margin-top: 0.55rem; color: var(--text-tertiary); font-size: 0.68rem; }
.reading-archive-heading { margin-top: 2rem; }
.archive-column-title { display: flex; justify-content: space-between; margin: 0.7rem 0; color: var(--text-primary); font-weight: 650; }
.archive-column-title span { color: var(--accent); font: 0.7rem var(--font-mono); }
.finished-book-card { margin: 0.5rem 0; padding: 0.85rem 0.95rem; border: 1px solid var(--border-subtle); border-radius: 13px; background: var(--surface-1); }
.finished-book-card .row-meta { display: block; margin-top: 0.3rem; white-space: normal; }
.prayer-rhythm-heading, .prayer-heatmap-heading { display: grid; gap: 0.25rem; margin: 1.5rem 0 0.75rem; padding-top: 1rem; border-top: 1px solid var(--border-default); }
.prayer-rhythm-heading span, .prayer-heatmap-heading span { color: var(--accent); font: 600 0.64rem var(--font-mono); letter-spacing: 0.14em; }
.prayer-rhythm-heading strong, .prayer-heatmap-heading strong { color: var(--text-primary); font-size: 1.3rem; letter-spacing: -0.035em; }
.prayer-rhythm-heading small, .prayer-heatmap-heading small { color: var(--text-tertiary); font-size: 0.74rem; }
.prayer-rhythm { display: grid; grid-template-columns: repeat(7, 1fr); gap: 0.55rem; }
.prayer-day { display: grid; gap: 0.2rem; padding: 0.8rem 0.5rem; border: 1px solid var(--border-subtle); border-radius: 15px; background: var(--surface-1); text-align: center; }
.prayer-day span { color: var(--text-tertiary); font: 0.65rem var(--font-mono); text-transform: uppercase; }
.prayer-day strong { color: var(--text-primary); font: 700 1.35rem var(--font-mono); }
.prayer-day small { color: var(--text-secondary); font-size: 0.68rem; }
.prayer-day--clear { border-color: var(--success-border); }
.prayer-day--clear strong { color: var(--success); }
.prayer-day--partial { border-color: var(--warning-border); }
.prayer-day--partial strong { color: var(--warning); }
.prayer-day--missed { border-color: var(--danger-border); }
.prayer-day--missed strong { color: var(--danger); }
.prayer-heatmap { display: grid; grid-template-columns: 1.5fr repeat(5, minmax(4.5rem, 1fr)) 0.7fr; gap: 0.45rem; align-items: center; margin: 0.45rem 0; }
.prayer-heatmap--head { margin-bottom: 0.75rem; color: var(--text-tertiary); font: 600 0.64rem var(--font-mono); text-transform: uppercase; }
.prayer-heatmap--head > div:not(:first-child) { text-align: center; }
.prayer-kid { color: var(--text-primary); font-weight: 650; }
.prayer-cell, .prayer-total { padding: 0.75rem 0.4rem; border-radius: 11px; text-align: center; font: 600 0.72rem var(--font-mono); }
.prayer-cell--clear { background: var(--success-subtle); border: 1px solid var(--success-border); color: var(--success); }
.prayer-cell--missed { background: var(--danger-subtle); border: 1px solid var(--danger-border); color: var(--danger); }
.prayer-total { color: var(--text-primary); background: var(--surface-2); }
@media (max-width: 640px) {
    .prayer-rhythm { gap: 0.25rem; }
    .prayer-day { padding: 0.6rem 0.2rem; }
    .prayer-day strong { font-size: 1rem; }
    .prayer-heatmap { grid-template-columns: 1fr repeat(5, minmax(2.6rem, 1fr)) 0.6fr; gap: 0.2rem; }
    .prayer-heatmap--head { font-size: 0.5rem; }
    .prayer-cell, .prayer-total { padding: 0.6rem 0.1rem; font-size: 0.6rem; }
}
@media (max-width: 640px) {
    .focus-panel { align-items: flex-start; flex-direction: column; }
    .focus-panel__value { align-self: flex-end; }
    .profile-command-grid, .profile-wide-module, .profile-achievement-deck { padding: 1rem; border-radius: 18px; }
    .profile-task-card { align-items: flex-start; flex-direction: column; gap: 0.3rem; }
    .profile-task-card__meta { white-space: normal; }
}
.route-section-label {
    margin: 1.35rem 0 0.6rem;
    color: var(--text-primary);
    font-size: 0.92rem;
    font-weight: 600;
    letter-spacing: -0.01em;
}
.route-section-label span {
    margin-left: 0.45rem;
    color: var(--text-tertiary);
    font: 0.68rem var(--font-mono);
}
.reward-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin: 0.65rem 0 0.2rem;
    padding: 1rem 1.1rem;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    background: var(--surface-1);
}
.reward-card h4 { margin: 0; color: var(--text-primary); }
.reward-month-marker { display: grid; gap: 0.2rem; text-align: center; }
.reward-month-marker span, .reward-leaderboard-heading span, .reward-exchange-heading span { color: var(--accent); font: 600 0.64rem var(--font-mono); letter-spacing: 0.14em; }
.reward-month-marker strong { color: var(--text-primary); font-size: 1.35rem; letter-spacing: -0.035em; }
.reward-month-marker small, .reward-leaderboard-heading small, .reward-exchange-heading small { color: var(--text-tertiary); font-size: 0.72rem; }
.reward-leaderboard-heading, .reward-exchange-heading { display: grid; gap: 0.25rem; margin: 1.4rem 0 0.7rem; padding-top: 1rem; border-top: 1px solid var(--border-default); }
.reward-leaderboard-heading strong, .reward-exchange-heading strong { color: var(--text-primary); font-size: 1.3rem; letter-spacing: -0.035em; }
.reward-leaderboard { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.45rem; }
.reward-leader-row { display: grid; grid-template-columns: 2.2rem 1fr auto; align-items: center; gap: 0.6rem; padding: 0.8rem 0.9rem; border: 1px solid var(--border-subtle); border-radius: 13px; background: var(--surface-1); }
.reward-leader-rank { color: var(--accent); font: 600 0.7rem var(--font-mono); }
.reward-leader-name { color: var(--text-primary); font-weight: 650; }
.reward-leader-name small, .reward-leader-points small { display: block; color: var(--text-tertiary); font-size: 0.65rem; font-weight: 400; }
.reward-leader-points { color: var(--text-primary); font: 700 1.1rem var(--font-mono); text-align: right; }
.reward-exchange-card { display: grid; grid-template-columns: 1fr auto; gap: 0.35rem 1rem; margin: 0.65rem 0; padding: 1.1rem 1.2rem; border: 1px solid var(--border-subtle); border-radius: 19px; background: linear-gradient(110deg, var(--surface-1), var(--surface-2)); }
.reward-exchange-card__identity { display: grid; gap: 0.2rem; }
.reward-exchange-card__kind { color: var(--accent); font: 600 0.62rem var(--font-mono); letter-spacing: 0.12em; text-transform: uppercase; }
.reward-exchange-card__identity strong { color: var(--text-primary); font-size: 1.1rem; }
.reward-exchange-card__identity small { color: var(--text-tertiary); font-size: 0.7rem; }
.reward-exchange-card__value { display: grid; grid-template-columns: auto auto; align-items: baseline; gap: 0.25rem 0.4rem; text-align: right; }
.reward-exchange-card__value strong { color: var(--accent); font: 700 1.5rem var(--font-mono); }
.reward-exchange-card__value small { color: var(--text-tertiary); font-size: 0.65rem; }
.reward-exchange-card__value span { grid-column: 1 / -1; color: var(--text-secondary); font: 0.75rem var(--font-mono); }
.reward-exchange-card__progress { grid-column: 1 / -1; height: 0.3rem; overflow: hidden; border-radius: 99px; background: var(--surface-3); }
.reward-exchange-card__progress div { height: 100%; border-radius: inherit; background: var(--accent); }
.reward-exchange-card__hint { grid-column: 1 / -1; color: var(--text-tertiary); font-size: 0.67rem; }
@media (max-width: 640px) { .reward-leaderboard { grid-template-columns: 1fr; } }
.admin-section-header { display: grid; gap: 0.25rem; margin: 1.75rem 0 1rem; padding: 1.15rem 1.25rem; border-left: 3px solid var(--accent); border-radius: 0 17px 17px 0; background: linear-gradient(100deg, var(--accent-subtle), transparent 70%); }
.admin-section-header span { color: var(--accent); font: 600 0.64rem var(--font-mono); letter-spacing: 0.14em; }
.admin-section-header strong { color: var(--text-primary); font-size: 1.5rem; letter-spacing: -0.04em; }
.admin-section-header small { color: var(--text-secondary); font-size: 0.78rem; }
.admin-create-panel, .admin-inventory-heading { display: grid; gap: 0.25rem; margin: 1.4rem 0 0.85rem; padding: 1rem 1.15rem; border: 1px solid var(--border-subtle); border-radius: 16px; background: var(--surface-1); }
.admin-create-panel { border-color: var(--accent-border); background: linear-gradient(105deg, var(--accent-subtle), var(--surface-1)); }
.admin-create-panel span, .admin-inventory-heading span { color: var(--accent); font: 600 0.62rem var(--font-mono); letter-spacing: 0.14em; }
.admin-create-panel strong, .admin-inventory-heading strong { color: var(--text-primary); font-size: 1.08rem; letter-spacing: -0.025em; }
.admin-create-panel small, .admin-inventory-heading small { color: var(--text-tertiary); font-size: 0.72rem; }
.admin-resource-icon { display: grid !important; place-items: center; width: 3rem !important; height: 3rem !important; border-radius: 12px !important; background: var(--accent-subtle) !important; color: var(--accent) !important; font: 600 0.58rem var(--font-mono) !important; letter-spacing: 0.08em; }
.admin-grid-card { min-height: 4.4rem; }
.stRadio [role="radiogroup"] {
    gap: 0.35rem;
    flex-wrap: wrap;
    padding: 0.35rem;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    background: var(--surface-1);
}
.stRadio [role="radiogroup"] label {
    min-height: 2rem;
    padding: 0.35rem 0.7rem;
    border-radius: var(--radius-xs);
    background: transparent;
    transition: background var(--transition), color var(--transition);
}
.stRadio [role="radiogroup"] label:has(input:checked) {
    background: var(--accent-subtle);
    color: var(--accent-hover) !important;
}
@media (max-width: 640px) {
    .route-stat-strip { grid-template-columns: 1fr; }
    .profile-identity { align-items: flex-start; flex-direction: column; }
    .page-heading { min-height: 190px; padding: 1.75rem 1.25rem; border-radius: 22px; }
    .page-heading__mode { top: 1.25rem; left: 1.25rem; }
    .page-heading__signal { right: 1.5rem; top: 1.25rem; }
}
"""

# ── Components ───────────────────────────────────────────────────────────────

_COMPONENT_CSS = """
/* ── Buttons ──
   Every button variant is named explicitly, including the two form-submit
   testids. They are not covered by a [kind] attribute, so a selector list that
   left them out left Streamlit's own white-on-primaryColor label in place --
   1.98:1 on the accent, which is the one button in the app you most need to be
   able to read. */
[data-testid="stButton"] button,
[data-testid="stFormSubmitButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stLinkButton"] a,
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-primaryFormSubmit"],
[data-testid="stBaseButton-secondaryFormSubmit"] {
    font-family: var(--font) !important;
    font-size: 0.875rem !important;
    font-weight: var(--weight-medium) !important;
    letter-spacing: -0.005em;
    border-radius: var(--radius) !important;
    padding: 0.4375rem 0.875rem !important;
    min-height: 2.3125rem;
    border: 1px solid transparent !important;
    box-shadow: none !important;
    cursor: pointer;
    transition: background-color var(--transition), border-color var(--transition),
                color var(--transition), box-shadow var(--transition),
                transform var(--transition) !important;
}
[data-testid="stButton"] button:focus-visible,
[data-testid="stFormSubmitButton"] button:focus-visible {
    outline: 2px solid var(--accent) !important;
    outline-offset: 2px;
}

/* The label has to take the button's size, and it will not do it on its own.
   Streamlit renders a button's text as its own markdown paragraph nested three
   elements deep, and that container re-establishes 1rem -- so every label in
   the app rendered at 16px whatever size the button asked for, and every
   button-size rule above was decorative. The nav row measured 16px on a phone
   next to a 13px button box. `inherit` alone is not enough either: it inherits
   from the container, which is the thing setting 1rem. Both links in the chain
   have to be told to pass the size along. */
[data-testid="stButton"] [data-testid="stMarkdownContainer"],
[data-testid="stFormSubmitButton"] [data-testid="stMarkdownContainer"],
[data-testid="stDownloadButton"] [data-testid="stMarkdownContainer"],
[data-testid="stLinkButton"] [data-testid="stMarkdownContainer"],
[data-testid^="stBaseButton"] [data-testid="stMarkdownContainer"] {
    font-size: inherit !important;
    line-height: inherit !important;
}
[data-testid="stButton"] [data-testid="stMarkdownContainer"] p,
[data-testid="stFormSubmitButton"] [data-testid="stMarkdownContainer"] p,
[data-testid="stDownloadButton"] [data-testid="stMarkdownContainer"] p,
[data-testid="stLinkButton"] [data-testid="stMarkdownContainer"] p,
[data-testid^="stBaseButton"] [data-testid="stMarkdownContainer"] p {
    font-size: inherit !important;
    line-height: inherit !important;
    font-family: inherit !important;
    font-weight: inherit !important;
}

[data-testid="stButton"] button[kind="primary"],
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"] {
    background: var(--accent) !important;
    color: var(--accent-fg) !important;
    border-color: var(--accent) !important;
}
[data-testid="stButton"] button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover {
    background: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
    box-shadow: none !important;
}
[data-testid="stButton"] button[kind="primary"]:active,
[data-testid="stBaseButton-primary"]:active,
[data-testid="stBaseButton-primaryFormSubmit"]:active {
    background: var(--accent-active) !important;
    box-shadow: none !important;
    transform: translateY(0.5px);
}

[data-testid="stButton"] button[kind="secondary"],
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-secondaryFormSubmit"] {
    background: var(--surface-1) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
    box-shadow: var(--shadow-xs) !important;
}
[data-testid="stButton"] button[kind="secondary"]:hover,
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-secondaryFormSubmit"]:hover {
    background: var(--surface-2) !important;
    border-color: var(--border-strong) !important;
    color: var(--text-primary) !important;
}
[data-testid="stButton"] button[kind="secondary"]:active,
[data-testid="stBaseButton-secondary"]:active,
[data-testid="stBaseButton-secondaryFormSubmit"]:active {
    background: var(--surface-3) !important;
    transform: translateY(0.5px);
}

[data-testid="stButton"] button:disabled,
[data-testid="stBaseButton-primary"]:disabled,
[data-testid="stBaseButton-secondary"]:disabled,
[data-testid="stBaseButton-primaryFormSubmit"]:disabled,
[data-testid="stBaseButton-secondaryFormSubmit"]:disabled {
    opacity: 0.45;
    cursor: not-allowed;
}

/* A button label is a <p>, and the `p, li` rule above recoloured every one of
 * them to --text-secondary -- which is fine on a page and 1.13:1 on a filled
 * primary button. The label takes the button's own colour and type instead. */
[data-testid="stButton"] button p,
[data-testid="stFormSubmitButton"] button p,
[data-testid="stDownloadButton"] button p,
[data-testid="stBaseButton-primary"] p,
[data-testid="stBaseButton-secondary"] p,
[data-testid="stBaseButton-primaryFormSubmit"] p,
[data-testid="stBaseButton-secondaryFormSubmit"] p {
    color: inherit !important;
    font-family: var(--font) !important;
    font-size: inherit !important;
    font-weight: inherit !important;
    line-height: inherit !important;
    margin: 0 !important;
}

/* ── App navigation ──
   Scoped to the container marked with .nav-scope so ordinary buttons placed in
   columns (week paging, task toggles, admin actions) keep their own styling. */
.stApp [data-testid="stVerticalBlock"]:has(.nav-scope) { gap: 0.25rem; }
.stApp [data-testid="stVerticalBlock"]:has(.nav-scope) [data-testid="stHorizontalBlock"] {
    gap: 0.25rem !important;
}
.stApp [data-testid="stVerticalBlock"]:has(.nav-scope) [data-testid="stButton"] button {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border: 1px solid transparent !important;
    border-radius: var(--radius) !important;
    font-size: 0.8125rem !important;
    font-weight: var(--weight-medium) !important;
    padding: 0.375rem 0.25rem !important;
    min-height: 2.125rem !important;
    letter-spacing: -0.01em;
    white-space: nowrap;
    box-shadow: none !important;
}
.stApp [data-testid="stVerticalBlock"]:has(.nav-scope) [data-testid="stButton"] button:hover {
    background: var(--surface-2) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-subtle) !important;
}
.stApp [data-testid="stVerticalBlock"]:has(.nav-scope) [data-testid="stButton"] button[kind="primary"],
.stApp [data-testid="stVerticalBlock"]:has(.nav-scope) [data-testid="stBaseButton-primary"] {
    background: var(--accent-subtle) !important;
    color: var(--accent) !important;
    border-color: var(--accent-border) !important;
    font-weight: var(--weight-semibold) !important;
    box-shadow: none !important;
}

/* ── Segmented control (st.button_group) ── */
.stButtonGroup,
.stSegmentedControl {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius) !important;
    padding: 3px !important;
    gap: 2px !important;
}
.stButtonGroup label,
.stSegmentedControl label {
    border-radius: var(--radius-sm) !important;
    padding: 0.375rem 0.75rem !important;
    font-size: 0.8125rem !important;
    font-weight: var(--weight-medium) !important;
    color: var(--text-secondary) !important;
    transition: all var(--transition) !important;
}
.stButtonGroup label:hover,
.stSegmentedControl label:hover {
    background: var(--scrim) !important;
}
.stButtonGroup label[data-checked="true"],
.stSegmentedControl label[data-checked="true"] {
    background: var(--surface-1) !important;
    color: var(--text-primary) !important;
    font-weight: var(--weight-semibold) !important;
    box-shadow: var(--shadow-xs) !important;
}

/* ── Radio ── */
.stRadio [role="radiogroup"] {
    gap: 0.375rem !important;
    flex-wrap: wrap;
}
.stRadio label {
    border-radius: var(--radius) !important;
    background: var(--surface-1) !important;
    border: 1px solid var(--border-default) !important;
    margin: 0 !important;
    padding: 0.375rem 0.75rem !important;
    font-size: 0.8125rem !important;
    font-weight: var(--weight-medium) !important;
    transition: all var(--transition) !important;
    cursor: pointer !important;
}
.stRadio label:hover {
    background: var(--surface-2) !important;
    border-color: var(--border-strong) !important;
}
.stRadio label[data-checked="true"] {
    background: var(--accent-subtle) !important;
    border-color: var(--accent-border) !important;
}
.stRadio label[data-checked="true"] p {
    color: var(--accent) !important;
    font-weight: var(--weight-semibold) !important;
}

/* ── Checkbox / toggle ── */
.stCheckbox label {
    padding: 0.25rem 0 !important;
    font-size: 0.875rem !important;
}
.stCheckbox [data-baseweb="checkbox"] {
    border-radius: var(--radius-xs) !important;
    border-color: var(--border-strong) !important;
    background: var(--surface-1) !important;
}
.stCheckbox [data-checked="true"] [data-baseweb="checkbox"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}

/* ── Inputs ── */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stDateInput input,
.stSelectbox [data-baseweb="select"] > div,
.stTimeInput input {
    border: 1px solid var(--border-default) !important;
    border-radius: var(--radius) !important;
    padding: 0.4375rem 0.75rem !important;
    min-height: 2.3125rem;
    font-family: var(--font) !important;
    font-size: 0.875rem !important;
    background: var(--surface-1) !important;
    color: var(--text-primary) !important;
    box-shadow: none !important;
    transition: border-color var(--transition), box-shadow var(--transition) !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: var(--text-tertiary) !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus,
.stDateInput input:focus,
.stSelectbox [data-baseweb="select"] > div:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-subtle) !important;
}
.stTextArea textarea { line-height: 1.6; }
[data-testid="stNumberInputStepUp"],
[data-testid="stNumberInputStepDown"] {
    background: var(--surface-2) !important;
    color: var(--text-secondary) !important;
    border-color: var(--border-default) !important;
}
[data-testid="stNumberInputStepUp"]:hover,
[data-testid="stNumberInputStepDown"]:hover {
    background: var(--surface-3) !important;
    color: var(--text-primary) !important;
}

/* ── Selectbox ──
   Streamlit hangs the selected value off a bare <div value="..."> that is a
   flex item with overflow:hidden, and overflow:hidden zeroes a flex item's
   automatic minimum height. The value could therefore be squeezed below its own
   line box: on the parents page "Havva Nur" was rendering in an 8px box for
   14px type, so the name was unreadable. min-height is the whole fix. */
.stSelectbox div[value] {
    min-height: 1.375rem;
    display: flex;
    align-items: center;
}

/* ── Multiselect ──
   Its chips are the one place a control carries several values at once, and the
   Board's rounded geometry has to reach them or the control reads as a
   different product from every input beside it. */
.stMultiSelect [data-baseweb="tag"] {
    background: var(--accent-subtle) !important;
    border: 1px solid var(--accent-border) !important;
    border-radius: var(--radius-full) !important;
    color: var(--accent) !important;
    font-size: 0.8125rem !important;
    font-weight: var(--weight-medium) !important;
}
.stMultiSelect [data-baseweb="tag"] svg { fill: var(--accent) !important; }
.stMultiSelect [data-baseweb="tag"] + [data-baseweb="tag"] { margin-left: 0.25rem; }
.stMultiSelect div[role="combobox"] {
    background: var(--surface-1) !important;
    border: 1px solid var(--border-default) !important;
    border-radius: var(--radius) !important;
    min-height: 2.3125rem;
    color: var(--text-primary) !important;
}
/* The text a select draws for itself, including its placeholder. BaseWeb paints
 * the placeholder from its own rule at 60% of a near-white, and a rule on the
 * container cannot reach it because the leaf carries its own colour: in day mode
 * "Choose options" measured 1.02:1, white on the page. A descendant rule is the
 * only thing that lands, and the chips have to be re-asserted after it because
 * they are descendants too and should be the one coloured thing in the control. */
.stSelectbox [data-baseweb="select"] *,
[data-testid="stMultiSelect"] [data-baseweb="select"] * {
    color: var(--text-primary) !important;
}
.stMultiSelect [data-baseweb="tag"],
.stMultiSelect [data-baseweb="tag"] * {
    color: var(--accent) !important;
}
/* ── Dropdowns and the date calendar ──
   These float above the page in a portal, so they inherit nothing from the
   stylesheet's component rules and have to be told what they are. Streamlit
   paints a selected day in the accent, and its own white label on the accent is
   1.98:1 -- the same mistake the primary button was making. */
[data-baseweb="popover"],
[data-testid="stDateInput"] [data-baseweb="calendar"] {
    background: var(--surface-2) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-default) !important;
}
[data-baseweb="popover"] li,
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="menuitem"] {
    background: var(--surface-2) !important;
    color: var(--text-primary) !important;
    font-size: 0.875rem !important;
}
[data-baseweb="popover"] li:hover,
[data-baseweb="popover"] [role="option"]:hover { background: var(--surface-3) !important; }
[data-baseweb="popover"] li[aria-selected="true"],
[data-baseweb="popover"] [aria-selected="true"] {
    background: var(--accent) !important;
    color: var(--accent-fg) !important;
}

[data-testid="stDateInput"] [data-baseweb="calendar"] button,
[data-testid="stDateInput"] [data-baseweb="calendar"] [role="gridcell"] {
    color: var(--text-secondary) !important;
    border-radius: var(--radius-sm) !important;
}
[data-testid="stDateInput"] [data-baseweb="calendar"] button:hover {
    background: var(--surface-3) !important;
    color: var(--text-primary) !important;
}
[data-testid="stDateInput"] [data-baseweb="calendar"] button[aria-pressed="true"],
[data-testid="stDateInput"] [data-baseweb="calendar"] [aria-selected="true"] {
    background: var(--accent) !important;
    color: var(--accent-fg) !important;
    font-weight: var(--weight-semibold) !important;
}
[data-testid="stDateInput"] [data-baseweb="calendar"] [role="button"]:disabled {
    color: var(--text-tertiary) !important;
    opacity: 0.55;
}

/* ── File uploader ──
   A drop zone is a dashed invitation to interact, so it keeps the dashed edge
   and the accent tint rather than pretending to be a field. */
[data-testid="stFileUploaderDropzone"] {
    background: var(--surface-1) !important;
    border: 1px dashed var(--border-strong) !important;
    border-radius: var(--radius) !important;
    color: var(--text-secondary) !important;
    transition: border-color var(--transition), background-color var(--transition);
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--accent) !important;
    background: var(--accent-subtle) !important;
}
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzoneInstructions"] { color: var(--text-tertiary) !important; }
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] div { color: var(--text-secondary) !important; }

/* ── Toggle ──
   Streamlit draws the track with its own greys, which on a near-black surface
   is a light bar with a light thumb on it. */
[data-testid="stToggle"] label { color: var(--text-secondary) !important; }
[data-testid="stToggle"] [data-baseweb="checkbox"] {
    background: var(--surface-3) !important;
    border-color: var(--border-strong) !important;
}
[data-testid="stToggle"] [data-checked="true"] [data-baseweb="checkbox"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}
[data-testid="stToggle"] [data-baseweb="checkbox"] span { background: var(--surface-1) !important; }
[data-testid="stToggle"] [data-checked="true"] [data-baseweb="checkbox"] span {
    background: var(--accent-fg) !important;
}

/* ── Slider ── */
[data-testid="stSlider"] [data-baseweb="slider"] { background: var(--surface-3) !important; }
[data-testid="stSlider"] [role="slider"] { background: var(--accent) !important; }
[data-testid="stSlider"] [data-testid="stTickBarMin"],
[data-testid="stSlider"] [data-testid="stTickBarMax"] { color: var(--text-tertiary) !important; }

/* ── Progress ── */
[data-testid="stProgress"] > div > div { background: var(--surface-3) !important; }
[data-testid="stProgress"] [role="progressbar"] { background: var(--accent) !important; }

/* ── Form ── */
[data-testid="stForm"] {
    background: var(--surface-1) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.5rem !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: var(--surface-1) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius) !important;
    box-shadow: none !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary,
.streamlit-expanderHeader {
    background: var(--surface-2) !important;
    color: var(--text-primary) !important;
    font-size: 0.875rem !important;
    font-weight: var(--weight-semibold) !important;
    border-radius: var(--radius) !important;
    transition: background-color var(--transition) !important;
}
[data-testid="stExpander"] summary:hover,
.streamlit-expanderHeader:hover {
    background: var(--surface-3) !important;
    color: var(--text-primary) !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    border-top: 1px solid var(--border-subtle);
}

/* ── Alerts ──
   Previously every severity collapsed onto the same flat card colour. Each
   severity now gets its own tinted surface and matching accent bar. */
[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border-subtle) !important;
    border-left: 3px solid var(--accent) !important;
    background: var(--surface-1) !important;
    color: var(--text-primary) !important;
    padding: 0.75rem 1rem !important;
    box-shadow: var(--shadow-xs) !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] span,
[data-testid="stAlert"] div { color: var(--text-primary) !important; }
[data-testid="stAlert"]:has([data-testid="stIconMaterialSuccess"]) {
    background: var(--success-subtle) !important;
    border-color: var(--success-border) !important;
    border-left-color: var(--success) !important;
}
[data-testid="stAlert"]:has([data-testid="stIconMaterialWarning"]) {
    background: var(--warning-subtle) !important;
    border-color: var(--warning-border) !important;
    border-left-color: var(--warning) !important;
}
[data-testid="stAlert"]:has([data-testid="stIconMaterialError"]) {
    background: var(--danger-subtle) !important;
    border-color: var(--danger-border) !important;
    border-left-color: var(--danger) !important;
}

/* ── Metric ── */
[data-testid="stMetric"] {
    background: var(--surface-1) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius) !important;
    padding: 0.875rem 1rem !important;
    box-shadow: var(--shadow-xs) !important;
}
[data-testid="stMetric"] label {
    color: var(--text-secondary) !important;
    font-size: 0.8125rem !important;
    font-weight: var(--weight-medium) !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-mono) !important;
    font-weight: var(--weight-semibold) !important;
    color: var(--text-primary) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface-1) !important;
    border-right: 1px solid var(--border-subtle) !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { padding: 1.25rem; }

/* ── Dataframe / table ── */
.stDataFrame, [data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius) !important;
    overflow: hidden !important;
}

/* ── Cards ── */
.card {
    background: var(--surface-1);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.5rem;
    box-shadow: none;
    transition: background-color var(--transition-slow), border-color var(--transition-slow);
    animation: fadeIn 320ms var(--ease-out);
}
/* Hover is a step up the surface ladder. It used to be a shadow, which is a cue
 * from the light theme: on a near-black page a drop shadow is invisible, so the
 * lift has to come from the surface itself. */
.card:hover {
    background: var(--surface-2);
    border-color: var(--border-default);
}
.card--hover { cursor: pointer; }
.card--hover:hover { border-color: var(--accent-border); }
.card--pad-sm { padding: 0.875rem 1rem; }
.card--center { text-align: center; }
.card--stat {
    border-left: 3px solid var(--accent);
    position: relative;
    overflow: hidden;
}
.card--progress { border-left: 3px solid var(--success); }
.card--danger { border-left: 3px solid var(--danger); }
.card--success { border-left: 3px solid var(--success); }
.card--warning { border-left: 3px solid var(--warning); }
.card--info { border-left: 3px solid var(--info); }
.card .value {
    font-family: var(--font-mono);
    font-size: 1.875rem;
    font-weight: var(--weight-bold);
    color: var(--text-primary);
    line-height: 1.15;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.02em;
}
.card .label {
    font-size: 0.8125rem;
    color: var(--text-secondary);
    font-weight: var(--weight-medium);
}
.card .icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
.card--stat hr { margin: 0.75rem 0; }

/* ── Metric card (legacy class name, maps to card--stat) ── */
.metric-card {
    background: var(--surface-1) !important;
    border: 1px solid var(--border-subtle) !important;
    border-left: 3px solid var(--accent) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.25rem !important;
    box-shadow: none !important;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: background-color var(--transition-slow), border-color var(--transition-slow);
}
.metric-card:hover {
    background: var(--surface-2) !important;
    border-color: var(--border-default) !important;
}
.metric-card h3 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: var(--weight-medium);
    color: var(--text-secondary);
}
.metric-card .value {
    font-family: var(--font-mono);
    font-size: 2rem;
    font-weight: var(--weight-bold);
    color: var(--text-primary);
    margin: 0.375rem 0;
    line-height: 1.15;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.02em;
}
.metric-card .label {
    font-size: 0.8125rem;
    color: var(--text-secondary);
    font-weight: var(--weight-medium);
}

/* ── Task items ── */
.task-item {
    background: var(--surface-1);
    border: 1px solid var(--border-subtle);
    border-left: 3px solid var(--accent);
    border-radius: 18px;
    padding: 1rem 1.1rem;
    margin: 0.375rem 0;
    box-shadow: none;
    color: var(--text-primary);
    font-size: 0.875rem;
    animation: fadeIn 300ms var(--ease-out);
    transition: transform var(--transition), background-color var(--transition), border-color var(--transition);
}
.task-item:hover { background: var(--surface-2); border-color: var(--accent-border); transform: translateX(3px); }
.task-item p { color: var(--text-secondary); }
.task-item.task-done { border-left-color: var(--success); }
.task-item.task-overdue { border-left-color: var(--danger); }
.task-item.task-done .row-title { color: var(--text-secondary); }

/* ── Rows: a flex line with a leading label and trailing meta ── */
.row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
}
.row--top { align-items: flex-start; }
.row-title {
    font-weight: var(--weight-semibold);
    color: var(--text-primary);
    min-width: 0;
    overflow-wrap: anywhere;
}
.row-title h4 { margin: 0; font-size: 0.9375rem; font-weight: var(--weight-semibold); }
.row-meta {
    color: var(--text-secondary);
    font-size: 0.8125rem;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
}
.row-faint {
    color: var(--text-tertiary);
    font-size: 0.75rem;
    white-space: nowrap;
}
.row-end { text-align: right; white-space: nowrap; }
.row-stack { display: flex; flex-direction: column; gap: 0.125rem; }
.progress-line { margin-top: 0.625rem; }
.progress-line span {
    font-size: 0.8125rem;
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
}
.writer-line {
    margin: 0.3125rem 0 0;
    font-size: 0.8125rem;
    color: var(--text-tertiary);
}
.assigned-line {
    margin-top: 0.375rem;
    font-size: 0.75rem;
    color: var(--text-tertiary);
}

/* ── Banners ── */
.banner {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-radius: var(--radius);
    border: 1px solid var(--border-subtle);
    background: var(--surface-2);
    color: var(--text-primary);
    font-size: 0.875rem;
    margin-top: 0.5rem;
}
.banner--gold {
    background: var(--gold-subtle);
    border-color: var(--gold-border);
    color: var(--text-primary);
}
.banner--warn {
    background: var(--danger-subtle);
    border-color: var(--danger-border);
}
.banner--ok {
    background: var(--success-subtle);
    border-color: var(--success-border);
}
.banner--info {
    background: var(--info-subtle);
    border-color: var(--info-border);
}
.banner--rank {
    display: block;
    text-align: center;
    padding: 0.875rem 1rem;
    background: linear-gradient(135deg, var(--accent-subtle) 0%, var(--surface-2) 100%);
    border-color: var(--accent-border);
}
.banner--rank .rank-icon { font-size: 2.25rem; display: block; line-height: 1.1; }
.banner--rank .rank-name {
    font-size: 1.0625rem;
    font-weight: var(--weight-semibold);
    color: var(--text-primary);
}

/* ── Entity rows (admin lists) ── */
.entity-row {
    display: flex;
    align-items: center;
    gap: 0.875rem;
    padding: 0.5rem 0;
}
.entity-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    width: 2.5rem;
    height: 2.5rem;
    border-radius: var(--radius);
    background: var(--accent-subtle);
    border: 1px solid var(--accent-border);
    font-size: 1.125rem;
}
.entity-icon--tall { height: 4rem; }
.entity-title {
    font-size: 0.9375rem;
    font-weight: var(--weight-semibold);
    color: var(--text-primary);
}
.entity-meta {
    color: var(--text-tertiary);
    font-size: 0.75rem;
    line-height: 1.5;
}

/* ── Week heading ── */
.week-heading {
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    text-align: center;
    color: var(--accent);
    font-size: 1.0625rem;
    font-weight: var(--weight-semibold);
    letter-spacing: -0.01em;
    margin: 0;
}
.week-range {
    color: var(--text-secondary);
    font-size: 0.8125rem;
    font-weight: var(--weight-medium);
}

/* ── Data table (prayer report) ── */
.th {
    font-size: 0.8125rem;
    font-weight: var(--weight-semibold);
    color: var(--text-primary);
    padding-bottom: 0.5rem;
}
.td {
    font-size: 0.875rem;
    color: var(--text-secondary);
    padding: 0.1875rem 0;
}
.count {
    font-family: var(--font-mono);
    font-weight: var(--weight-semibold);
    font-variant-numeric: tabular-nums;
    color: var(--text-primary);
}
.count--missed { color: var(--danger); }
.count--ok { color: var(--success); }
.count--total { color: var(--text-primary); font-weight: var(--weight-semibold); }

/* ── Utility text ── */
.num {
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.01em;
}
.center { text-align: center; }
.muted { color: var(--text-secondary); }
.faint { color: var(--text-tertiary); }
.strong { font-weight: var(--weight-semibold); color: var(--text-primary); }
.text-accent { color: var(--accent); }
.text-success { color: var(--success); }
.text-danger { color: var(--danger); }
.text-gold { color: var(--gold); }
.strike { text-decoration: line-through; opacity: 0.6; }
.dim { opacity: 0.6; }
.mt-sm { margin-top: 0.5rem; }

/* ── Comment thread (meeting) ── */
.comment {
    border-left: 2px solid var(--border-default);
    padding-left: 0.75rem;
    margin: 0.5rem 0;
}
.comment-meta {
    color: var(--text-tertiary);
    font-size: 0.75rem;
}

/* ── Status badges ── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.125rem 0.5rem;
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: var(--weight-semibold);
    letter-spacing: 0.01em;
    white-space: nowrap;
}
.status-backlog {
    background: var(--surface-3);
    color: var(--text-secondary);
    border: 1px solid var(--border-default);
}
.status-in-progress {
    background: var(--warning-subtle);
    color: var(--warning);
    border: 1px solid var(--warning-border);
}
.status-done {
    background: var(--success-subtle);
    color: var(--success);
    border: 1px solid var(--success-border);
}

/* ── Progress bars ── */
.book-progress-bar {
    height: 6px;
    background: var(--surface-3);
    border-radius: var(--radius-full);
    overflow: hidden;
    margin: 0.625rem 0;
}
.book-progress-fill {
    height: 100%;
    background: var(--accent);
    border-radius: var(--radius-full);
    transition: width 600ms cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}
.book-progress-fill::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, var(--shine), transparent);
    animation: shimmer 2.4s infinite;
}

/* ── Avatar ── */
.avatar-circle {
    border-radius: 50%;
    object-fit: cover;
    border: 1px solid var(--border-default);
    box-shadow: none;
    transition: transform var(--transition), border-color var(--transition);
}
.avatar-circle:hover {
    transform: scale(1.03);
    border-color: var(--border-strong);
}
.avatar-fallback {
    display: flex;
    align-items: center;
    justify-content: center;
    /* Flat accent, not an accent-to-info gradient: the Board has one accent. */
    background: var(--accent);
    color: var(--on-gradient);
    border: none;
    box-shadow: none;
    line-height: 1;
}

/* ── Achievement badge ── */
.achievement-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.375rem 0.75rem;
    background: var(--gold-subtle);
    border: 1px solid var(--gold-border);
    border-radius: var(--radius-full);
    margin: 0.25rem 0.25rem 0.25rem 0;
    font-weight: var(--weight-semibold);
    font-size: 0.8125rem;
    color: var(--gold);
    animation: badgePop 380ms var(--ease-out);
}

/* ── Metric display ── */
.metric-display { text-align: center; padding: 1rem; }
.metric-display .metric-value {
    font-family: var(--font-mono);
    font-size: 2.125rem;
    font-weight: var(--weight-display);
    color: var(--text-primary);
    line-height: 1.15;
    font-variant-numeric: tabular-nums;
}
.metric-display .metric-label {
    font-size: 0.8125rem;
    color: var(--text-secondary);
    font-weight: var(--weight-medium);
    margin-top: 0.125rem;
}

/* ── Info boxes (helper-rendered messages) ── */
.info-box {
    padding: 0.75rem 1rem;
    border-radius: var(--radius);
    border: 1px solid var(--border-subtle);
    font-weight: var(--weight-medium);
    font-size: 0.875rem;
}
.info-box--success { background: var(--success-subtle); border-color: var(--success-border); color: var(--success); }
.info-box--error { background: var(--danger-subtle); border-color: var(--danger-border); color: var(--danger); }
.info-box--warning { background: var(--warning-subtle); border-color: var(--warning-border); color: var(--warning); }
.info-box--info { background: var(--info-subtle); border-color: var(--info-border); color: var(--info); }

/* ── Dividers ── */
.divider-gradient {
    border: 0;
    height: 1px;
    /* A hairline that fades out at both ends. It used to be a 2px accent line,
     * which is a section break the Board does not use anywhere. */
    background: linear-gradient(90deg,
        transparent 0%,
        var(--border-default) 50%,
        transparent 100%);
    margin: 1.75rem 0;
}

/* ── Motion ── */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes badgePop {
    0% { transform: scale(0.85); opacity: 0; }
    70% { transform: scale(1.04); }
    100% { transform: scale(1); opacity: 1; }
}
@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

@media (prefers-reduced-motion: reduce) {
    .card, .task-item, .achievement-badge, .book-progress-fill,
    .book-progress-fill::after, [data-testid="stButton"] button {
        animation: none !important;
        transition: none !important;
    }
}
"""

# ── Board chrome ─────────────────────────────────────────────────────────────
# ── Chrome the component rules never reached ────────────────────────────────
#
# Everything in here is token-driven and therefore correct in both modes without
# a word about day or night. That is the point: these were not day-mode bugs.
# They were elements the stylesheet had never styled at all, which nobody could
# see because Streamlit's own dark values happened to be the right colour for a
# dark page. A second palette is what exposed them -- and the honest reading is
# that the day mode is not a second design, it is a second lighting, and anything
# that only looked right under one lighting was never styled.
#
# Each entry below was found by tools/audit.py's island check in day mode, which
# reports every element whose background is far darker than the page it is on.

_CHROME_CSS = """
/* The header is a full-width bar painted from the theme's background. On a dark
 * page it is invisible; on a light page it is a dark stripe across the top of
 * every page. The page colour is the right answer in both, and it is what the
 * rest of the app already assumes. */
[data-testid="stHeader"] {
    background: var(--surface-0) !important;
}
[data-testid="stToolbar"] {
    background: var(--surface-0) !important;
}

/* The segmented control. Streamlit renders st.segmented_control as a row of
 * <button kind="..."> inside a button-group, and the rules in _COMPONENT_CSS
 * were written for the <label> elements it used to render instead -- so the
 * container was styled and the segments inside it were not, leaving Streamlit's
 * near-black default on the page. The kind attribute is the stable hook: it is
 * part of the element's contract rather than an emotion class name that changes
 * with every Streamlit release. */
[data-baseweb="button-group"] [kind="segmented_control"] {
    background: var(--surface-1) !important;
    color: var(--text-secondary) !important;
    border: 1px solid transparent !important;
    border-radius: var(--radius-sm) !important;
    font-weight: var(--weight-medium) !important;
}
[data-baseweb="button-group"] [kind="segmented_control"]:hover {
    background: var(--surface-2) !important;
    color: var(--text-primary) !important;
}
[data-baseweb="button-group"] [kind="segmented_controlActive"],
[data-baseweb="button-group"] [kind="segmented_controlActive"]:hover {
    background: var(--accent-subtle) !important;
    color: var(--accent) !important;
    border-color: var(--accent-border) !important;
    font-weight: var(--weight-semibold) !important;
}
[data-baseweb="button-group"] [kind="segmented_control"] p,
[data-baseweb="button-group"] [kind="segmented_controlActive"] p {
    color: inherit !important;
    font-size: 0.8125rem !important;
}

/* The radio's own dot. The label around it was styled in _COMPONENT_CSS and the
 * dot was not, so a selected radio drew Streamlit's theme-primary circle next to
 * a label painted from our tokens. The dot is a div whose depth inside the label
 * differs depending on whether it is checked, so both are covered by painting
 * every descendant of the mark rather than guessing at a child index. */
.stRadio [data-baseweb="radio"] div {
    background: var(--surface-0) !important;
    border-color: var(--border-strong) !important;
}
.stRadio label[data-checked="true"] [data-baseweb="radio"] div,
.stRadio [data-baseweb="radio"] div:has(svg) {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}

/* The box around a text field. _COMPONENT_CSS styles the <input> itself, but
 * Streamlit draws the field on a wrapper and the input sits on top of it, so on
 * a light page the light input sat inside a dark box. Number, date and time
 * fields share the same wrapper, which is why one rule covers all of them. */
[data-testid="stTextInputRootElement"],
[data-testid="stTextAreaRootElement"],
[data-baseweb="input"],
[data-baseweb="base-input"] {
    background: var(--surface-1) !important;
    border-color: var(--border-default) !important;
}
[data-testid="stTextInputRootElement"] input,
[data-testid="stTextAreaRootElement"] textarea {
    background: transparent !important;
}
/* The select box's own frame, and the chevron in it. stMultiSelect draws the
 * same widget with a different testid, so it is named here too rather than
 * being left as a dark dropdown on a light page. */
.stSelectbox [data-baseweb="select"] > div,
.stSelectbox [data-baseweb="select"],
[data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] {
    background: var(--surface-1) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
}
.stSelectbox svg,
[data-testid="stMultiSelect"] svg {
    color: var(--text-secondary) !important;
    fill: var(--text-secondary) !important;
}

/* The tick inside a checked checkbox. The box is filled from --accent by the
 * rules above, but the glyph inside it is painted separately and kept the theme's
 * primary colour -- so on a light page a white box held a night-cyan tick. It is
 * a mark on a filled surface, so it takes the label colour, not a second one. */
.stCheckbox [data-baseweb="checkbox"] span {
    background: transparent !important;
}
.stCheckbox [data-baseweb="checkbox"] svg {
    fill: var(--accent-fg) !important;
    color: var(--accent-fg) !important;
}

/* The material icon Streamlit draws beside an alert, an expander or a metric
 * takes its colour from the theme's primary colour, so it stayed the night
 * accent while everything around it went to day. */
[data-testid^="stIconMaterial"] {
    color: var(--accent) !important;
}
[data-testid="stAlert"] svg {
    fill: currentColor !important;
}
"""


# The Board's host-side furniture: the flag above the canvas and the full-bleed
# layout the canvas needs. It used to be a style block inside app.py's board
# branch, which meant the Board's colours were written twice -- once here in
# oklch and once in the shell -- and the shell's copy was the one that drifted.
# The layout half has to stay where it is: it is scoped to the board branch,
# because the other pages keep the padded body.

_BOARD_CSS = """
.board-flag {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: var(--weight-semibold);
    color: var(--text-secondary);
}
.board-flag b {
    color: var(--text-primary);
    font-weight: var(--weight-bold);
    letter-spacing: -0.01em;
}
.board-flag span {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-tertiary);
}
.board-flag__dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--success);
}
"""

# ── Kiosk ────────────────────────────────────────────────────────────────────
# The screensaver and adhan overlay render on their own near-black backdrop
# regardless of the app theme, so they intentionally use literal colors instead
# of theme tokens. Do not re-point these at tokens: the layout, z-index stack
# and pointer-events here are load-bearing for the adhan runtime.

_KIOSK_CSS = """
.kiosk-screensaver {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 99999;
    background: rgba(0, 0, 0, 0.92);
    display: flex;
    align-items: center;
    justify-content: center;
    animation: kioskFadeIn 0.8s ease-out;
    cursor: pointer;
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
}
.kiosk-active header[data-testid="stHeader"],
.kiosk-active [data-testid="stToolbar"] {
    display: none !important;
}
.kiosk-screensaver-images {
    background: #000;
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}
.kiosk-screensaver-images--fallback {
    background: radial-gradient(circle at 50% 35%, rgba(0, 199, 255, 0.16), transparent 42%), #0b1018;
    color: #f4f5f8;
    font: 600 1.4rem var(--font);
    letter-spacing: 0.04em;
}
.kiosk-screensaver-img {
    position: absolute;
    max-width: 90vw;
    max-height: 90vh;
    object-fit: contain;
    border-radius: 12px;
    opacity: 0;
    transition: opacity 1.5s ease-in-out;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}
.kiosk-screensaver-img.active { opacity: 1; }
.kiosk-screensaver-footer {
    position: fixed;
    bottom: 28px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 100000;
    background: rgba(0, 0, 0, 0.55);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    color: #fff;
    font-family: var(--font);
    font-size: 1.15em;
    font-weight: var(--weight-medium);
    padding: 12px 28px;
    /* Reads as a soft pill on one line and as a rounded panel once the items
     * wrap, instead of turning into a 132px-tall stadium. */
    border-radius: 28px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px 18px;
    /* The pill must never clip. Each item keeps itself on one line, but the
     * row is allowed to wrap: on an iPad portrait the three items need ~980px
     * and only ~754px is available, so a nowrap container silently cut the
     * weather off the end. */
    flex-wrap: wrap;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35), 0 0 0 1px rgba(255, 255, 255, 0.08);
    animation: kioskFadeIn 1s ease-out;
    letter-spacing: 0.3px;
    max-width: 92vw;
}
.kiosk-screensaver-footer .kiosk-ss-time {
    color: #fff;
    font-weight: var(--weight-semibold);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
.kiosk-screensaver-footer .kiosk-ss-prayer {
    color: #A5B4FC;
    font-weight: var(--weight-semibold);
    white-space: nowrap;
}
.kiosk-screensaver-footer .kiosk-ss-weather {
    color: #7DD3FC;
    font-weight: var(--weight-semibold);
    white-space: nowrap;
}
.kiosk-screensaver-footer .kiosk-audio-status {
    position: static;
    transform: none;
}
@keyframes kioskFadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* The Kiosk runtime test controls. Plain buttons rather than st.button: the
 * runtime dispatches them directly on the real tap, so the test needs no
 * Streamlit rerun and no flag to be polled for. Colours come from the app
 * tokens so they match the rest of Admin. */
.kiosk-test-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
    margin: 0.75rem 0 0.35rem;
}
.kiosk-test-btn {
    font: 600 0.85rem var(--font);
    color: var(--text-primary);
    background: var(--surface-2);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-sm);
    padding: 0.55rem 1.1rem;
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease, transform 0.1s ease;
    -webkit-tap-highlight-color: transparent;
}
.kiosk-test-btn:hover { border-color: var(--accent-border); background: var(--surface-1); }
.kiosk-test-btn:active { transform: translateY(1px); }
.kiosk-test-btn--primary {
    color: var(--accent-fg);
    background: var(--accent);
    border-color: var(--accent);
}
.kiosk-test-btn--primary:hover { background: var(--accent-hover); border-color: var(--accent-hover); }
.kiosk-test-status {
    display: inline-flex;
    flex-wrap: wrap;
    gap: 6px 14px;
    font: 0.72rem var(--font-mono);
    color: var(--text-tertiary);
}
.kiosk-test-status b { font-weight: 500; }
.kiosk-test-status [data-tone="ok"] { color: var(--accent); }
.kiosk-test-status [data-tone="warn"] { color: #F59E0B; }
/* A preview is the user actively testing the display, not a wall tablet going
 * to sleep, so it is marked and held rather than timing out under the pointer. */
.kiosk-screensaver--preview { box-shadow: inset 0 0 0 3px rgba(0, 199, 255, 0.35); }
.kiosk-screensaver-footer .kiosk-ss-preview {
    color: #7DD3FC;
    font-weight: var(--weight-semibold);
    white-space: nowrap;
}

.kiosk-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 16px;
    border-radius: 100px;
    font-size: 0.85em;
    font-weight: var(--weight-semibold);
}
.kiosk-status.active {
    background: rgba(16, 185, 129, 0.1);
    color: #10B981;
    border: 1px solid rgba(16, 185, 129, 0.2);
}
.kiosk-status.inactive {
    background: rgba(239, 68, 68, 0.1);
    color: #EF4444;
    border: 1px solid rgba(239, 68, 68, 0.2);
}
.kiosk-status.warning {
    background: rgba(245, 158, 11, 0.1);
    color: #F59E0B;
    border: 1px solid rgba(245, 158, 11, 0.2);
}

.kiosk-audio-status {
    position: fixed;
    top: 30px;
    right: 24px;
    z-index: 100001;
    padding: 12px 20px;
    border-radius: 100px;
    font-family: var(--font);
    font-size: 0.95em;
    font-weight: var(--weight-semibold);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    animation: kioskFadeIn 0.4s ease-out;
    pointer-events: none;
}
.kiosk-audio-status.ok { background: rgba(16, 185, 129, 0.95); color: #fff; }
.kiosk-audio-status.warn { background: rgba(245, 158, 11, 0.95); color: #fff; }
.kiosk-audio-status.err { background: rgba(239, 68, 68, 0.95); color: #fff; }

/* Stays on screen until a gesture unlocks the media session. A 6-second toast
 * expires long before anyone notices on a wall tablet.
 *
 * z-index sits just above the app but *below* every kiosk layer: the
 * screensaver (99999), its footer (100000) and the audio-status chip (100001).
 * The screensaver is an ambient fullscreen display and should not get a banner
 * stamped over it. Any tap still unlocks, because the screensaver's own gesture
 * handler dismisses it and primes audio at the same time, so the hint is only
 * needed on an ordinary page. */
.kiosk-unlock-hint {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 99998;
    padding: 12px 22px;
    border-radius: 100px;
    background: rgba(245, 158, 11, 0.96);
    color: #1A1300;
    font-family: var(--font);
    font-size: 0.95em;
    font-weight: var(--weight-semibold);
    white-space: nowrap;
    max-width: 92vw;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    animation: kioskFadeIn 0.4s ease-out;
    pointer-events: none;
}
@media (max-width: 768px) {
    .kiosk-unlock-hint {
        font-size: 0.8em;
        padding: 10px 16px;
        white-space: normal;
        text-align: center;
        bottom: 16px;
    }
}

/* Live runtime readout, rendered into the page by kiosk.js when the Admin →
 * Kiosk tab asks for it. Deliberately self-contained: it is written by the
 * runtime, not by Streamlit, so it must not depend on app tokens.
 *
 * This one is intentionally topmost (100003) - it is an explicit, temporary
 * debugging aid, and it is useless if a screensaver is covering it. */
.kiosk-diagnostics {
    position: fixed;
    top: 20px;
    left: 20px;
    z-index: 100003;
    min-width: 340px;
    max-width: 92vw;
    padding: 16px 18px;
    border-radius: 14px;
    background: rgba(12, 12, 14, 0.95);
    color: #fff;
    font-family: var(--font);
    font-size: 0.9em;
    line-height: 1.5;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(255, 255, 255, 0.1);
    pointer-events: none;
}
@media (max-width: 768px) {
    .kiosk-diagnostics { min-width: 0; font-size: 0.8em; padding: 12px 14px; }
}
"""

# ── Responsive ───────────────────────────────────────────────────────────────

_RESPONSIVE_CSS = """
@media (max-width: 1200px) {
    .stApp [data-testid="stVerticalBlock"]:has(.nav-scope) [data-testid="stButton"] button {
        font-size: 0.75rem !important;
        padding: 0.375rem 0.125rem !important;
    }
}
@media (max-width: 768px) {
    .kiosk-screensaver-footer {
        font-size: 0.9em;
        padding: 10px 18px;
        gap: 6px 10px;
        bottom: 16px;
        border-radius: 16px;
    }
    .kiosk-screensaver-footer .kiosk-ss-weather,
    .kiosk-screensaver-footer .kiosk-ss-prayer { white-space: normal; }

    .top-navbar {
        padding: 0 0 0.625rem;
        flex-wrap: wrap;
    }
    .navbar-brand h1 { font-size: 1.0625rem; }
    .navbar-brand h1 { display: none !important; }
    .navbar-brand::after {
        content: "Family Task";
        color: var(--text-primary);
        font-size: 0.78rem;
        font-weight: var(--weight-semibold);
    }
    .navbar-brand span,
    .navbar-actions .nav-date { display: none; }

    .stApp [data-testid="stHorizontalBlock"] {
        display: block !important;
        flex-direction: column !important;
        gap: 0.75rem !important;
    }
    .stApp [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        width: 100% !important;
        flex: 1 1 auto !important;
    }
    .stApp [data-testid="stHorizontalBlock"]:has(.profile-identity) {
        display: block !important;
    }
    .stApp [data-testid="stHorizontalBlock"]:has(.profile-identity) > [data-testid="stColumn"] {
        width: 100% !important;
    }

    .stApp [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .nav-scope) > [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.3rem !important;
    }
    .stApp [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .nav-scope) > [data-testid="stLayoutWrapper"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"] {
        width: auto !important;
        min-width: 0 !important;
        flex: none !important;
    }

    .stApp [data-testid="stVerticalBlock"]:has(.nav-scope) [data-testid="stButton"] button {
        font-size: 0.6875rem !important;
        padding: 0.3125rem 0.125rem !important;
    }
    .card { padding: 1rem; }
    .metric-card { padding: 1rem !important; }
    .task-item { padding: 0.75rem 0.875rem; }
    .metric-display { padding: 0.75rem; }
}
"""


def _build_css() -> str:
    return "\n".join(
        (
            _FONT_IMPORT,
            _SHARED_TOKENS,
            # Both palettes are in every stylesheet, always. Selecting a mode is a
            # single attribute on <html> and nothing else, so flipping it costs a
            # style recalculation instead of a rerun, a remount, or a second copy
            # of the rules. The consequence to keep in mind is that --surface-1
            # and friends are not a single value any more: they are a pair that
            # depends on the mode in force. Anything reading them at runtime has
            # to ask which mode it is in, which is why the mode also travels in
            # the Board payload and why the one-design test reads a palette per
            # mode rather than one for the file.
            _TOKENS,
            _TOKENS_DAY,
            _BASE_CSS,
            _NAV_CSS,
            _COMPONENT_CSS,
            _CHROME_CSS,
            _BOARD_CSS,
            _KIOSK_CSS,
            _RESPONSIVE_CSS,
        )
    )


def apply_custom_styles():
    st.markdown(f"<style>{_build_css()}</style>", unsafe_allow_html=True)


# ── Presentation helpers ─────────────────────────────────────────────────────
# Signatures and behaviour are unchanged; these only render through the tokens
# above instead of inline hex values.

def styled_card(title: str, content: str, emoji: str = ""):
    st.markdown(
        f"""
        <div class="card">
            <h3>{emoji} {title}</h3>
            <p>{content}</p>
        </div>
    """,
        unsafe_allow_html=True,
    )


def success_message(message: str, emoji: str = "✅"):
    st.markdown(
        f'<div class="info-box info-box--success">{emoji} {message}</div>',
        unsafe_allow_html=True,
    )


def error_message(message: str, emoji: str = "❌"):
    st.markdown(
        f'<div class="info-box info-box--error">{emoji} {message}</div>',
        unsafe_allow_html=True,
    )


def warning_message(message: str, emoji: str = "⚠️"):
    st.markdown(
        f'<div class="info-box info-box--warning">{emoji} {message}</div>',
        unsafe_allow_html=True,
    )


def info_message(message: str, emoji: str = "ℹ️"):
    st.markdown(
        f'<div class="info-box info-box--info">{emoji} {message}</div>',
        unsafe_allow_html=True,
    )


def metric_card(title: str, value: str, subtitle: str = "", emoji: str = ""):
    st.markdown(
        f"""
        <div class="card card--stat card--center">
            <div class="icon">{emoji}</div>
            <h3 class="muted" style="margin:0;font-size:0.875rem;font-weight: var(--weight-medium);">{title}</h3>
            <div class="value">{value}</div>
            <div class="label">{subtitle}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )


def styled_section_header(title: str, emoji: str = ""):
    st.markdown(
        f"""
        <h2 style="border-bottom:1px solid var(--border-subtle);padding-bottom:0.625rem;
                   margin-bottom:1.25rem;color:var(--text-primary);">
            {emoji} {title}
        </h2>
    """,
        unsafe_allow_html=True,
    )


def divider_gradient():
    st.markdown('<hr class="divider-gradient">', unsafe_allow_html=True)


def status_badge(status: str):
    badge_classes = {
        "Backlog": "status-badge status-backlog",
        "In Progress": "status-badge status-in-progress",
        "Done": "status-badge status-done",
    }
    css_class = badge_classes.get(status, "status-badge")
    st.markdown(f'<span class="{css_class}">{status}</span>', unsafe_allow_html=True)


def avatar_image(image_url: str, width: int = 120):
    if image_url:
        st.markdown(
            f'<img src="{image_url}" class="avatar-circle" width="{width}" height="{width}" />',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="avatar-circle avatar-fallback" style="width:{width}px;height:{width}px;'
            f'font-size:{width // 2.5}px;">👤</div>',
            unsafe_allow_html=True,
        )


def achievement_badge(icon: str, label: str):
    st.markdown(
        f'<span class="achievement-badge">{icon} {label}</span>',
        unsafe_allow_html=True,
    )
