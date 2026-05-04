import streamlit as st
from utils.db_helpers import get_all_data
from utils.styles import apply_custom_styles
from app_pages.dashboard import dashboard_page
from app_pages.kanban import kanban_page
from app_pages.kids_profiles import kids_profiles_page
from app_pages.parents_profiles import parents_profiles_page
from app_pages.reading_library import reading_library_page
from app_pages.admin import admin_page

st.set_page_config(
    page_title="Family Task Tracker",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark mode toggle
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Apply custom styles based on dark mode
apply_custom_styles(dark_mode=st.session_state.dark_mode)

# Modern navbar + family background CSS
st.markdown("""
    <style>
    /* Hide Streamlit branding and padding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    .stApp {
        background: linear-gradient(135deg, #FFF5F7 0%, #F0F8FF 50%, #F0FFF4 100%);
        min-height: 100vh;
    }

    /* Family scene background pattern */
    .family-bg {
        position: fixed;
        bottom: 0;
        right: 0;
        width: 350px;
        height: 350px;
        opacity: 0.06;
        pointer-events: none;
        z-index: -1;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 400'%3E%3Cg fill='%23FF8A80'%3E%3Ccircle cx='200' cy='80' r='25'/%3E%3Cpath d='M175 130 Q200 110 225 130 L220 180 Q200 170 180 180 Z'/%3E%3Cpath d='M160 180 L145 240 L170 240 L180 190 Z'/%3E%3Cpath d='M240 180 L255 240 L230 240 L220 190 Z'/%3E%3C/g%3E%3Cg fill='%234ECDC4'%3E%3Ccircle cx='130' cy='140' r='18'/%3E%3Cpath d='M112 180 Q130 165 148 180 L144 220 Q130 215 116 220 Z'/%3E%3Cpath d='M104 220 L95 270 L115 270 L112 230 Z'/%3E%3Cpath d='M156 220 L165 270 L145 270 L148 230 Z'/%3E%3C/g%3E%3Cg fill='%234ECDC4'%3E%3Ccircle cx='270' cy='140' r='18'/%3E%3Cpath d='M252 180 Q270 165 288 180 L284 220 Q270 215 256 220 Z'/%3E%3Cpath d='M244 220 L235 270 L255 270 L252 230 Z'/%3E%3Cpath d='M296 220 L305 270 L285 270 L288 230 Z'/%3E%3C/g%3E%3Cg fill='%23FFD93D'%3E%3Ccircle cx='200' cy='170' r='14'/%3E%3Cpath d='M186 200 Q200 190 214 200 L210 240 Q200 235 190 240 Z'/%3E%3Cpath d='M182 240 L174 280 L190 280 L194 245 Z'/%3E%3Cpath d='M218 240 L226 280 L210 280 L206 245 Z'/%3E%3C/g%3E%3Ccircle cx='100' cy='300' r='30' fill='%23FF8A80' opacity='0.5'/%3E%3Ccircle cx='300' cy='320' r='25' fill='%234ECDC4' opacity='0.5'/%3E%3Cpath d='M50 350 L60 330 L70 350 Z' fill='%23FFD93D' opacity='0.6'/%3E%3Cpath d='M330 340 L340 320 L350 340 Z' fill='%23FF8A80' opacity='0.5'/%3E%3C/svg%3E");
        background-size: contain;
        background-repeat: no-repeat;
    }

    /* Top navbar */
    .top-navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(90deg, #FF8A80 0%, #FF6B6B 40%, #4ECDC4 100%);
        padding: 12px 30px;
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 8px 30px rgba(255, 138, 128, 0.2);
        position: relative;
        overflow: hidden;
        height: 60px;
    }

    .top-navbar::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -30%;
        width: 150%;
        height: 200%;
        background: linear-gradient(45deg, transparent 40%, rgba(255, 255, 255, 0.08) 50%, transparent 60%);
        animation: navbarShine 4s infinite;
    }

    @keyframes navbarShine {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    .navbar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        z-index: 1;
    }

    .navbar-brand .logo {
        font-size: 1.8em;
        background: rgba(255, 255, 255, 0.2);
        width: 42px;
        height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 12px;
    }

    .navbar-brand h1 {
        color: white;
        font-size: 1.5em;
        margin: 0;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        letter-spacing: 1px;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
    }

    .navbar-brand span {
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.85em;
        font-weight: 400;
        margin-left: 5px;
    }

    .navbar-actions {
        display: flex;
        align-items: center;
        gap: 15px;
        z-index: 1;
    }

    .navbar-actions .nav-date {
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.9em;
        font-weight: 500;
    }

    .stToggle {
        z-index: 10;
    }

    .stToggle label {
        display: none !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255, 138, 128, 0.05) 0%, rgba(78, 205, 196, 0.05) 100%);
        border-right: 4px solid;
        border-image: linear-gradient(180deg, #FF8A80, #4ECDC4) 1;
        position: sticky;
        top: 0;
        height: 100vh;
    }

    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        padding: 20px;
    }

    .stRadio > label {
        font-size: 1.15em;
        font-weight: 600;
        color: #2C3E50;
        padding: 12px 15px;
        background: linear-gradient(90deg, rgba(255, 138, 128, 0.05), rgba(78, 205, 196, 0.05));
        border-radius: 10px;
        margin: 8px 0;
        transition: all 0.3s ease;
        cursor: pointer;
        border-left: 3px solid transparent;
    }

    .stRadio > label:hover {
        background: linear-gradient(90deg, rgba(255, 138, 128, 0.15), rgba(78, 205, 196, 0.15));
        border-left: 3px solid #FF8A80;
        transform: translateX(5px);
    }

    h1, h2, h3 {
        color: #FF8A80;
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        letter-spacing: 0.5px;
    }

    h1 { font-size: 2.2em; }
    h2 { font-size: 1.8em; }
    h3 { font-size: 1.4em; }

    body, p {
        color: #2C3E50;
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
    }

    .stButton > button {
        background: linear-gradient(135deg, #FF8A80 0%, #4ECDC4 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 25px;
        font-weight: 600;
        font-size: 1em;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 138, 128, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255, 138, 128, 0.4);
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border: 2px solid #4ECDC4 !important;
        border-radius: 10px !important;
        padding: 10px 15px !important;
        font-family: 'Inter', sans-serif !important;
    }

    .streamlit-expanderHeader {
        background: linear-gradient(90deg, rgba(255, 138, 128, 0.1), rgba(78, 205, 196, 0.1));
        border-radius: 10px;
        color: #2C3E50;
        font-weight: 600;
    }

    hr {
        border: 0;
        height: 3px;
        background: linear-gradient(90deg, #FF8A80, #4ECDC4);
    }

    .caption {
        color: #666;
        font-size: 0.95em;
        font-weight: 500;
    }

    .status-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .status-backlog {
        background: rgba(158, 158, 158, 0.15);
        color: #9E9E9E;
        border: 1px solid #9E9E9E;
    }

    .status-in-progress {
        background: rgba(255, 152, 0, 0.15);
        color: #FF9800;
        border: 1px solid #FF9800;
    }

    .status-done {
        background: rgba(76, 175, 80, 0.15);
        color: #4CAF50;
        border: 1px solid #4CAF50;
    }

    .avatar-circle {
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid #FF8A80;
        box-shadow: 0 4px 15px rgba(255, 138, 128, 0.3);
    }

    .achievement-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 18px;
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 193, 7, 0.1));
        border: 1px solid #FFD700;
        border-radius: 25px;
        margin: 5px;
        animation: badgePop 0.5s ease-out;
        font-weight: 600;
        color: #B8860B;
    }

    @keyframes badgePop {
        0% { transform: scale(0); opacity: 0; }
        80% { transform: scale(1.1); }
        100% { transform: scale(1); opacity: 1; }
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .metric-card {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E72 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 20px rgba(255, 107, 107, 0.3);
    }

    .metric-card h3 {
        color: white;
        margin: 0;
        font-size: 1.2em;
    }

    .metric-card .value {
        font-size: 2.5em;
        font-weight: 700;
        margin: 10px 0;
    }

    .metric-card .label {
        font-size: 0.9em;
        opacity: 0.9;
    }

    .task-item {
        background: rgba(255, 255, 255, 0.8);
        padding: 15px 20px;
        border-radius: 12px;
        margin: 10px 0;
        border-left: 4px solid #FF8A80;
        animation: fadeIn 0.4s ease-out;
    }

    .task-item:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .book-progress-bar {
        height: 8px;
        background: rgba(0, 0, 0, 0.08);
        border-radius: 4px;
        overflow: hidden;
        margin: 10px 0;
    }

    .book-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #FF8A80, #4ECDC4);
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    @media (max-width: 768px) {
        .top-navbar {
            padding: 10px 15px;
            border-radius: 12px;
            height: 50px;
        }

        .navbar-brand h1 {
            font-size: 1.1em;
        }

        .navbar-brand .logo {
            font-size: 1.4em;
            width: 35px;
            height: 35px;
        }

        .navbar-actions .nav-date {
            display: none;
        }

        .metric-card {
            padding: 15px;
        }

        .metric-card .value {
            font-size: 1.8em;
        }

        .family-bg {
            width: 200px;
            height: 200px;
        }
    }
    </style>

    <div class="family-bg"></div>
""", unsafe_allow_html=True)

# Modern navbar
dark_col1, dark_col2 = st.columns([6, 1])

with dark_col1:
    st.markdown("""
        <div class="top-navbar">
            <div class="navbar-brand">
                <div class="logo">🏠</div>
                <h1>Family Task Tracker <span>✨ Your family's adventure</span></h1>
            </div>
            <div class="navbar-actions">
                <div class="nav-date" id="current-date"></div>
            </div>
        </div>
        <script>
            document.getElementById('current-date').textContent = new Date().toLocaleDateString('en-GB', {
                weekday: 'short', day: 'numeric', month: 'short', year: 'numeric'
            });
        </script>
    """, unsafe_allow_html=True)

with dark_col2:
    st.markdown("<div style='height:60px;display:flex;align-items:center;justify-content:center;'>", unsafe_allow_html=True)
    dark_toggle = st.toggle("🌙", value=st.session_state.dark_mode, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()

data = get_all_data()

# Sidebar navigation
st.sidebar.markdown("### 📋 NAVIGATION")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Select a page:",
    [
        "📊 Dashboard",
        "🎯 Kanban Board",
        "👨‍👩‍👧‍👦 Parents Profiles",
        "👨‍👩‍👧‍👦 Kids Profiles",
        "📚 Reading Library",
        "⚙️ Admin"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.caption("💖 Made with love for your family")

# Route to pages
if "Dashboard" in page:
    dashboard_page(data)

elif "Kanban" in page:
    kanban_page(data)

elif "Parents" in page:
    parents_profiles_page(data)

elif "Kids" in page:
    kids_profiles_page(data)

elif "Reading" in page:
    reading_library_page(data)

elif "Admin" in page:
    admin_page(data)
