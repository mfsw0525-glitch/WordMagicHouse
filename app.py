# app.py
import streamlit as st
import time
from config import *
from ui_components import *
from learning_engine import le
from data_manager import dm

# Page Config
st.set_page_config(page_title="Word Magic House", page_icon="🏰", layout="centered")
inject_custom_css()

# Session State Initialization
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'user_stats' not in st.session_state:
    st.session_state.user_stats = dm.get_user_stats()
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'feedback' not in st.session_state:
    st.session_state.feedback = None
if 'spelling_attempts' not in st.session_state:
    st.session_state.spelling_attempts = 0
if 'notification_sent' not in st.session_state:
    st.session_state.notification_sent = False

import random 

# --- Helper Functions ---

def check_answer(target_id, selected_id):
    # Instant visual feedback - no API calls here
    if target_id == selected_id:
        st.session_state.feedback = (True, "Correct!")
    else:
        err_msgs = ["Try Again! 😅", "Not that one! 🛑", "Keep trying! 💪"]
        st.session_state.feedback = (False, random.choice(err_msgs))
    
    # Update local state only (instant)
    le.submit_answer(target_id, target_id == selected_id)
    st.rerun()

def check_spelling(target_id, target_word, user_input):
    if user_input.strip().lower() == target_word.lower():
        mastered = le.submit_answer(target_id, True)
        msg = "Excellent! ✍️"
        if mastered: msg += "<br><span style='font-size:1.2rem'>Mastered! 🌟</span>"
        st.session_state.feedback = (True, msg)
        st.session_state.spelling_attempts = 0 # Reset
        st.toast("Spelling Master! 📝", icon="✅")
    else:
        # Increment attempts
        st.session_state.spelling_attempts = st.session_state.get('spelling_attempts', 0) + 1
        
        if st.session_state.spelling_attempts >= SPELLING_MAX_ATTEMPTS:
            le.submit_answer(target_id, False) # Mark as wrong in engine
            msg = f"Game Over 😅<br>Answer: <b>{target_word}</b>"
            st.session_state.feedback = (False, msg)
            st.session_state.spelling_attempts = 0 # Reset
            st.toast("Better luck next time! 🥺", icon="💔")
        else:
            remaining = SPELLING_MAX_ATTEMPTS - st.session_state.spelling_attempts
            # Add dynamic timestamp or distinct visual to ensure rerender works visibly if message is same?
            # Randomizing the encouragment helps
            encourage = random.choice(["Hint: Check the letters!", "One more time!", "You can do it!", "Focus!"])
            msg = f"{encourage}<br>{remaining} tries left! 💪"
            st.session_state.feedback = (False, msg)
            st.toast(f"Incorrect! {remaining} tries left.", icon="⚠️")
            pass
            
    st.rerun()

# --- Pages ---

@st.cache_data(ttl=1800)  # Cache for 30 mins (stats change slowly)
def get_cached_stats():
    return dm.get_stats()

def home_page():
    total, new_cnt, review_cnt, learned_cnt = get_cached_stats()
    
    render_sidebar_stats(None, 0, 0)
    render_header("Word Magic House")
    
    # Stats Cards
    c1, c2 = st.columns(2)
    with c1:
        render_stat_card("Total Words", total)
    with c2:
        render_stat_card("Mastered", learned_cnt)
    
    st.write("")
    
    # Action Buttons
    c3, c4 = st.columns(2)
    with c3:
        st.markdown(f"""
        <div class="glass-card" style="padding: 15px;">
            <div style="font-size:1.1rem; font-weight:bold; color:{THEME_ACCENT}; margin-bottom:5px;">Learn New</div>
            <div style="font-size:0.9rem; opacity:0.7; margin-bottom:10px;">Goal: {WORDS_PER_SESSION} words</div>
        </div>
        """, unsafe_allow_html=True)
        cols = st.columns([1, 2, 1])
        with cols[1]:
            if st.button("🚀 Start Learning", use_container_width=True):
                count = le.start_new_session(WORDS_PER_SESSION)
                if count > 0:
                    st.session_state.page = 'learning'
                    st.rerun()
                else:
                    st.warning("No new words available!")

    with c4:
        st.markdown(f"""
        <div class="glass-card" style="padding: 15px;">
            <div style="font-size:1.1rem; font-weight:bold; color:{THEME_ACCENT}; margin-bottom:5px;">Review</div>
            <div style="font-size:0.9rem; opacity:0.7; margin-bottom:10px;">{review_cnt} due today</div>
        </div>
        """, unsafe_allow_html=True)
        cols = st.columns([1, 2, 1])
        with cols[1]:
            if st.button("🔄 Start Review", use_container_width=True):
                if review_cnt > 0:
                    le.start_review_session()
                    st.session_state.page = 'learning'
                    st.rerun()
                else:
                    st.info("No reviews due! 🎉")

def learning_page():
    # Check if session is done
    q = st.session_state.current_question
    if not q:
        q = le.get_next_question()
        if not q:
            # Session Complete
            st.session_state.page = 'summary'
            st.rerun()
        st.session_state.current_question = q
        st.session_state.feedback = None
        st.session_state.spelling_attempts = 0 # Reset attempts for new question
    
    # Render Sidebar with Session Progress
    total = len(le.session_words)
    unmastered = len([w for w in le.session_words if le.mastery_map[w['id']] < 2])
    render_sidebar_stats(le.session_type, total, total - unmastered)
        
    # Render Question Types
    q_type = q['type']
    word = q['word']
    
    # Definition Card (Prominent style)
    render_definition_card(word['definition'])
    
    # Feedback Area
    if st.session_state.feedback:
        is_correct, msg = st.session_state.feedback
        render_feedback(is_correct, msg)

        if is_correct:
            cols = st.columns([1, 1, 1])
            with cols[1]:
                if st.button("Next ➡️", key="next_btn", use_container_width=True):
                    st.session_state.current_question = None
                    st.session_state.feedback = None
                    st.rerun()
            return # Stop rendering inputs if correct
            
        else:
            if "Game Over" in msg:
                 cols = st.columns([1, 1, 1])
                 with cols[1]:
                    if st.button("Next ➡️", key="next_btn_fail", use_container_width=True):
                        st.session_state.current_question = None
                        st.session_state.feedback = None
                        st.rerun()
                 return

    # Input Area
    if q_type == 'choice' or q_type == 'matching':
        label = "Which word is this?" if q_type == 'choice' else "Match the correct word!"
        st.markdown(f'<div class="center-text">{label}</div>', unsafe_allow_html=True)
        st.write("")
        cols = st.columns([1, 2, 2, 1])
        for i, opt in enumerate(q['options']):
            col_idx = 1 if i % 2 == 0 else 2
            with cols[col_idx]:
                # Unique key prevents iPad focus/visual carryover
                btn_key = f"q_{word['id']}_{opt['id']}_{i}"
                if st.button(opt['word'], key=btn_key, use_container_width=True):
                    check_answer(word['id'], opt['id'])

    elif q_type.startswith('spelling'):
        # Use a form to capture Enter keypress
        with st.form(key='spelling_form', clear_on_submit=False):
            if q_type == 'spelling_easy':
                hint = " ".join(["_" for _ in word['word']])
                st.info(f"Hint: {len(word['word'])} letters: {hint}")
            else:
                st.info("Hint: Type the word")
                
            ans = st.text_input("Answer:", key="spelling_input")
            submit = st.form_submit_button("Check Answer")
            
            if submit:
                check_spelling(word['id'], word['word'], ans)

def summary_page():
    render_sidebar_stats(None, 0, 0)
    render_header("🎉 Session Complete!")
    st.balloons()
    
    # Send Notification if not sent
    if not st.session_state.notification_sent:
        streak = st.session_state.user_stats.get('streak_days', 1)
        dm.send_bot_notification(le.session_type, len(le.session_words), streak)
        st.session_state.notification_sent = True

    render_card(f"Great job today! You've mastered your tasks. 🌟", text_color=THEME_ACCENT)
    
    if st.button("🏠 Back Home"):
        st.session_state.page = 'home'
        st.session_state.notification_sent = False
        st.rerun()

# --- Pages ---
# ... (Keep home_page, learning_page, summary_page)


# --- Main Routing ---
if st.session_state.page == 'home':
    home_page()
elif st.session_state.page == 'learning':
    learning_page()
elif st.session_state.page == 'summary':
    summary_page()