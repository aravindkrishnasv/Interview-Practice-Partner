# 🎙️ AI Interview Practice Partner

## Overview
This project is a conversational AI agent designed to help users prepare for technical job interviews. Built for the **Eightfold AI Agent Building Assignment** (Problem Statement 2), it simulates a real-time voice-based interview, adapts to candidate behavior, and provides structured post-interview feedback.

**Live Demo:** [Insert Link to Video or App if hosted]

---

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.9+
- A Google Gemini API Key

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-link>
   cd <repo-name>

2. **Create and activate a virtual environment:**
  # Windows
    python -m venv venv
    .\venv\Scripts\activate

  # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate

3. **Install dependencies:**
  pip install -r requirements.txt

4. **Configure Environment: Create a .env file in the root directory and add your API key:**
  GEMINI_API_KEY=your_actual_api_key_here

5. **Run the Application:**
  streamlit run app.py

🏗️ **Architecture Notes**
  The application follows a Stateful Multi-Agent Architecture powered by Streamlit and Google Gemini.

  Input Layer:
    Voice: Captures audio via browser-native APIs (streamlit-mic-recorder). Speech-to-text conversion happens on the client side to minimize latency.
    Text: Fallback text input is provided for accessibility and debugging.

  Orchestration Layer (Streamlit):

    Manages Session State to persist conversation history across UI re-renders.
    Controls the flow between the "Interview Phase" (interactive) and the "Evaluation Phase" (static analysis).

  Intelligence Layer (Gemini 2.0 Flash):

    Interviewer Agent: Dynamically generates questions based on chat history and specific persona instructions. It is restricted from giving feedback during the interview to maintain realism.
    Evaluator Agent: A separate system prompt that analyzes the full transcript after the session to generate the performance report.

  Output Layer:
    TTS Engine: Uses gTTS (Google Text-to-Speech) to generate audio responses, fulfilling the assignment's "Voice Preferred" requirement.

**Design Decisions & Reasoning**
  Per the assignment evaluation criteria, the following technical decisions were made to prioritize Conversational Quality and Adaptability:

  1. **Choice of Model: Gemini 2.0 Flash**
    Decision: I selected the Flash model over Pro.
    Reasoning: Voice-based interactions require near-instant responses to feel natural. The "Flash" model offers the best trade-off between low latency (speed) and high reasoning capability for technical topics.

  2. **Separation of "Interviewer" and "Evaluator" Prompts**
    Decision: Using two distinct system prompts rather than one continuous context.
    Reasoning: To prevent "role leakage."
    During the interview, the Interviewer Agent is strictly forbidden from giving feedback. This ensures the user feels the pressure of a real interview.
    The Evaluator Agent is instantiated only at the end to review the transcript objectively.

  3. **"Persona Hint" System for Adaptability**
    Decision: Implementation of a "Persona Injection" mechanism in the sidebar.
    Reasoning: To demonstrate Agentic Behavior and the ability to handle multiple user personas .
    Implementation: The system prompt dynamically receives a hint (e.g., "The Confused User").
    Result: Instead of a rigid script, the AI adapts: offering hints to confused users, pushing efficient users for more depth, or steering chatty users back to the topic.

  4. **Direct Speech-to-Text Transcription**
    Decision: Using speech_to_text (browser-based) instead of backend audio processing.
    Reasoning: Sending raw audio files to a server adds significant latency. Client-side transcription ensures the text is ready immediately, keeping the conversation fluid and mimicking a real human interaction.

📂 Project Structure
├── app.py                # Main application logic & UI
├── requirements.txt      # Python dependencies
├── .env                  # API keys (local only)
└── README.md             # Documentation & Design Decisions