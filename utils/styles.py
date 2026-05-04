"""
Modern styling utilities for the Family Task Tracker
Provides reusable components and styling functions
"""

import streamlit as st


def apply_custom_styles(dark_mode=False):
    """Apply modern custom CSS styling to the app"""

    if dark_mode:
        bg_gradient = "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)"
        card_bg = "linear-gradient(135deg, rgba(30, 30, 50, 0.95), rgba(25, 25, 45, 0.9))"
        text_color = "#e0e0e0"
        text_secondary = "#a0a0a0"
        header_color = "#4ECDC4"
        sidebar_bg = "linear-gradient(180deg, rgba(78, 205, 196, 0.05) 0%, rgba(255, 138, 128, 0.05) 100%)"
        input_border = "#4ECDC4"
        header_gradient = "linear-gradient(90deg, #4ECDC4 0%, #FF8A80 100%)"
        card_border = "#4ECDC4"
        container_bg = "rgba(255, 255, 255, 0.05)"
    else:
        bg_gradient = "linear-gradient(135deg, #FFF5F7 0%, #F0F8FF 50%, #F0FFF4 100%)"
        card_bg = "linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(240, 247, 255, 0.9))"
        text_color = "#2C3E50"
        text_secondary = "#666"
        header_color = "#FF8A80"
        sidebar_bg = "linear-gradient(180deg, rgba(255, 138, 128, 0.05) 0%, rgba(78, 205, 196, 0.05) 100%)"
        input_border = "#4ECDC4"
        header_gradient = "linear-gradient(90deg, #FF8A80 0%, #4ECDC4 100%)"
        card_border = "#FF8A80"
        container_bg = "rgba(255, 255, 255, 0.8)"

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@300;400;600;700&display=swap');

        * {{
            font-family: 'Inter', 'Poppins', sans-serif;
        }}

        .stApp {{
            background: {bg_gradient};
            min-height: 100vh;
        }}

        [data-testid="stSidebar"] {{
            background: {sidebar_bg};
            border-right: 4px solid;
            border-image: {header_gradient} 1;
        }}

        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
            padding: 20px;
        }}

        .main-header {{
            background: {header_gradient};
            padding: 50px 40px;
            border-radius: 25px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 15px 40px rgba(255, 138, 128, 0.2);
            animation: slideDown 0.7s ease-out;
            position: relative;
            overflow: hidden;
        }}

        .main-header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%);
            animation: shine 3s infinite;
        }}

        @keyframes shine {{
            0% {{ transform: translateX(-100%) translateY(-100%); }}
            100% {{ transform: translateX(100%) translateY(100%); }}
        }}

        @keyframes slideDown {{
            from {{ opacity: 0; transform: translateY(-30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}

        @keyframes countUp {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes badgePop {{
            0% {{ transform: scale(0); opacity: 0; }}
            80% {{ transform: scale(1.1); }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}

        .main-header h1 {{
            color: white;
            font-size: 3.5em;
            margin: 0;
            text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.15);
            font-weight: 700;
            font-family: 'Poppins', sans-serif;
            letter-spacing: 2px;
            position: relative;
            z-index: 1;
        }}

        .main-header p {{
            color: rgba(255, 255, 255, 0.95);
            font-size: 1.4em;
            margin: 20px 0 0 0;
            font-weight: 500;
            letter-spacing: 0.5px;
            position: relative;
            z-index: 1;
        }}

        h1, h2, h3 {{
            color: {header_color};
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}

        .stButton > button {{
            background: {header_gradient};
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 25px;
            font-weight: 600;
            font-size: 1em;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255, 138, 128, 0.3);
        }}

        .stButton > button:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(255, 138, 128, 0.4);
        }}

        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {{
            border: 2px solid {input_border} !important;
            border-radius: 10px !important;
            padding: 10px 15px !important;
        }}

        .streamlit-expanderHeader {{
            background: {container_bg};
            border-radius: 10px;
            color: {text_color};
            font-weight: 600;
        }}

        hr {{
            border: 0;
            height: 3px;
            background: {header_gradient};
        }}

        .status-badge {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .status-backlog {{
            background: rgba(158, 158, 158, 0.15);
            color: #9E9E9E;
            border: 1px solid #9E9E9E;
        }}

        .status-in-progress {{
            background: rgba(255, 152, 0, 0.15);
            color: #FF9800;
            border: 1px solid #FF9800;
        }}

        .status-done {{
            background: rgba(76, 175, 80, 0.15);
            color: #4CAF50;
            border: 1px solid #4CAF50;
        }}

        .modern-card {{
            background: {card_bg};
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            border-left: 5px solid {card_border};
            margin: 15px 0;
            transition: all 0.3s ease;
            animation: fadeIn 0.5s ease-out;
        }}

        .modern-card:hover {{
            box-shadow: 0 8px 25px rgba(255, 107, 107, 0.15);
            transform: translateY(-5px);
        }}

        .avatar-circle {{
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid {header_gradient};
            box-shadow: 0 4px 15px rgba(255, 138, 128, 0.3);
        }}

        .achievement-badge {{
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
        }}

        .metric-card {{
            background: {header_gradient};
            padding: 25px;
            border-radius: 15px;
            color: white;
            text-align: center;
            box-shadow: 0 8px 20px rgba(255, 107, 107, 0.3);
        }}

        .metric-card h3 {{
            color: white;
            margin: 0;
            font-size: 1.2em;
        }}

        .metric-card .value {{
            font-size: 2.5em;
            font-weight: 700;
            margin: 10px 0;
        }}

        .metric-card .label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}

        .week-nav {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
        }}

        .week-nav button {{
            background: {header_gradient};
            color: white;
            border: none;
            border-radius: 10px;
            padding: 8px 20px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s ease;
        }}

        .week-nav button:hover {{
            transform: scale(1.05);
        }}

        .task-item {{
            background: {container_bg};
            padding: 15px 20px;
            border-radius: 12px;
            margin: 10px 0;
            border-left: 4px solid {card_border};
            animation: fadeIn 0.4s ease-out;
        }}

        .task-item:hover {{
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}

        .book-progress-bar {{
            height: 8px;
            background: rgba(0, 0, 0, 0.1);
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }}

        .book-progress-fill {{
            height: 100%;
            background: {header_gradient};
            border-radius: 4px;
            transition: width 0.3s ease;
        }}

        .calendar-day {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            font-size: 0.9em;
            font-weight: 600;
            margin: 2px;
        }}

        .calendar-day.has-tasks {{
            background: rgba(255, 138, 128, 0.2);
            border: 2px solid #FF8A80;
        }}

        .calendar-day.today {{
            background: {header_gradient};
            color: white;
        }}

        @media (max-width: 768px) {{
            .main-header {{
                padding: 30px 20px;
                border-radius: 15px;
            }}

            .main-header h1 {{
                font-size: 2em;
            }}

            .main-header p {{
                font-size: 1em;
            }}

            .modern-card {{
                padding: 15px;
            }}

            .stButton > button {{
                padding: 10px 15px;
                font-size: 0.9em;
            }}

            .metric-card {{
                padding: 15px;
            }}

            .metric-card .value {{
                font-size: 1.8em;
            }}
        }}
        </style>
    """, unsafe_allow_html=True)


def styled_card(title: str, content: str, emoji: str = ""):
    """Create a modern styled card"""
    st.markdown(f"""
        <div class="modern-card">
            <h3>{emoji} {title}</h3>
            <p>{content}</p>
        </div>
    """, unsafe_allow_html=True)


def success_message(message: str, emoji: str = "✅"):
    """Display a success message with modern styling"""
    st.markdown(f"""
        <div class="info-box">
            {emoji} {message}
        </div>
    """, unsafe_allow_html=True)


def error_message(message: str, emoji: str = "❌"):
    """Display an error message with modern styling"""
    st.markdown(f"""
        <div class="error-box">
            {emoji} {message}
        </div>
    """, unsafe_allow_html=True)


def warning_message(message: str, emoji: str = "⚠️"):
    """Display a warning message with modern styling"""
    st.markdown(f"""
        <div class="warning-box">
            {emoji} {message}
        </div>
    """, unsafe_allow_html=True)


def info_message(message: str, emoji: str = "ℹ️"):
    """Display a info message with modern styling"""
    st.markdown(f"""
        <div class="info-box">
            {emoji} {message}
        </div>
    """, unsafe_allow_html=True)


def metric_card(title: str, value: str, subtitle: str = "", emoji: str = ""):
    """Create a colorful metric card"""
    st.markdown(f"""
        <div class="metric-card">
            <h3>{emoji} {title}</h3>
            <div class="value">{value}</div>
            <div class="label">{subtitle}</div>
        </div>
    """, unsafe_allow_html=True)


def styled_section_header(title: str, emoji: str = ""):
    """Create a modern section header"""
    st.markdown(f"""
        <h2 style='color: #FF6B6B; border-bottom: 3px solid #4ECDC4; padding-bottom: 10px;'>
            {emoji} {title}
        </h2>
    """, unsafe_allow_html=True)


def create_button_group(buttons: list):
    """Create a group of styled buttons"""
    cols = st.columns(len(buttons))
    for col, button_text in zip(cols, buttons):
        with col:
            st.button(button_text)


def divider_gradient():
    """Create a gradient divider"""
    st.markdown("""
        <hr style='background: linear-gradient(90deg, #FF6B6B, #FFD93D, #4ECDC4);
                   border: 0; height: 3px; margin: 30px 0;'>
    """, unsafe_allow_html=True)


def status_badge(status: str):
    """Create a color-coded status badge"""
    badge_classes = {
        "Backlog": "status-badge status-backlog",
        "In Progress": "status-badge status-in-progress",
        "Done": "status-badge status-done",
    }
    css_class = badge_classes.get(status, "status-badge")
    st.markdown(f'<span class="{css_class}">{status}</span>', unsafe_allow_html=True)


def avatar_image(image_url: str, width: int = 120):
    """Display a circular avatar image"""
    if image_url:
        st.markdown(
            f'<img src="{image_url}" class="avatar-circle" width="{width}" height="{width}" />',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="avatar-circle" style="width:{width}px;height:{width}px;background:linear-gradient(135deg,#FF8A80,#4ECDC4);display:flex;align-items:center;justify-content:center;font-size:{width//2.5}px;color:white;">👤</div>',
            unsafe_allow_html=True
        )


def achievement_badge(icon: str, label: str):
    """Display an achievement badge"""
    st.markdown(
        f'<span class="achievement-badge">{icon} {label}</span>',
        unsafe_allow_html=True
    )
