"""
Modern styling utilities for the Family Task Tracker
Provides reusable components and styling functions
"""

import streamlit as st


def apply_custom_styles():
    """Apply modern custom CSS styling to the app"""
    st.markdown("""
        <style>
        /* Card component */
        .modern-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(240, 247, 255, 0.9));
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            border-left: 5px solid #FF6B6B;
            margin: 15px 0;
            transition: all 0.3s ease;
        }
        
        .modern-card:hover {
            box-shadow: 0 8px 25px rgba(255, 107, 107, 0.15);
            transform: translateY(-5px);
        }
        
        /* Success message */
        .success-box {
            background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(76, 175, 80, 0.05));
            border-left: 5px solid #4CAF50;
            padding: 15px 20px;
            border-radius: 10px;
            color: #2E7D32;
            font-weight: 500;
        }
        
        /* Error message */
        .error-box {
            background: linear-gradient(135deg, rgba(244, 67, 54, 0.1), rgba(244, 67, 54, 0.05));
            border-left: 5px solid #F44336;
            padding: 15px 20px;
            border-radius: 10px;
            color: #C62828;
            font-weight: 500;
        }
        
        /* Warning message */
        .warning-box {
            background: linear-gradient(135deg, rgba(255, 193, 7, 0.1), rgba(255, 193, 7, 0.05));
            border-left: 5px solid #FFC107;
            padding: 15px 20px;
            border-radius: 10px;
            color: #F57F17;
            font-weight: 500;
        }
        
        /* Info message */
        .info-box {
            background: linear-gradient(135deg, rgba(33, 150, 243, 0.1), rgba(33, 150, 243, 0.05));
            border-left: 5px solid #2196F3;
            padding: 15px 20px;
            border-radius: 10px;
            color: #1565C0;
            font-weight: 500;
        }
        
        /* Metric card */
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
        <div class="success-box">
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
    """Display an info message with modern styling"""
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
