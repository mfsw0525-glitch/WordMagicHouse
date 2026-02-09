# ui_components.py
import streamlit as st
from config import *

def inject_custom_css():
    # Use a template to avoid f-string brace confusion
    css = """
    <style>
        /* Global Font */
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Nunito', sans-serif;
            color: {{THEME_TEXT_PRIMARY}};
        }

        /* App Background */
        .stApp {
            background: {{THEME_BACKGROUND_GRADIENT}};
        }
        
        /* Headers */
        h1 {
            color: {{THEME_TEXT_PRIMARY}};
            font-weight: 700;
            text-align: center;
            font-size: 2.5rem !important;
            margin-bottom: 30px !important;
        }
        
        /* Glassmorphism Cards */
        .glass-card {
            background: rgba(255, 255, 255, 0.65);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.4);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
            padding: 24px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        /* Definition Card */
        .definition-card {
            background: #D4EFDF;
            border-left: 10px solid {{THEME_ACCENT}};
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            text-align: center;
        }
        
        /* Stats Numbers */
        .stat-number {
            font-size: 2.5rem;
            font-weight: 800;
            color: {{THEME_ACCENT}};
        }
        
        /* Buttons - Modern Filled Style */
        .stButton > button {
            background: {{THEME_COLOR_PRIMARY}} !important;
            color: #FFFFFF !important;
            border-radius: 50px !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
            font-size: 20px !important;
            font-weight: 700 !important;
            padding: 10px 20px !important;
            transition: all 0.2s ease !important;
        }
        .stButton > button:hover {
            background: {{THEME_TEXT_PRIMARY}} !important;
            color: #FFFFFF !important;
            transform: translateY(-2px);
        }
        
        /* Hide Streamlit Branding */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        div.stDeployButton {display:none;}
        
        /* Centering */
        .stMarkdown, .stButton {
            text-align: center;
        }
        .center-text {
            text-align: center;
            width: 100%;
        }
    </style>
    """
    # Replace placeholders manually to be 100% safe
    css = css.replace("{{THEME_TEXT_PRIMARY}}", THEME_TEXT_PRIMARY)
    css = css.replace("{{THEME_BACKGROUND_GRADIENT}}", THEME_BACKGROUND_GRADIENT)
    css = css.replace("{{THEME_ACCENT}}", THEME_ACCENT)
    css = css.replace("{{THEME_COLOR_PRIMARY}}", THEME_COLOR_PRIMARY)
    css = css.replace("{{THEME_TEXT_SECONDARY}}", THEME_TEXT_SECONDARY)
    
    st.markdown(css, unsafe_allow_html=True)

def render_sidebar_stats(session_type, total, remaining):
    with st.sidebar:
        st.markdown(f"<h2>🏰 Learning Status</h2>", unsafe_allow_html=True)
        st.write("---")
        if session_type:
            label = "🆕 New Task" if session_type == "new" else "🔄 Review Task"
            st.write(f"**{label}**")
            st.write(f"Progress: {remaining} / {total}")
            progress = (total - remaining) / total if total > 0 else 0
            st.progress(progress)
        else:
            st.info("Start a session!")

def render_header(title, subtitle=None):
    st.markdown(f"<h1 style='text-align:center;'>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<h3 style='text-align:center; opacity:0.7;'>{subtitle}</h3>", unsafe_allow_html=True)

def render_stat_card(label, value):
    st.markdown(f"""
    <div class="glass-card">
        <div style="opacity:0.8;">{label}</div>
        <div style="font-size:2.5rem; font-weight:800; color:{THEME_ACCENT};">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def render_definition_card(content):
    st.markdown(f"""
    <div class="definition-card">
        <div style="font-size:0.9rem; opacity:0.6; margin-bottom:10px; font-weight:bold; text-transform:uppercase;">Meaning</div>
        <div style="font-size:2rem; font-weight:800; color:#1A5276;">{content}</div>
    </div>
    """, unsafe_allow_html=True)

def render_card(content, text_color=None):
    style = f"color: {text_color};" if text_color else ""
    st.markdown(f'<div class="glass-card" style="font-size: 1.5rem; font-weight:700; {style}">{content}</div>', unsafe_allow_html=True)

def render_feedback(is_correct, message):
    color = THEME_CORRECT if is_correct else THEME_WRONG
    icon = "🎉" if is_correct else "💪"
    st.markdown(f"""
    <div style="text-align:center; padding:20px; border-radius:20px; border:3px solid {color}; background:#F4F6F7; margin-bottom: 30px;">
        <div style="font-size:2rem; font-weight:800; color:{color};">{icon} {message}</div>
    </div>
    """, unsafe_allow_html=True)
