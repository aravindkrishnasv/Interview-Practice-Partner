import os
import base64
import tempfile
from typing import List, Dict

import streamlit as st
from dotenv import load_dotenv
from gtts import gTTS
# CHANGED: We now import speech_to_text for direct transcription
from streamlit_mic_recorder import speech_to_text
import google.generativeai as genai

# ---------------------------
# 1. Configuration & Setup
# ---------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ---------------------------
# 2. Prompts & Agent Behavior
# ---------------------------
def build_interviewer_prompt(job_role: str, persona_hint: str, num_questions: int) -> str:
    if not job_role:
        job_role = "Software Development Engineer"

    return f"""
    You are an expert technical interviewer for the role: {job_role}.
    Your goal is to conduct a realistic, human-like interview.

    **Interview Structure:**
    1.  Ask exactly ONE question at a time.
    2.  Cover these topics dynamically:
        * Technical depth (relevant to {job_role})
        * Problem-solving/Scenario-based questions
        * Behavioral (STAR method)
    3.  This interview will last for approximately {num_questions} questions.

    **Your Interaction Style:**
    * **Be Adaptive:** * If the candidate is **confused**, simplify the question or offer a hint.
        * If the candidate is **brief/efficient**, ask a deeper follow-up to test depth.
        * If the candidate is **chatty/off-topic**, politely steer them back to the question.
    * **Follow-up:** Always listen to the candidate's answer. If it's vague, ask "Can you explain that further?". If it's good, move to the next topic.
    * **Tone:** Professional, encouraging, but rigorous.

    **Demo Context (Internal Note):**
    The user is currently simulating this persona: "{persona_hint}". 
    Be prepared to handle behaviors associated with this persona.

    **Constraint:** - Do NOT provide feedback yet. 
    - Do NOT answer the question yourself. 
    - Keep responses concise (spoken conversation style).
    """

def build_evaluator_prompt(job_role: str) -> str:
    if not job_role:
        job_role = "Software Development Engineer"

    return f"""
    You are a Senior Hiring Manager evaluating a candidate for the role: {job_role}.
    
    Review the transcript below and provide structured feedback.
    
    **Evaluation Criteria:**
    1.  **Communication:** Clarity, structure, and ability to stay on topic.
    2.  **Technical Knowledge:** Depth of understanding for {job_role}.
    3.  **Problem Solving:** Approach to scenarios and logic.

    **Output Format:**
    * **Summary:** A 2-sentence overview of the candidate's performance.
    * **Strengths:** 3 bullet points citing specific examples from the chat.
    * **Areas for Improvement:** 3 bullet points with actionable advice.
    * **Overall Rating:** X/10 (Be honest and critical).
    """

# ---------------------------
# 3. Helper Functions (Audio & Logic)
# ---------------------------
def play_audio(text: str):
    if not text:
        return
    try:
        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            audio_bytes = open(fp.name, "rb").read()
        
        audio_base64 = base64.b64encode(audio_bytes).decode()
        audio_html = f"""
        <audio autoplay controls>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
        os.unlink(fp.name)
    except Exception as e:
        st.error(f"Audio playback error: {e}")

def build_transcript(messages: List[Dict]) -> str:
    lines = []
    for msg in messages:
        role = "Interviewer" if msg["role"] == "assistant" else "Candidate"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)

def get_gemini_response(system_prompt: str, chat_history: List[Dict] = None, transcript: str = None) -> str:
    if not GEMINI_API_KEY:
        return "⚠️ Error: GEMINI_API_KEY is missing."

    try:
        model = genai.GenerativeModel("gemini-2.0-flash") 

        if transcript: 
            final_prompt = f"{system_prompt}\n\nTRANSCRIPT:\n{transcript}"
            response = model.generate_content(final_prompt)
        else:
            history_text = build_transcript(chat_history) if chat_history else ""
            final_prompt = f"{system_prompt}\n\nCURRENT INTERVIEW HISTORY:\n{history_text}\n\n(Ask the next question now:)"
            response = model.generate_content(final_prompt)

        return (response.text or "").strip()
    
    except Exception as e:
        return f"⚠️ API Error: {str(e)}"

# ---------------------------
# 4. Streamlit Application
# ---------------------------
def main():
    st.set_page_config(
        page_title="Interview AI Agent",
        page_icon="🎙️",
        layout="centered"
    )

    st.title("🎙️ AI Interview Practice Partner")
    st.markdown("""
    **Assignment Submission:** Conversational AI Agent  
    *Prepare for your interview by speaking naturally. The agent will adapt to your responses.*
    """)

    if not GEMINI_API_KEY:
        st.error("🔑 Please set your GEMINI_API_KEY in the .env file to proceed.")
        st.stop()

    # --- Session State Initialization ---
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "interview_active" not in st.session_state:
        st.session_state.interview_active = False
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0
    if "feedback" not in st.session_state:
        st.session_state.feedback = None

    # --- Sidebar: Configuration & Demo Controls ---
    with st.sidebar:
        st.header("⚙️ Interview Settings")
        job_role = st.text_input("Target Role", value="Software Engineer")
        num_questions = st.slider("Interview Length (Questions)", 3, 10, 5)

        st.markdown("---")
        st.subheader("🧪 Demo Controls")
        st.info("Use these personas to demonstrate 'Adaptability' in your video submission.")
        
        persona_hint = st.selectbox(
            "Simulate Candidate Persona",
            [
                "Standard User (Balanced)",
                "The Confused User (Needs clarification)",
                "The Efficient User (Short answers)",
                "The Chatty User (Goes off-topic)",
                "The Edge Case (Invalid inputs)"
            ]
        )

        if st.button("▶️ Start / Reset Interview", type="primary"):
            st.session_state.messages = []
            st.session_state.interview_active = True
            st.session_state.question_count = 0
            st.session_state.feedback = None
            st.rerun()

    # --- Main Chat Interface ---
    
    # 1. Start the Interview
    if st.session_state.interview_active and st.session_state.question_count == 0:
        with st.spinner("AI Interviewer is reviewing your resume..."):
            initial_prompt = build_interviewer_prompt(job_role, persona_hint, num_questions)
            first_q = get_gemini_response(initial_prompt, [])
            
        st.session_state.messages.append({"role": "assistant", "content": first_q})
        st.session_state.question_count = 1
        st.rerun()

    # 2. Display Chat History
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 3. Audio Playback
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        play_audio(st.session_state.messages[-1]["content"])

    # 4. User Input Handling
    if st.session_state.interview_active and st.session_state.question_count <= num_questions:
        st.markdown("### 🗣️ Your Answer")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            # CHANGED: Using speech_to_text for direct text return
            voice_text = speech_to_text(
                start_prompt="🎤 Record",
                stop_prompt="⏹️ Stop",
                just_once=True,
                key="voice_input"
            )
        
        text_input = st.chat_input("Or type your answer here...")

        user_response = None
        # CHANGED: Check voice_text directly (it is a string)
        if voice_text:
            user_response = voice_text
        elif text_input:
            user_response = text_input

        # Process User Response
        if user_response:
            st.session_state.messages.append({"role": "user", "content": user_response})
            
            with st.spinner("Interviewer is thinking..."):
                system_prompt = build_interviewer_prompt(job_role, persona_hint, num_questions)
                ai_reply = get_gemini_response(system_prompt, st.session_state.messages)
            
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.session_state.question_count += 1
            st.rerun()

    # 5. Conclusion & Feedback
    elif st.session_state.interview_active and st.session_state.question_count > num_questions:
        st.success("✅ Interview Completed!")
        
        if st.button("📄 Generate Performance Report"):
            with st.spinner("Analyzing communication, technical depth, and behavior..."):
                transcript = build_transcript(st.session_state.messages)
                eval_prompt = build_evaluator_prompt(job_role)
                feedback = get_gemini_response(eval_prompt, transcript=transcript)
                st.session_state.feedback = feedback
    
    # 6. Display Feedback
    if st.session_state.feedback:
        st.markdown("---")
        st.subheader("📊 Evaluation Report")
        st.markdown(st.session_state.feedback)

if __name__ == "__main__":
    main()