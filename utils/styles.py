"""Design system for the Family Task Tracker UI.

Everything visual lives here as plain CSS strings so the stylesheet stays
readable and diffable. Only the palette block is swapped per theme, which
means every component rule below it is written once and works in both light
and dark mode.

Layout note: Streamlit components live in the same document as this stylesheet,
so components reference semantic custom properties (``var(--surface-1)``)
instead of hardcoded colors. The board is the exception: it is a separate
document with its own visual system in ``static/board/board.css``, and inherits
nothing from here.
"""

import streamlit as st

# ── Design tokens ────────────────────────────────────────────────────────────
# NOTE: the @import below must stay the first rule in the emitted stylesheet or
# the browser discards it and the app silently falls back to system fonts.

_FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Inter:wght@300;400;475;500;625;700&"
    "family=JetBrains+Mono:wght@400;600&display=swap');"
)

# Theme-independent scales: type, radii, motion, layout.
_SHARED_TOKENS = """
:root {
    --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
            'Helvetica Neue', Arial, sans-serif;
    --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;

    /* Inter is a variable font, so mid weights are real weights rather than
     * faux-bold. Todoist leans on 475/625 and never uses 700 for body copy;
     * heavy weights are what make a Streamlit app read as clumsy. */
    --weight-regular: 400;
    --weight-medium: 475;
    --weight-semibold: 625;

    --leading-body: 1.75;
    --leading-tight: 1.25;

    /* Small, disciplined radii. Large rounded corners read as toy-like. */
    --radius-xs: 4px;
    --radius-sm: 6px;
    --radius: 8px;
    --radius-md: 10px;
    --radius-lg: 13px;
    --radius-xl: 15px;
    --radius-full: 9999px;

    --transition: 160ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 260ms cubic-bezier(0.16, 1, 0.3, 1);
    --ease-out: cubic-bezier(0.16, 1, 0.3, 1);

    --navbar-height: 60px;
    --max-width: 1200px;
}
"""

# Palette lifted from Todoist's own published tokens, so the app reads the same
# way their product does: warm neutrals rather than cold blue-greys, exactly
# one accent used sparingly, and separation by hairline instead of shadow.
_LIGHT_TOKENS = """
:root {
    --surface-0: #FCF8F3;
    --surface-1: #FFFFFF;
    --surface-2: #FAFAFA;
    --surface-3: #F2F2F2;

    --border-subtle: #F2EFED;
    --border-default: #EBEBEB;
    --border-strong: #DEDEDE;

    --text-primary: #1F1F1F;
    --text-secondary: #575757;
    --text-tertiary: #999999;

    --accent: #3879FA;
    --accent-hover: #316FEA;
    --accent-active: #2064CA;
    --accent-subtle: #F1F7FE;
    --accent-border: #E2F0FF;
    --accent-fg: #FFFFFF;
    --accent-shadow: rgba(56, 121, 250, 0.28);
    --on-gradient: #FFFFFF;

    --gold: #8A6400;
    --gold-subtle: #FAF6EB;
    --gold-border: #EFE0B9;

    --success: #3D7A4A;
    --success-subtle: #F6F9F7;
    --success-border: #CFE3D3;

    --warning: #8A5B00;
    --warning-subtle: #FFFBF1;
    --warning-border: #F7E4C0;

    --danger: #B3342B;
    --danger-subtle: #FDF3F2;
    --danger-border: #F3D3D0;

    --info: #2064CA;
    --info-subtle: #F1F7FE;
    --info-border: #E2F0FF;

    /* Elevation is a 1px hairline at rest. Shadows are reserved for things
     * that genuinely float: overlays, menus, dialogs. */
    --shadow-xs: 0 1px 0 rgba(31, 31, 31, 0.06);
    --shadow-sm: 0 1px 0 rgba(31, 31, 31, 0.08);
    --shadow-md: 0 4px 12px rgba(31, 31, 31, 0.10);
    --shadow-lg: 0 12px 32px rgba(31, 31, 31, 0.14);
    --scrim: rgba(31, 31, 31, 0.03);
}
"""

_DARK_TOKENS = """
:root {
    --surface-0: #16161A;
    --surface-1: #1E1E23;
    --surface-2: #26262C;
    --surface-3: #2E2E35;

    --border-subtle: #26262C;
    --border-default: #32323A;
    --border-strong: #43434D;

    --text-primary: #EDEDF0;
    --text-secondary: #A8A8B3;
    --text-tertiary: #77777F;

    --accent: #3879FA;
    --accent-hover: #5493FB;
    --accent-active: #7AACFC;
    --accent-subtle: #16233A;
    --accent-border: #24406B;
    --accent-fg: #FFFFFF;
    --accent-shadow: rgba(56, 121, 250, 0.34);
    --on-gradient: #FFFFFF;

    --gold: #E0B04A;
    --gold-subtle: #2A2418;
    --gold-border: #453C24;

    --success: #5FB37A;
    --success-subtle: #18251C;
    --success-border: #2A3D30;

    --warning: #E3A73F;
    --warning-subtle: #2A2116;
    --warning-border: #453820;

    --danger: #E0685C;
    --danger-subtle: #2C1A18;
    --danger-border: #4A2C28;

    --info: #7AACFC;
    --info-subtle: #16233A;
    --info-border: #24406B;

    --shadow-xs: 0 1px 0 rgba(0, 0, 0, 0.30);
    --shadow-sm: 0 1px 0 rgba(0, 0, 0, 0.36);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.44);
    --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.55);
    --scrim: rgba(255, 255, 255, 0.03);
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

[data-testid="stAppViewContainer"] .block-container,
.block-container {
    padding-top: 0.75rem !important;
    padding-bottom: 3rem !important;
    max-width: var(--max-width);
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="collapsedControl"] { z-index: 100; }

/* ── Typography ── */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font);
    color: var(--text-primary);
    font-weight: var(--weight-semibold);
    letter-spacing: -0.02em;
    line-height: 1.25;
}
h1 { font-size: 1.75rem; font-weight: var(--weight-semibold); }
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

.top-navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    background: var(--surface-1);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 0.875rem 1.25rem;
    margin-bottom: 0.875rem;
    box-shadow: var(--shadow-sm);
    min-height: 4.25rem;
    position: relative;
    z-index: 10;
}

.navbar-brand {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    text-decoration: none;
    color: inherit;
    cursor: pointer;
}
.top-navbar a[href*="nav"] {
    text-decoration: none;
    color: inherit;
    cursor: pointer;
}
.navbar-brand h1 {
    font-size: 1.1875rem;
    font-weight: var(--weight-semibold);
    margin: 0;
    letter-spacing: -0.03em;
    white-space: nowrap;
    background: linear-gradient(135deg, var(--accent) 0%, var(--text-primary) 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent;
}
.navbar-brand span {
    color: var(--text-tertiary);
    font-size: 0.75rem;
    font-weight: var(--weight-regular);
    margin-left: 0.25rem;
    border-left: 1px solid var(--border-default);
    padding-left: 0.625rem;
}
.navbar-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0;
}
.navbar-actions .nav-date {
    color: var(--text-tertiary);
    font-size: 0.8125rem;
    font-weight: var(--weight-medium);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
"""

# ── Components ───────────────────────────────────────────────────────────────

_COMPONENT_CSS = """
/* ── Buttons ── */
[data-testid="stButton"] button,
[data-testid="stFormSubmitButton"] button,
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-secondary"] {
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

[data-testid="stButton"] button[kind="primary"],
[data-testid="stBaseButton-primary"] {
    background: var(--accent) !important;
    color: var(--accent-fg) !important;
    border-color: var(--accent) !important;
}
[data-testid="stButton"] button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
    background: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
    box-shadow: 0 1px 2px rgba(16, 18, 22, 0.10), 0 4px 12px var(--accent-shadow) !important;
}
[data-testid="stButton"] button[kind="primary"]:active,
[data-testid="stBaseButton-primary"]:active {
    background: var(--accent-active) !important;
    box-shadow: none !important;
    transform: translateY(0.5px);
}

[data-testid="stButton"] button[kind="secondary"],
[data-testid="stBaseButton-secondary"] {
    background: var(--surface-1) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-default) !important;
    box-shadow: var(--shadow-xs) !important;
}
[data-testid="stButton"] button[kind="secondary"]:hover,
[data-testid="stBaseButton-secondary"]:hover {
    background: var(--surface-2) !important;
    border-color: var(--border-strong) !important;
    color: var(--text-primary) !important;
}
[data-testid="stButton"] button[kind="secondary"]:active,
[data-testid="stBaseButton-secondary"]:active {
    background: var(--surface-3) !important;
    transform: translateY(0.5px);
}

[data-testid="stButton"] button:disabled,
[data-testid="stBaseButton-primary"]:disabled,
[data-testid="stBaseButton-secondary"]:disabled {
    opacity: 0.45;
    cursor: not-allowed;
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
    box-shadow: var(--shadow-sm);
    transition: box-shadow var(--transition-slow), border-color var(--transition-slow),
                transform var(--transition-slow);
    animation: fadeIn 320ms var(--ease-out);
}
.card:hover {
    box-shadow: var(--shadow-md);
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
.card--stat::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 5rem;
    height: 5rem;
    border-radius: 50%;
    background: var(--accent);
    opacity: 0.05;
    transform: translate(1.25rem, -1.25rem);
    pointer-events: none;
}
.card--progress { border-left: 3px solid var(--success); }
.card--danger { border-left: 3px solid var(--danger); }
.card--success { border-left: 3px solid var(--success); }
.card--warning { border-left: 3px solid var(--warning); }
.card--info { border-left: 3px solid var(--info); }
.card .value {
    font-family: var(--font-mono);
    font-size: 1.875rem;
    font-weight: var(--weight-semibold);
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
    box-shadow: var(--shadow-sm) !important;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: box-shadow var(--transition-slow), border-color var(--transition-slow);
}
.metric-card:hover { box-shadow: var(--shadow-md); }
.metric-card h3 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: var(--weight-medium);
    color: var(--text-secondary);
}
.metric-card .value {
    font-family: var(--font-mono);
    font-size: 2rem;
    font-weight: var(--weight-semibold);
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
    border-radius: var(--radius);
    padding: 0.875rem 1rem;
    margin: 0.375rem 0;
    box-shadow: var(--shadow-xs);
    color: var(--text-primary);
    font-size: 0.875rem;
    animation: fadeIn 300ms var(--ease-out);
    transition: box-shadow var(--transition), border-color var(--transition);
}
.task-item:hover { box-shadow: var(--shadow-sm); }
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
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.22), transparent);
    animation: shimmer 2.4s infinite;
}

/* ── Avatar ── */
.avatar-circle {
    border-radius: 50%;
    object-fit: cover;
    border: 1px solid var(--border-default);
    box-shadow: var(--shadow-sm);
    transition: transform var(--transition), box-shadow var(--transition);
}
.avatar-circle:hover {
    transform: scale(1.03);
    box-shadow: var(--shadow-md);
}
.avatar-fallback {
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--accent) 0%, var(--info) 100%);
    color: var(--on-gradient);
    border: none;
    box-shadow: var(--shadow-sm);
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
    font-weight: var(--weight-semibold);
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
    height: 2px;
    background: linear-gradient(90deg,
        transparent 0%,
        var(--accent) 50%,
        transparent 100%);
    margin: 1.75rem 0;
    border-radius: 2px;
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
.kiosk-screensaver-images {
    background: #000;
    position: relative;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
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
        padding: 0.75rem 1rem;
        min-height: 3.5rem;
        flex-wrap: wrap;
    }
    .navbar-brand h1 { font-size: 1.0625rem; }
    .navbar-brand span,
    .navbar-actions .nav-date { display: none; }

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


def _build_css(dark_mode: bool) -> str:
    palette = _DARK_TOKENS if dark_mode else _LIGHT_TOKENS
    return "\n".join(
        (
            _FONT_IMPORT,
            _SHARED_TOKENS,
            palette,
            _BASE_CSS,
            _NAV_CSS,
            _COMPONENT_CSS,
            _KIOSK_CSS,
            _RESPONSIVE_CSS,
        )
    )


def apply_custom_styles(dark_mode: bool = False):
    st.markdown(f"<style>{_build_css(dark_mode)}</style>", unsafe_allow_html=True)


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
