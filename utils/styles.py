import streamlit as st


def apply_custom_styles(dark_mode=False):
    theme = "dark" if dark_mode else "light"

    light = {
        "primary": "#6366F1",
        "primary-light": "#818CF8",
        "primary-dark": "#4F46E5",
        "secondary": "#EC4899",
        "secondary-light": "#F472B6",
        "accent": "#14B8A6",
        "accent-light": "#2DD4BF",
        "bg": "#F8FAFC",
        "bg-card": "#FFFFFF",
        "bg-card-alt": "#F1F5F9",
        "bg-nav": "rgba(255,255,255,0.72)",
        "text": "#0F172A",
        "text-secondary": "#64748B",
        "text-muted": "#94A3B8",
        "border": "#E2E8F0",
        "shadow": "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
        "shadow-lg": "0 10px 40px rgba(0,0,0,0.08)",
        "shadow-glow": "0 0 20px rgba(99,102,241,0.15)",
        "success": "#10B981",
        "warning": "#F59E0B",
        "danger": "#EF4444",
        "info": "#6366F1",
    }
    dark_vars = {
        "primary": "#818CF8",
        "primary-light": "#A5B4FC",
        "primary-dark": "#6366F1",
        "secondary": "#F472B6",
        "secondary-light": "#F9A8D4",
        "accent": "#2DD4BF",
        "accent-light": "#5EEAD4",
        "bg": "#0F172A",
        "bg-card": "#1E293B",
        "bg-card-alt": "#334155",
        "bg-nav": "rgba(15,23,42,0.78)",
        "text": "#F1F5F9",
        "text-secondary": "#94A3B8",
        "text-muted": "#64748B",
        "border": "#334155",
        "shadow": "0 1px 3px rgba(0,0,0,0.2), 0 1px 2px rgba(0,0,0,0.1)",
        "shadow-lg": "0 10px 40px rgba(0,0,0,0.3)",
        "shadow-glow": "0 0 20px rgba(129,140,248,0.2)",
        "success": "#34D399",
        "warning": "#FBBF24",
        "danger": "#F87171",
        "info": "#818CF8",
    }

    v = dark_vars if dark_mode else light

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

    :root {{
        --primary: {v["primary"]};
        --primary-light: {v["primary-light"]};
        --primary-dark: {v["primary-dark"]};
        --secondary: {v["secondary"]};
        --secondary-light: {v["secondary-light"]};
        --accent: {v["accent"]};
        --accent-light: {v["accent-light"]};
        --bg: {v["bg"]};
        --bg-card: {v["bg-card"]};
        --bg-card-alt: {v["bg-card-alt"]};
        --bg-nav: {v["bg-nav"]};
        --text: {v["text"]};
        --text-secondary: {v["text-secondary"]};
        --text-muted: {v["text-muted"]};
        --border: {v["border"]};
        --shadow: {v["shadow"]};
        --shadow-lg: {v["shadow-lg"]};
        --shadow-glow: {v["shadow-glow"]};
        --success: {v["success"]};
        --warning: {v["warning"]};
        --danger: {v["danger"]};
        --info: {v["info"]};
        --radius: 12px;
        --radius-lg: 16px;
        --radius-xl: 24px;
        --font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
        --transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        --navbar-height: 64px;
        --max-width: 1200px;
    }}

    * {{
        font-family: var(--font);
        transition: background-color var(--transition), color var(--transition), border-color var(--transition), box-shadow var(--transition);
    }}

    .stApp {{
        background: var(--bg);
        min-height: 100vh;
    }}

    h1, h2, h3, h4, h5, h6 {{
        font-family: var(--font);
        font-weight: 700;
        color: var(--text);
        letter-spacing: -0.02em;
    }}

    h1 {{ font-size: 2em; }}
    h2 {{ font-size: 1.5em; }}
    h3 {{ font-size: 1.25em; }}

    p, li, .caption {{
        color: var(--text-secondary);
        line-height: 1.6;
    }}

    hr {{
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border), transparent);
        margin: 24px 0;
    }}

    /* ── Cards ── */
    .card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 20px 24px;
        box-shadow: var(--shadow);
        transition: all var(--transition);
        animation: fadeIn 0.4s ease-out;
    }}
    .card:hover {{
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }}
    .card--hover {{
        cursor: pointer;
    }}
    .card--hover:hover {{
        border-color: var(--primary-light);
        box-shadow: 0 4px 20px rgba(99,102,241,0.1);
    }}
    .card--stat {{
        border-left: 4px solid var(--primary);
        position: relative;
        overflow: hidden;
    }}
    .card--stat::after {{
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: var(--primary);
        opacity: 0.04;
        transform: translate(20px, -20px);
    }}
    .card--stat .value {{
        font-family: var(--font-mono);
        font-size: 2em;
        font-weight: 700;
        color: var(--text);
        line-height: 1.2;
    }}
    .card--stat .label {{
        font-size: 0.85em;
        color: var(--text-secondary);
        font-weight: 500;
    }}
    .card--stat .icon {{
        font-size: 1.5em;
        margin-bottom: 8px;
    }}
    .card--progress {{
        border-left: 4px solid var(--accent);
    }}
    .card--danger {{
        border-left: 4px solid var(--danger);
    }}
    .card--success {{
        border-left: 4px solid var(--success);
    }}
    .card--warning {{
        border-left: 4px solid var(--warning);
    }}
    .card--info {{
        border-left: 4px solid var(--info);
    }}

    /* ── Task items ── */
    .task-item {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 16px 20px;
        margin: 8px 0;
        box-shadow: var(--shadow);
        border-left: 4px solid var(--primary);
        animation: fadeIn 0.4s ease-out;
        transition: all var(--transition);
    }}
    .task-item:hover {{
        box-shadow: var(--shadow-lg);
    }}
    .task-item.task-done {{
        border-left-color: var(--success);
        opacity: 0.75;
    }}
    .task-item.task-overdue {{
        border-left-color: var(--danger);
    }}

    /* ── Status badges ── */
    .status-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 14px;
        border-radius: 100px;
        font-size: 0.8em;
        font-weight: 600;
        letter-spacing: 0.3px;
        white-space: nowrap;
    }}
    .status-backlog {{
        background: rgba(148,163,184,0.12);
        color: var(--text-muted);
        border: 1px solid rgba(148,163,184,0.2);
    }}
    .status-in-progress {{
        background: rgba(245,158,11,0.1);
        color: var(--warning);
        border: 1px solid rgba(245,158,11,0.2);
    }}
    .status-done {{
        background: rgba(16,185,129,0.1);
        color: var(--success);
        border: 1px solid rgba(16,185,129,0.2);
    }}

    /* ── Buttons ── */
    .stButton > button {{
        border-radius: var(--radius) !important;
        font-weight: 600 !important;
        font-size: 0.9em !important;
        padding: 10px 22px !important;
        transition: all var(--transition) !important;
        border: none !important;
        background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
        color: white !important;
        box-shadow: 0 4px 14px rgba(99,102,241,0.25) !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 24px rgba(99,102,241,0.35) !important;
    }}
    .stButton > button:active {{
        transform: scale(0.97) !important;
    }}
    .stButton > button[kind="secondary"] {{
        background: transparent !important;
        color: var(--text) !important;
        box-shadow: none !important;
        border: 1px solid var(--border) !important;
    }}
    .stButton > button[kind="secondary"]:hover {{
        border-color: var(--primary) !important;
        color: var(--primary) !important;
        background: rgba(99,102,241,0.05) !important;
    }}

    /* ── Segmented control ── */
    .stSegmentedControl > div {{
        background: var(--bg-card-alt) !important;
        border-radius: var(--radius) !important;
        padding: 3px !important;
        border: 1px solid var(--border) !important;
    }}
    .stSegmentedControl label {{
        border-radius: 8px !important;
        padding: 6px 16px !important;
        font-weight: 500 !important;
        font-size: 0.85em !important;
        transition: all var(--transition) !important;
    }}
    .stSegmentedControl label[data-checked="true"] {{
        background: var(--primary) !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(99,102,241,0.3) !important;
    }}

    /* ── Radio ── */
    .stRadio label {{
        padding: 8px 16px !important;
        border-radius: var(--radius) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        margin: 4px !important;
        font-weight: 500 !important;
        transition: all var(--transition) !important;
        cursor: pointer !important;
    }}
    .stRadio label:hover {{
        border-color: var(--primary-light) !important;
        background: rgba(99,102,241,0.03) !important;
    }}
    .stRadio label[data-checked="true"] {{
        border-color: var(--primary) !important;
        background: rgba(99,102,241,0.06) !important;
        color: var(--primary) !important;
    }}

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input {{
        border: 1.5px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 10px 14px !important;
        font-family: var(--font) !important;
        font-size: 0.9em !important;
        background: var(--bg-card) !important;
        color: var(--text) !important;
        transition: all var(--transition) !important;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > div:focus,
    .stNumberInput > div > div > input:focus,
    .stDateInput > div > div > input:focus {{
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
    }}

    /* ── Form ── */
    .stForm {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding: 24px !important;
        box-shadow: var(--shadow) !important;
    }}

    /* ── Tabs ── */
    .stTabs [role="tablist"] {{
        background: var(--bg-card-alt) !important;
        border-radius: var(--radius) !important;
        padding: 4px !important;
        border: 1px solid var(--border) !important;
        gap: 0 !important;
    }}
    .stTabs [role="tab"] {{
        border-radius: 8px !important;
        padding: 8px 20px !important;
        font-weight: 500 !important;
        font-size: 0.85em !important;
        color: var(--text-secondary) !important;
        transition: all var(--transition) !important;
    }}
    .stTabs [role="tab"][aria-selected="true"] {{
        background: var(--bg-card) !important;
        color: var(--primary) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    }}
    .stTabs [role="tab"]:hover {{
        color: var(--primary) !important;
    }}

    /* ── Selectbox ── */
    .stSelectbox label {{
        font-weight: 600 !important;
        font-size: 0.9em !important;
    }}

    /* ── Metric display ── */
    .metric-display {{
        text-align: center;
        padding: 16px;
    }}
    .metric-display .metric-value {{
        font-family: var(--font-mono);
        font-size: 2.2em;
        font-weight: 700;
        color: var(--text);
        line-height: 1.2;
    }}
    .metric-display .metric-label {{
        font-size: 0.8em;
        color: var(--text-secondary);
        font-weight: 500;
        margin-top: 2px;
    }}

    /* ── Progress bars ── */
    .book-progress-bar {{
        height: 8px;
        background: var(--bg-card-alt);
        border-radius: 100px;
        overflow: hidden;
        margin: 10px 0;
    }}
    .book-progress-fill {{
        height: 100%;
        background: linear-gradient(90deg, var(--primary), var(--accent));
        border-radius: 100px;
        transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}
    .book-progress-fill::after {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        animation: shimmer 2s infinite;
    }}
    @keyframes shimmer {{
        0% {{ transform: translateX(-100%); }}
        100% {{ transform: translateX(100%); }}
    }}

    /* ── Avatar ── */
    .avatar-circle {{
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid var(--primary);
        box-shadow: 0 4px 14px rgba(99,102,241,0.2);
        transition: all var(--transition);
    }}
    .avatar-circle:hover {{
        transform: scale(1.05);
        box-shadow: 0 6px 24px rgba(99,102,241,0.3);
    }}

    /* ── Achievement badge ── */
    .achievement-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        background: linear-gradient(135deg, rgba(251,191,36,0.12), rgba(245,158,11,0.08));
        border: 1px solid rgba(251,191,36,0.3);
        border-radius: 100px;
        margin: 4px;
        font-weight: 600;
        font-size: 0.85em;
        color: #B45309;
        animation: badgePop 0.5s ease-out;
    }}
    html[data-theme="dark"] .achievement-badge {{
        background: linear-gradient(135deg, rgba(251,191,36,0.15), rgba(245,158,11,0.1));
        color: #FBBF24;
        border-color: rgba(251,191,36,0.3);
    }}

    /* ── Navbar page buttons ── */
    .stColumn [data-testid="stButton"] button {{
        border-radius: 100px !important;
        padding: 8px 18px !important;
        font-weight: 600 !important;
        font-size: 0.85em !important;
        transition: all var(--transition) !important;
        white-space: nowrap !important;
        background: transparent !important;
        color: var(--text-secondary) !important;
        border: 1px solid transparent !important;
        box-shadow: none !important;
    }}
    .stColumn [data-testid="stButton"] button:hover {{
        background: rgba(99,102,241,0.06) !important;
        color: var(--primary) !important;
        border-color: rgba(99,102,241,0.15) !important;
    }}
    .stColumn [data-testid="stButton"][aria-pressed="true"] button,
    .stColumn [data-testid="stButton"] button[type="primary"] {{
        background: var(--primary) !important;
        color: white !important;
        box-shadow: 0 4px 14px rgba(99,102,241,0.25) !important;
        border-color: transparent !important;
    }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background: var(--bg-card) !important;
        border-right: 1px solid var(--border) !important;
    }}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
        padding: 20px;
    }}

    /* ── Info/Success/Warning/Error boxes ── */
    .stAlert > div {{
        border-radius: var(--radius) !important;
        border: 1px solid var(--border) !important;
        background: var(--bg-card) !important;
        color: var(--text) !important;
    }}

    /* ── Expander ── */
    .streamlit-expanderHeader {{
        background: var(--bg-card-alt) !important;
        border-radius: var(--radius) !important;
        color: var(--text) !important;
        font-weight: 600 !important;
        border: 1px solid var(--border) !important;
        transition: all var(--transition) !important;
    }}
    .streamlit-expanderHeader:hover {{
        border-color: var(--primary-light) !important;
    }}

    /* ── Dataframe / Table ── */
    .stDataFrame, [data-testid="stTable"] {{
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        overflow: hidden !important;
    }}

    /* ── Dividers ── */
    .divider-gradient {{
        border: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--primary), var(--secondary), var(--accent));
        margin: 28px 0;
        border-radius: 2px;
    }}

    /* ── Metric card (legacy class name, maps to card--stat) ── */
    .metric-card {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        padding: 24px !important;
        box-shadow: var(--shadow) !important;
        text-align: center;
        border-left: 4px solid var(--primary);
        position: relative;
        overflow: hidden;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 1em;
        font-weight: 500;
        color: var(--text-secondary);
    }
    .metric-card .value {
        font-family: var(--font-mono);
        font-size: 2.2em;
        font-weight: 700;
        color: var(--text);
        margin: 8px 0;
        line-height: 1.2;
    }
    .metric-card .label {
        font-size: 0.85em;
        color: var(--text-secondary);
        font-weight: 500;
    }

    /* ── StMetric ── */
    .stMetric {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 12px 16px !important;
        box-shadow: var(--shadow) !important;
    }}
    .stMetric label {{
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }}
    .stMetric [data-testid="stMetricValue"] {{
        font-family: var(--font-mono) !important;
        font-weight: 700 !important;
        color: var(--text) !important;
    }}

    /* ── Animations ── */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes slideDown {{
        from {{ opacity: 0; transform: translateY(-20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes badgePop {{
        0% {{ transform: scale(0); opacity: 0; }}
        80% {{ transform: scale(1.1); }}
        100% {{ transform: scale(1); opacity: 1; }}
    }}

    /* ── Mobile ── */
    @media (max-width: 768px) {{
        .stColumn [data-testid="stButton"] button {{
            padding: 6px 10px !important;
            font-size: 0.75em !important;
        }}
        .task-item {{
            padding: 12px 16px;
        }}
        .card {{
            padding: 16px;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)


def styled_card(title: str, content: str, emoji: str = ""):
    st.markdown(f"""
        <div class="card">
            <h3>{emoji} {title}</h3>
            <p>{content}</p>
        </div>
    """, unsafe_allow_html=True)


def success_message(message: str, emoji: str = "✅"):
    st.markdown(f"""
        <div class="info-box" style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);border-radius:12px;padding:12px 16px;color:var(--success, #10B981);font-weight:500;">
            {emoji} {message}
        </div>
    """, unsafe_allow_html=True)


def error_message(message: str, emoji: str = "❌"):
    st.markdown(f"""
        <div class="info-box" style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);border-radius:12px;padding:12px 16px;color:var(--danger, #EF4444);font-weight:500;">
            {emoji} {message}
        </div>
    """, unsafe_allow_html=True)


def warning_message(message: str, emoji: str = "⚠️"):
    st.markdown(f"""
        <div class="info-box" style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);border-radius:12px;padding:12px 16px;color:var(--warning, #F59E0B);font-weight:500;">
            {emoji} {message}
        </div>
    """, unsafe_allow_html=True)


def info_message(message: str, emoji: str = "ℹ️"):
    st.markdown(f"""
        <div class="info-box" style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);border-radius:12px;padding:12px 16px;color:var(--info, #6366F1);font-weight:500;">
            {emoji} {message}
        </div>
    """, unsafe_allow_html=True)


def metric_card(title: str, value: str, subtitle: str = "", emoji: str = ""):
    st.markdown(f"""
        <div class="card card--stat" style="text-align:center;border-left-color:var(--primary);">
            <div style="font-size:1.8em;margin-bottom:6px;">{emoji}</div>
            <h3 style="margin:0;font-size:1em;color:var(--text-secondary);font-weight:500;">{title}</h3>
            <div class="value" style="font-size:2.2em;">{value}</div>
            <div class="label">{subtitle}</div>
        </div>
    """, unsafe_allow_html=True)


def styled_section_header(title: str, emoji: str = ""):
    st.markdown(f"""
        <h2 style="border-bottom:2px solid var(--border);padding-bottom:10px;margin-bottom:20px;color:var(--text);">
            {emoji} {title}
        </h2>
    """, unsafe_allow_html=True)


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
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="avatar-circle" style="width:{width}px;height:{width}px;background:linear-gradient(135deg,var(--primary),var(--secondary));display:flex;align-items:center;justify-content:center;font-size:{width//2.5}px;color:white;">👤</div>',
            unsafe_allow_html=True
        )


def achievement_badge(icon: str, label: str):
    st.markdown(
        f'<span class="achievement-badge">{icon} {label}</span>',
        unsafe_allow_html=True
    )
