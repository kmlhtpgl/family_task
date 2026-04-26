import streamlit as st
from utils.data_helpers import load_data

from app_pages.dashboard import dashboard_page
from app_pages.kanban import kanban_page
from app_pages.kids_profiles import kids_profiles_page
from app_pages.reading_library import reading_library_page
from app_pages.admin import admin_page


st.set_page_config(
    page_title="Family Task Tracker",
    page_icon="✅",
    layout="wide"
)

st.title("✅ Family Task Tracker")
st.caption("A simple Jira-style task and reading tracker for your family.")

data = load_data()

st.sidebar.header("Menu")

page = st.sidebar.radio(
    "Go to",
    [
        "Dashboard",
        "Kanban Board",
        "Kids Profiles",
        "Reading Library",
        "Admin"
    ]
)

if page == "Dashboard":
    dashboard_page(data)

elif page == "Kanban Board":
    kanban_page(data)

elif page == "Kids Profiles":
    kids_profiles_page(data)

elif page == "Reading Library":
    reading_library_page(data)

elif page == "Admin":
    admin_page(data)
