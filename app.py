import streamlit as st
import json
import time
import os

# --- Page Setup ---
st.set_page_config(page_title="AI Trivia", layout="wide", initial_sidebar_state="collapsed")

# --- CSS Styling ---
st.markdown("""
    <style>
    .question-box {
        background-color: #2C3E50;
        color: #ECF0F1;
        padding: 30px;
        border-radius: 15px;
        font-size: 36px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .option-card {
        border-radius: 10px;
        padding: 20px;
        font-size: 28px;
        text-align: center;
        color: #2C3E50;
        height: 150px; 
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .opt-label {
        font-weight: bold;
        font-size: 32px;
        margin-right: 10px;
    }
    .status-msg {
        margin-top: 30px;
        font-size: 24px;
        text-align: center;
        font-style: italic;
        min-height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- File Handling ---
STATUS_FILE = "current_state.json"

def load_data():
    if not os.path.exists(STATUS_FILE):
        return None
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

# --- Logic: Determine Color ---
def get_card_style(option_key, data):
    """
    Returns the CSS style string for a card based on game state.
    """
    status = data.get("status", "waiting")
    
    # SAFEGUARDS: Handle missing keys and strip whitespace
    correct_ans = str(data.get("correct_answer", "")).strip().upper()
    user_ans = str(data.get("user_answer", "")).strip().upper()
    option_key = option_key.upper()
    
    # Default Style (White)
    bg_color = "#FFFFFF"
    border_color = "#BDC3C7"
    
    # Logic
    if status == "correct":
        if option_key == correct_ans:
            bg_color = "#D5F5E3" # Light Green
            border_color = "#27AE60" # Dark Green

    elif status == "wrong":
        if option_key == correct_ans:
            bg_color = "#D5F5E3" # Light Green (Show the right one)
            border_color = "#27AE60" 
        elif option_key == user_ans:
            bg_color = "#FADBD8" # Light Red (Show the mistake)
            border_color = "#E74C3C" # Dark Red

    return f"background-color: {bg_color}; border: 3px solid {border_color};"

# --- Debug Sidebar ---
debug_mode = st.sidebar.checkbox("Show Raw JSON (Debug)", value=False)

# --- Main Loop ---
st.title("🤖 Interactive AI Trivia")
placeholder = st.empty() 

while True:
    data = load_data()
    
    if data is None:
        with placeholder.container():
            st.warning("⏳ Waiting for Backend Orchestrator...")
        time.sleep(1)
        continue

    # Render UI
    with placeholder.container():
        
        # DEBUG VIEW: Check if keys exist!
        if debug_mode:
            st.json(data)

        # 1. Question
        st.markdown(f'<div class="question-box">{data.get("question", "Loading...")}</div>', unsafe_allow_html=True)
        
        # 2. Options
        c1, c2, c3 = st.columns(3)
        options = data.get("options", {})
        
        # A
        with c1:
            style = get_card_style("A", data)
            st.markdown(f'<div class="option-card" style="{style}"><div><span class="opt-label" style="color:#34495E;">A.</span>{options.get("A", "")}</div></div>', unsafe_allow_html=True)
        # B
        with c2:
            style = get_card_style("B", data)
            st.markdown(f'<div class="option-card" style="{style}"><div><span class="opt-label" style="color:#34495E;">B.</span>{options.get("B", "")}</div></div>', unsafe_allow_html=True)
        # C
        with c3:
            style = get_card_style("C", data)
            st.markdown(f'<div class="option-card" style="{style}"><div><span class="opt-label" style="color:#34495E;">C.</span>{options.get("C", "")}</div></div>', unsafe_allow_html=True)

        # 3. Status Message
        status = data.get("status", "")
        msg_color = "#7F8C8D"
        
        if status == "correct":
            msg_color = "#27AE60"
            
        elif status == "wrong":
            msg_color = "#C0392B"

        unique_id = f"msg_{int(time.time() * 1000)}"
        st.markdown(
            f'<div id="{unique_id}" class="status-msg" style="color:{msg_color};">'
            f'{data.get("message", "")}'
            f'</div>', 
            unsafe_allow_html=True
        )
        if status == "correct":
            st.balloons()
    time.sleep(0.5)