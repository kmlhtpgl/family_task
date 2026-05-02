import streamlit as st
from utils.db_helpers import get_all_data
from app_pages.dashboard import dashboard_page
from app_pages.kanban import kanban_page
from app_pages.kids_profiles import kids_profiles_page
from app_pages.reading_library import reading_library_page
from app_pages.admin import admin_page

st.set_page_config(
    page_title="Family Task Tracker",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
    <style>
    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%);
        padding: 30px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .main-header h1 {
        color: white;
        font-size: 2.5em;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1em;
        margin: 10px 0 0 0;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #262730 0%, #1a1f2e 100%);
    }
    
    /* Radio button styling */
    .stRadio > label {
        font-size: 1.1em;
        font-weight: 500;
    }
    
    /* General text styling */
    h1, h2, h3 {
        color: #FF6B6B;
    }
    </style>
""", unsafe_allow_html=True)

# Header with gradient
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
        <div class="main-header">
            <h1>✅ Family Task Tracker</h1>
            <p>🎯 Your family's task & reading adventure</p>
        </div>
    """, unsafe_allow_html=True)

data = get_all_data()

# Sidebar with enhanced styling
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 NAVIGATION")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Select a page:",
    [
        "📊 Dashboard",
        "🎯 Kanban Board",
        "👨‍👩‍👧‍👦 Kids Profiles",
        "📚 Reading Library",
        "⚙️ Admin"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.caption("Made with ❤️ for your family")

# Route to pages
if "Dashboard" in page:
    dashboard_page(data)

elif "Kanban" in page:
    kanban_page(data)

elif "Kids" in page:
    kids_profiles_page(data)

elif "Reading" in page:
    reading_library_page(data)

elif "Admin" in page:
    admin_page(data)
