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

# Apply modern custom styling
apply_custom_styles()

# Custom CSS for main layout with beautiful color transitions
st.markdown("""
    <style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Inter', 'Poppins', sans-serif;
    }
    
    /* Main background with smooth gradient transition */
    .stApp {
        background: linear-gradient(135deg, #FFF5F7 0%, #F0F8FF 50%, #F0FFF4 100%);
        min-height: 100vh;
    }
    
    /* Main header with beautiful 2-color transition */
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
    
    /* Animated background shine effect */
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
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
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
    
    /* Sidebar styling with gradient border */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255, 138, 128, 0.05) 0%, rgba(78, 205, 196, 0.05) 100%);
        border-right: 4px solid;
        border-image: linear-gradient(180deg, #FF8A80, #4ECDC4) 1;
    }
    
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        padding: 20px;
    }
    
    /* Navigation styling with hover effect */
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
    
    /* Section headers with color transition */
    h1, h2, h3 {
        color: #FF8A80;
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    h1 { font-size: 2.5em; }
    h2 { font-size: 2em; }
    h3 { font-size: 1.5em; }
    
    /* Text styling */
    body, p {
        color: #2C3E50;
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
    }
    
    /* Button styling with coral-to-teal gradient */
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
    
    /* Input field styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border: 2px solid #4ECDC4 !important;
        border-radius: 10px !important;
        padding: 10px 15px !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, rgba(255, 138, 128, 0.1), rgba(78, 205, 196, 0.1));
        border-radius: 10px;
        color: #2C3E50;
        font-weight: 600;
    }
    
    /* Divider with gradient */
    hr {
        border: 0;
        height: 3px;
        background: linear-gradient(90deg, #FF8A80, #4ECDC4);
    }
    
    /* Caption and small text */
    .caption {
        color: #666;
        font-size: 0.95em;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# Header with beautiful 2-color gradient transition
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
st.sidebar.markdown("---")
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

# Route to pages based on selection
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
