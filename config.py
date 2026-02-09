# config.py
import os
import streamlit as st

# --- Feishu Configuration ---
# All sensitive info is now stored in Streamlit Secrets for safety.
# Local: .streamlit/secrets.toml (Excluded from Git)
# Cloud: Streamlit Dashboard -> Settings -> Secrets
def get_secret(key, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default

FEISHU_APP_ID = get_secret("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = get_secret("FEISHU_APP_SECRET", "")
FEISHU_BASE_TOKEN = get_secret("FEISHU_BASE_TOKEN", "")
FEISHU_TABLE_ID = get_secret("FEISHU_TABLE_ID", "")
FEISHU_USER_STATS_TABLE_ID = get_secret("FEISHU_USER_STATS_TABLE_ID", "")
FEISHU_WEBHOOK = get_secret("FEISHU_WEBHOOK", "")

# --- Learning Settings ---
WORDS_PER_SESSION = 20

# --- Ebbinghaus Intervals (Days) ---
REVIEW_INTERVALS = [1, 2, 4, 7, 15, 30]

# --- UI Theme Colors (Grey & Light Blue) ---
THEME_COLOR_PRIMARY = "#89C4F4"   # Light Blue
THEME_COLOR_SECONDARY = "#E0E5EC" # Greyish
THEME_TEXT_PRIMARY = "#2C3E50"    # Dark Blue-Grey
THEME_TEXT_SECONDARY = "#5D6D7E"  # Lighter Grey for definitions
THEME_ACCENT = "#F39C12"          # Orange for highlights/numbers
THEME_CORRECT = "#27AE60"         # Green for correct
THEME_WRONG = "#E74C3C"           # Red for wrong
THEME_BACKGROUND_GRADIENT = "linear-gradient(180deg, #E0E5EC 0%, #D4E6F1 100%)" # Grey to Light Blue

# --- Logic Settings ---
SPELLING_MAX_ATTEMPTS = 3
