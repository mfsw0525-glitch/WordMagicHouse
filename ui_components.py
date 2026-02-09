# ui_components.py
import streamlit as st
from config import *

def inject_custom_css():
    st.markdown(f"""
    <style>
        /* Global Font */
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Nunito', sans-serif;
            color: {THEME_TEXT_PRIMARY};
        }}

        /* App Background - Misty Rose Gradient */
        .stApp {{
            background: {THEME_BACKGROUND_GRADIENT};
        }}
        
        /* Headers */
        h1 {{
            color: {THEME_TEXT_PRIMARY};
            font-weight: 700;
            text-align: center;
            font-size: 2.5rem !important;
            margin-bottom: 30px !important;
        }}
        
        /* Glassmorphism Cards */
        .glass-card {{
            background: rgba(255, 255, 255, 0.65);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.4);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
            padding: 24px;
            margin-bottom: 20px;
            text-align: center;
            transition: transform 0.2s;
        }}
        .glass-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.12);
        }}
        
        /* Definition Card - Distinct Background */
        .definition-card {{
            background: #D4EFDF; /* Darker/More Saturated Light Green */
            border-left: 10px solid {THEME_ACCENT};
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        /* Stats Numbers */
        .stat-number {{
            font-size: 2.5rem;
            font-weight: 800;
            color: {THEME_ACCENT};
            margin-top: 5px;
        }}
        .stat-label {{
            font-size: 1.2rem;
            font-weight: 600;
            color: {THEME_TEXT_PRIMARY};
            opacity: 0.8;
        }}
        
        /* Buttons - Minimalist & Pill Shaped */
        .stButton > button {{
            background: #FFFFFF;
            color: {THEME_TEXT_PRIMARY};
            border-radius: 50px;
            border: 2px solid {THEME_COLOR_PRIMARY};
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            font-size: 22px !important; /* Larger font */
            font-weight: 700;
            padding: 15px 30px !important; /* Larger padding */
            width: 100%;
            transition: all 0.2s;
        }}
        .stButton > button:hover {{
            background: {THEME_COLOR_PRIMARY};
            color: #FFF;
            transform: scale(1.02);
            box-shadow: 0 6px 16px rgba(0,0,0,0.12);
        }}
        
        /* Special class for Next/Check buttons if we could target them, 
           but global style update covers the "Make buttons bigger" request */
        
        /* Progress Bar */
        .stProgress > div > div > div > div {{
            background-color: {THEME_ACCENT};
            border-radius: 10px;
        }}
        
        /* Input Fields */
        .stTextInput > div > div > input {{
            border-radius: 15px;
            border: 2px solid rgba(255,255,255,0.5);
            background: rgba(255,255,255,0.7);
            text-align: center;
            font-size: 24px;
            color: {THEME_TEXT_PRIMARY};
            padding: 10px;
        }}
        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background: {THEME_COLOR_SECONDARY};
            border-right: 1px solid rgba(0,0,0,0.05);
        }}
        .sidebar-stat-label {{
            font-size: 0.9rem;
            color: {THEME_TEXT_PRIMARY};
            opacity: 0.7;
            margin-top: 20px;
        }}
        .sidebar-stat-value {{
            font-size: 1.8rem;
            font-weight: 800;
            color: {THEME_ACCENT};
            margin-bottom: 5px;
        }}
    </style>
    """, unsafe_allow_html=True)

def render_sidebar_stats(session_type, total, remaining):
    with st.sidebar:
        st.markdown(f"<h2>🏰 Learning Status</h2>", unsafe_allow_html=True)
        st.write("---")
        
        if session_type:
            label = "🆕 New Task" if session_type == "new" else "🔄 Review Task"
            st.markdown(f'<div class="sidebar-stat-label">{label}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sidebar-stat-value">{remaining} / {total}</div>', unsafe_allow_html=True)
            
            # Simple progress circle/bar
            progress = (total - remaining) / total if total > 0 else 0
            st.progress(progress)
            st.caption(f"{int(progress*100)}% Completed")
        else:
            st.info("Start a session to see progress!")

def render_header(title, subtitle=None):
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<h3 style='text-align:center; opacity:0.7;'>{subtitle}</h3>", unsafe_allow_html=True)

def render_stat_card(label, value):
    st.markdown(f"""
    <div class="glass-card">
        <div class="stat-label">{label}</div>
        <div class="stat-number">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def render_definition_card(content):
    st.markdown(f"""
    <div class="definition-card">
        <div style="font-size: 0.9rem; opacity: 0.6; margin-bottom: 10px; font-weight: bold; text-transform: uppercase; color: {THEME_TEXT_SECONDARY};">Meaning</div>
        <div style="font-size: 2rem; font-weight: 800; color: #1A5276;">{content}</div>
    </div>
    """, unsafe_allow_html=True)

def render_card(content, text_color=None):
    style = f"color: {text_color};" if text_color else ""
    st.markdown(f'<div class="glass-card" style="font-size: 1.5rem; font-weight:700; {style}">{content}</div>', unsafe_allow_html=True)

def render_feedback(is_correct, message):
    color = THEME_CORRECT if is_correct else THEME_WRONG
    icon = "🎉" if is_correct else "💪"
    st.markdown(f"""
    <div style="
        text-align: center; 
        padding: 20px; 
        margin-top: 10px; 
        margin-bottom: 20px;
        border-radius: 20px; 
        background-color: #F4F6F7; /* Soft Pale Grey */
        border: 3px solid {color};
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        animation: fadeIn 0.5s;
    ">
        <div style="font-size: 2rem; font-weight: 800; color: {color}; margin-bottom: 5px;">
            {icon} {message}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_coin_counter(amount):
    st.markdown(
        f"""
        <div style="position: fixed; top: 15px; right: 20px; 
             background: rgba(255,255,255,0.9); 
             padding: 8px 18px; border-radius: 30px; 
             box-shadow: 0 4px 10px rgba(0,0,0,0.1);
             font-weight: 800; font-size: 18px; color: #FFD700; z-index: 999;
             display: flex; align-items: center; gap: 5px;">
            <span>💰</span> <span style="color: #444;">{amount}</span>
        </div>
        """, 
        unsafe_allow_html=True
    )
