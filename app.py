import streamlit as st
import sys
from io import StringIO

# Import your agents
from functions.agents import magic_agent, non_rag_magic_agent


# ====================================================
#   UTIL TO CAPTURE print() OUTPUT WITHOUT CHANGING
#   YOUR AGENT FUNCTIONS
# ====================================================
class ConsoleCapture:
    def __init__(self):
        self.buffer = StringIO()

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self.buffer
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._stdout

    def get_output(self):
        return self.buffer.getvalue()


# ====================================================
#                     STREAMLIT UI
# ====================================================

st.title("💬 Magic Chatbot")
st.write("Chat with a RAG-powered or non-RAG Magic: The Gathering assistant.")

# SIDEBAR SETTINGS
st.sidebar.header("⚙️ Settings")

use_rag = st.sidebar.toggle("Use RAG Agent (magic_agent)", value=True)

# Console output area
console_box = st.sidebar.container()
console_box.subheader("📜 Console output")

# Initialize chat history if missing
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ====================================================
#                    USER INPUT
# ====================================================
prompt = st.chat_input("What do you want to know, planeswalker?")

if prompt:

# Append the latest user message

    st.session_state.messages.append({"role": "user", "content": prompt})

    # Create a string representation of the history
    # This simulates passing context to a single-argument function
    context_string = ""
    # Use the last 6 messages (3 turns) for efficiency
    history_to_send = st.session_state.messages[-6:] 

    for message in history_to_send:
        # Format each message clearly for the LLM
        context_string += f"[{message['role'].upper()}]: {message['content']}\n"
    
    # Prepend an instruction and the formatted history to the new prompt
    final_prompt_with_history = (
        "CONSIDER THIS CONVERSATION HISTORY TO FORMULATE YOUR NEXT RESPONSE:\n\n"
        f"{context_string}\n\n"
        "--- END HISTORY ---"
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Capture console output from the agent
    with ConsoleCapture() as cap:
        if use_rag:
            response_text = magic_agent(prompt, verbose=True)
        else:
            response_text = non_rag_magic_agent(prompt, verbose=True)

    console_output = cap.get_output()
    console_box.write(console_output)

    # STREAMING RESPONSE (simulated character-by-character)
    with st.chat_message("assistant"):
        response_area = st.empty()
        streamed = ""

        for ch in response_text:
            streamed += ch
            response_area.markdown(streamed)

        final_text = streamed

    st.session_state.messages.append({"role": "assistant", "content": final_text})
