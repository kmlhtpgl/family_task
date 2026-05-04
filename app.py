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
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark mode toggle
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Sidebar dark mode toggle
with st.sidebar:
    st.markdown("---")
    dark_toggle = st.toggle("🌙 Dark mode", value=st.session_state.dark_mode)

    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()

    st.markdown("### 📋 NAVIGATION")
    st.markdown("---")

# Apply custom styles based on dark mode
apply_custom_styles(dark_mode=st.session_state.dark_mode)

# Custom CSS for main layout with beautiful color transitions
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@300;400;600;700&display=swap');

    * {
        font-family: 'Inter', 'Poppins', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #FFF5F7 0%, #F0F8FF 50%, #F0FFF4 100%);
        min-height: 100vh;
    }

    .main-header {
        background: linear-gradient(90deg, #FF8A80 0%, #4ECDC4 100%);
        padding: 50px 40px;
        border-radius: 25px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 15px 40px rgba(255, 138, 128, 0.2);
        animation: slideDown 0.7s ease-out;
        position: relative;
        overflow: hidden;
    }

    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%);
        animation: shine 3s infinite;
    }

    @keyframes shine {
        0% { transform: translateX(-100%) translateY(-100%); }
        100% { transform: translateX(100%) translateY(100%); }
    }

    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .main-header h1 {
        color: white;
        font-size: 3.5em;
        margin: 0;
        text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.15);
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        letter-spacing: 2px;
        position: relative;
        z-index: 1;
    }

    .main-header p {
        color: rgba(255, 255, 255, 0.95);
        font-size: 1.4em;
        margin: 20px 0 0 0;
        font-weight: 500;
        letter-spacing: 0.5px;
        position: relative;
        z-index: 1;
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

    h1 { font-size: 2.5em; }
    h2 { font-size: 2em; }
    h3 { font-size: 1.5em; }

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

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .task-item:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    @media (max-width: 768px) {
        .main-header {
            padding: 30px 20px;
            border-radius: 15px;
        }

        .main-header h1 {
            font-size: 2em;
        }

        .main-header p {
            font-size: 1em;
        }

        .metric-card {
            padding: 15px;
        }

        .metric-card .value {
            font-size: 1.8em;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
        <div class="main-header">
            <h1>✅ Family Task Tracker</h1>
            <p>🎯 Your family's task & reading adventure</p>
        </div>
    """, unsafe_allow_html=True)

data = get_all_data()

# Sidebar navigation
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
