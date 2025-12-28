import serial
import json
import time
import os
import pygame
import random
import uuid
from typing import TypedDict, Optional
from gtts import gTTS
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from state import GameState, QuestionGeneratorSchema, DomainGeneratorSchema
# --- CONFIGURATION ---
SERIAL_PORT = 'COM3'   
BAUD_RATE = 1200

STATUS_FILE = "current_state.json"

OLLAMA_MODEL = "gemma3:4b"



# --- INITIALIZATION ---
print(f"🦙 Initializing Ollama ({OLLAMA_MODEL})...")
def get_llm(temperature: float = 0):
    """
    Returns a ChatOllama instance with the specified temperature.

    Args:
        temperature (float): 0.0 for deterministic/strict, 1.0+ for creative/random.
    """
    # You can also make model_name an argument if you switch models often
    return ChatOllama(model=OLLAMA_MODEL, temperature=0)
# Try to connect to Serial (Safety check)
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    print(f"✅ Connected to {SERIAL_PORT}")
except Exception as e:
    print(f"⚠️ Serial Error: {e}. Running in simulation mode (Input might fail).")
    ser = None


# --- HELPER FUNCTIONS ---
def update_frontend(state: GameState, message: str):
    """Simulates updating the frontend by printing to console & writing file."""
    print("\n" + "="*40)
    print(f"🖥️  [FRONTEND UPDATE]")
    print(f"Question: {state.get('question', '...')}")
    print(f"Options:  {state.get('options', {})}")
    print(f"Status:   {state.get('status')}")
    print(f"Message:  {message}")
    print("="*40 + "\n")
    
    # Write file for Streamlit
    data = {
        "question": state.get("question", "Loading..."),
        "options": state.get("options", {"A": "-", "B": "-", "C": "-"}),
        "status": state.get("status", "waiting"),
        "message": message,
        # These allow the frontend to know which card to color Red/Green
        "correct_answer": state.get("correct_answer", ""), 
        "user_answer": state.get("user_answer", "")
    }
    
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def send_uart_command(command_char: str):
    """Sends a single character to the PIC18F to control the motor."""
    if ser and ser.is_open:
        try:
            ser.write(command_char.encode('utf-8'))
            print(f"📡 [UART SENT] -> '{command_char}'")
        except Exception as e:
            print(f"⚠️ UART Write Error: {e}")
    else:
        # Debug Print (if hardware is not connected)
        print(f"📡 [MOCK UART] -> '{command_char}' (Hardware not connected)")

# --- UPDATED AUDIO FUNCTION ---
def play_audio(text, is_wrong_answer=False):
    """
    Plays audio and controls hardware via UART "XYZ" protocol.
    X: Shake (1=Yes)
    Y: Talk  (1=Yes)
    Z: Light (1=Yes)
    """
    if not text:
        return
    
    print(f"🔊 [AUDIO GENERATING]: '{text}'")
    filename = "response.mp3"

    try:
        # UART Signals
        if is_wrong_answer:
            # Shake(1) + Talk(1) + Light(1)
            start_signal = "111\n"
        else:
            # Shake(0) + Talk(1) + Light(0)
            start_signal = "010\n"
            
        stop_signal = "000\n" # Reset everything when done

        # Generate MP3
        tts = gTTS(text=text, lang='en', tld='co.uk')
        tts.save(filename)
        
        # SEND START SIGNAL
        # triggers the PIC18F actions before audio starts
        send_uart_command(start_signal) 
        
        # Play Audio
        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        
        # Wait for audio to finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10) 
            
    except Exception as e:
        print(f"⚠️ Audio Error: {e}")
        
    finally:
        # SEND STOP SIGNAL
        # Turns off motor, stops shaking, turns off lights
        send_uart_command(stop_signal)
        

        if pygame.mixer.get_init():
            pygame.mixer.music.unload()
            pygame.mixer.quit()
        
        if os.path.exists(filename):
            try: os.remove(filename)
            except: pass

def read_uart_blocking():
    """Blocks execution until a valid 'A', 'B', or 'C' is received."""
    print("👂 Listening for UART input (A/B/C)...")
    buffer = ""
    while True:
        if ser and ser.in_waiting > 0:
            raw = ser.read().decode('utf-8', errors='ignore')
            if raw == '\n':
                message = buffer.strip().upper()
                buffer = "" 
                if message in ['A', 'B', 'C']:
                    print(f"📩 Received: {message}")
                    return message
            else:
                buffer += raw
        time.sleep(0.01)

# --- NODES (The Agents) ---

def domain_selection_node(state: GameState):
    print("🧠 Ollama is generating domains...")
    vibes = [
        "Pop Culture & Internet", "Obscure History", "Modern Technology", 
        "Weird Biology", "Culinary Arts", "Video Games", 
        "Space Exploration", "True Crime", "Mythology",
        "Celebrity Gossip", "Quantum Physics", "90s Music",
        "Anime & Manga", "Corporate Horror", "Extreme Sports"
    ]
    
    # pick 3 UNIQUE vibes
    # random.sample guarantees no duplicates
    selected_vibes = random.sample(vibes, 3) 
    
    print(f"--- GENERATING DOMAINS ---")
    print(f"🎨 Mixing Vibes: {selected_vibes}")
    llm = get_llm(temperature=1.7)
    seed = str(uuid.uuid4())
    # Structured Output
    structured_llm = llm.with_structured_output(DomainGeneratorSchema)
    prompt = (
        f"Random Seed: {seed}.\n"
        "We are playing a general knowledge Trivia Game. "
        f"🎨 Mixing Vibes: {selected_vibes}"
        "Generate 3 distinct, interesting topics that should change when the Random Seed changes and relate to the vibes for the player to choose from. "
        "Constraint: Each topic must be very short (1-3 words max), "
        "for example: 'World History', 'Python Coding', or 'Space Science'."
        f"Random Seed: {seed}. "
    )
    try:
        data = structured_llm.invoke(prompt)
        domain_map = {"A": data.A, "B": data.B, "C": data.C}
    except Exception as e:
        print(f"⚠️ Mock Fallback used: {e}")
        domain_map = {"A": "Science", "B": "History", "C": "Pop Culture"}

    update_frontend({
        "question": "Select a Topic",
        "options": domain_map,
        "status": "waiting"
    }, message="Press A, B, or C.")
    play_audio("Select a Topic", is_wrong_answer=False)
    # Wait for UART
    user_choice = read_uart_blocking()
    selected_domain = domain_map[user_choice]
    print(f"👉 Selected: {selected_domain}")
    
    return {"domain": selected_domain}

def question_generator_node(state: GameState):
    topic = state.get("domain", "General Knowledge")
    print(f"🧠 Ollama is generating question for: {topic}...")
    llm = get_llm(temperature=0)
    # Use schema
    structured_llm = llm.with_structured_output(QuestionGeneratorSchema)
    
    # Get history
    past_questions = state.get("asked_questions", [])
    
    # Format the list into a string
    history_context = "\n".join(f"- {q}" for q in past_questions)

    # inject 'history_context' into the prompt for new question
    prompt = (
        f"Generate a single multiple-choice trivia question about '{topic}'.\n"
        f"Avoid these previously asked questions:\n{history_context}\n\n" 
        "Strictly follow these rules:\n"
        "1. Provide exactly 3 options (A, B, C).\n"
        "2. Do NOT add option D.\n"
        "3. The correct_answer must be exactly 'A', 'B', or 'C'.\n"
        "4. Keep the JSON valid (no extra quotes)."
    )
    
    try:
        q_data = structured_llm.invoke(prompt)
        
        options_dict = {
            "A": q_data.option_a,
            "B": q_data.option_b,
            "C": q_data.option_c
        }
    except Exception as e:
        print(f"⚠️ Question Gen Error: {e}")
        # Fallback in case it still fails
        q_data = QuestionGeneratorSchema(
            question_text=f"Who is the 'father' of Python? (Fallback)", 
            option_a="Guido van Rossum", 
            option_b="Elon Musk", 
            option_c="Jeff Bezos", 
            correct_answer="A"
        )
        options_dict = {"A": "Guido van Rossum", "B": "Elon Musk", "C": "Jeff Bezos"}

    update_frontend({
        "question": q_data.question_text,
        "options": options_dict,
        "status": "waiting"
    }, message="Press the correct button!")
    play_audio(q_data.question_text, is_wrong_answer=False)
    return {
        "question": q_data.question_text,
        "options": options_dict,
        "correct_answer": q_data.correct_answer,
        "status": "waiting_for_answer",
        "asked_questions": [q_data.question_text]
    }
    
def answer_listener_node(state: GameState):
    """Step 3: Wait for user to answer."""
    user_ans = read_uart_blocking()
    return {"user_answer": user_ans}

def evaluation_node(state: GameState):
    """Step 4: Check answer, generate audio feedback."""
    is_correct = (state["user_answer"] == state["correct_answer"])
    status = "correct" if is_correct else "wrong"
    seed = str(uuid.uuid4())
    llm = get_llm(temperature=1.9)
    roast_way = ["so mean", "still using windowXP, u need upgrade", "like a dad joke", "like a Shakespearean insult", "like a stand-up comedian", "like pirate, even compass cant lead u", "my mom do better", "your  cpu needs an upgrade"]
    roast_level = random.choice(roast_way)
    print(f"--- ROAST LEVEL ---")
    print(f"{roast_level}")
    if is_correct:
        prompt = f"Random Seed: {seed}. The user answered correctly. Give them a short, enthusiastic compliment in {roast_level}(max 1 sentence)."
    else:
        prompt = f"Random Seed: {seed}. The user answered {state['user_answer']} but the answer was {state['correct_answer']}. Give them a short, sarcastic roast in {roast_level}(max 1 sentence). For example, 'HAHA! Wrong! Even a toddler knows that!'"
        
    feedback_resp = llm.invoke(prompt)
    feedback_text = feedback_resp.content
    
    # Update frontend with result
    update_frontend({
        "question": state["question"],
        "options": state["options"],
        "status": status,
        "correct_answer": state["correct_answer"],
        "user_answer": state["user_answer"]
    }, message=f"{feedback_text}")
    
    # Play Audio
    play_audio(feedback_text, is_wrong_answer=not is_correct)
    
    return {"feedback": feedback_text, "status": status}

# --- GRAPH CONSTRUCTION ---


workflow = StateGraph(GameState)

# Add Nodes
workflow.add_node("pick_domain", domain_selection_node)
workflow.add_node("generate_question", question_generator_node)
workflow.add_node("get_user_answer", answer_listener_node)
workflow.add_node("evaluate_result", evaluation_node)

# Set Entry Point
workflow.set_entry_point("pick_domain")

# Define Edges (The Flow)
workflow.add_edge("pick_domain", "generate_question")
workflow.add_edge("generate_question", "get_user_answer")
workflow.add_edge("get_user_answer", "evaluate_result")
workflow.add_edge("evaluate_result", "generate_question")

# Compile
app = workflow.compile()
def build_langgraph():
    return app
# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("🚀 LangGraph Orchestrator Started...")
    
    try:
        app.invoke({"domain": ""}, config={"recursion_limit": 1000})
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")