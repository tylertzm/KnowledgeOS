from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
from config import console, GROQ_API_KEY
from llm_handler import LLMHandler
from websearch_handler import WebSearchHandler
import numpy as np
from transcriptions import Transcriber
from collections import defaultdict
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins for now
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept", "Authorization", "Origin", "X-Requested-With", "Session-Id"],  # Added "Session-Id"
        "expose_headers": ["Content-Type", "Authorization"],
        "max_age": 3600,
        "supports_credentials": False  # Changed to False since we're using * for origins
    }
})

# Initialize SQLite database
DB_PATH = "sessions.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            ai_mode_active INTEGER DEFAULT 0,
            websearch_mode_active INTEGER DEFAULT 0,
            latest_transcription TEXT DEFAULT '',
            latest_response TEXT DEFAULT '',
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_session(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    session = cursor.fetchone()
    conn.close()
    return session

def create_or_update_session(session_id, ai_mode_active, websearch_mode_active, latest_transcription, latest_response):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (session_id, ai_mode_active, websearch_mode_active, latest_transcription, latest_response, last_active)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(session_id) DO UPDATE SET
            ai_mode_active = excluded.ai_mode_active,
            websearch_mode_active = excluded.websearch_mode_active,
            latest_transcription = excluded.latest_transcription,
            latest_response = excluded.latest_response,
            last_active = CURRENT_TIMESTAMP
    """, (session_id, ai_mode_active, websearch_mode_active, latest_transcription, latest_response))
    conn.commit()
    conn.close()

def delete_inactive_sessions():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cutoff_time = datetime.now() - timedelta(minutes=30)  # Inactive for 30 minutes
        cursor.execute("DELETE FROM sessions WHERE last_active < ?", (cutoff_time,))
        conn.commit()
        conn.close()
    except sqlite3.OperationalError as e:
        console.print(f"[ERROR] Failed to delete inactive sessions: {e}", style="bold red")
        init_db()  # Reinitialize the database if the table is missing

@app.before_first_request
def initialize_database():
    console.print("[INFO] Initializing database...", style="bold green")
    try:
        init_db()
    except Exception as e:
        console.print(f"[ERROR] Failed to initialize database: {e}", style="bold red")

@app.before_request
def cleanup_sessions():
    delete_inactive_sessions()

# Session-specific state
sessions = defaultdict(lambda: {
    "ai_mode_active": False,
    "websearch_mode_active": False,
    "latest_transcription": "",
    "latest_response": "",
})

# Global state
ai_mode_active = False
websearch_mode_active = False
latest_transcription = ""
latest_response = ""

# Initialize handlers
llm_handler = LLMHandler()
websearch_handler = WebSearchHandler()
transcriber = Transcriber()

@app.route("/")
def index():
    return jsonify({"status": "ok"})

@app.route("/status")
def status():
    session_id = request.headers.get("Session-Id")
    if not session_id:
        return jsonify({"error": "Session-Id header is required"}), 400

    session = get_session(session_id)
    if not session:
        # Create a new session if it doesn't exist
        create_or_update_session(session_id, 0, 0, "", "")
        session = (session_id, 0, 0, "", "", datetime.now())

    mode = "WebSearch" if session[2] else "AI" if session[1] else "Transcription"
    return jsonify({
        "mode": mode,
        "transcription": session[3],
        "response": session[4]
    })

@app.route("/process", methods=["POST"])
def process():
    session_id = request.headers.get("Session-Id")
    if not session_id:
        return jsonify({"error": "Session-Id header is required"}), 400

    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    data = request.json
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    ai_mode_active = session[1]
    websearch_mode_active = session[2]
    latest_transcription = text
    latest_response = ""

    if "ai mode" in text.lower():
        ai_mode_active = 1
        websearch_mode_active = 0
        latest_response = "AI mode activated"
    elif "web search mode" in text.lower():
        ai_mode_active = 0
        websearch_mode_active = 1
        latest_response = "Web search mode activated"
    elif websearch_mode_active and text.strip().endswith("?"):
        latest_response = f"Web search result for: {text}"  # Placeholder
    elif ai_mode_active:
        latest_response = f"AI response for: {text}"  # Placeholder

    create_or_update_session(session_id, ai_mode_active, websearch_mode_active, latest_transcription, latest_response)

    mode = "WebSearch" if websearch_mode_active else "AI" if ai_mode_active else "Transcription"
    return jsonify({
        "mode": mode,
        "transcription": latest_transcription,
        "response": latest_response
    })

# Add an OPTIONS handler for the /audio endpoint
@app.route('/audio', methods=['OPTIONS'])
def handle_audio_options():
    response = jsonify({'status': 'ok'})
    origin = request.headers.get('Origin', '*')
    response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept, Authorization, Origin, X-Requested-With, Session-Id')  # Added "Session-Id"
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.add('Access-Control-Max-Age', '3600')
    response.headers.add('Access-Control-Expose-Headers', 'Content-Type, Authorization')
    return response, 200

@app.route('/audio', methods=['POST'])
def handle_audio():
    if request.method == "OPTIONS":
        return handle_audio_options()
        
    try:
        # Log incoming request
        console.print("[INFO] Received audio request", style="bold blue")
        
        data = request.json
        if not data or 'audio' not in data:
            console.print("[ERROR] No audio data in request", style="bold red")
            return jsonify({
                'error': 'No audio data received'
            }), 400

        audio_data = data['audio']
        
        # Validate audio data
        if not isinstance(audio_data, list):
            console.print("[ERROR] Invalid audio data format", style="bold red")
            return jsonify({
                'error': 'Invalid audio data format'
            }), 400

        # Convert audio data to numpy array with error handling and detailed logging
        try:
            audio_array = np.array(audio_data, dtype=np.float32)
            console.print(f"[DEBUG] Audio array shape: {audio_array.shape}", style="blue")
            console.print(f"[DEBUG] Audio array dtype: {audio_array.dtype}", style="blue")
            console.print(f"[DEBUG] Audio array range: [{audio_array.min()}, {audio_array.max()}]", style="blue")
            console.print(f"[DEBUG] Non-zero values: {np.count_nonzero(audio_array)}/{audio_array.size}", style="blue")
        except Exception as e:
            console.print(f"[ERROR] Failed to convert audio data: {e}", style="bold red")
            console.print(f"[DEBUG] Raw audio data type: {type(audio_data)}", style="yellow")
            console.print(f"[DEBUG] Raw audio data length: {len(audio_data)}", style="yellow")
            console.print(f"[DEBUG] First few values: {audio_data[:10]}", style="yellow")
            return jsonify({
                'error': 'Failed to process audio data'
            }), 400

        # Check audio array validity
        if audio_array.size == 0:
            console.print("[ERROR] Empty audio data", style="bold red")
            return jsonify({
                'error': 'Empty audio data'
            }), 400
            
        # Check if audio data contains actual signal
        if np.allclose(audio_array, 0):
            console.print("[WARNING] Audio data contains only zeros", style="yellow")
            return jsonify({
                'error': 'Silent audio data'
            }), 400

        console.print(f"[INFO] Processing audio data of length {len(audio_data)}", style="bold green")
        
        # Process the audio (transcribe)
        try:
            transcription = transcriber.transcribe(audio_array)
            if not transcription:
                console.print("[ERROR] Transcription failed", style="bold red")
                return jsonify({
                    'error': 'Transcription failed'
                }), 500
        except Exception as e:
            console.print(f"[ERROR] Transcription error: {e}", style="bold red")
            return jsonify({
                'error': 'Transcription failed',
                'details': str(e)
            }), 500

        # Update global state
        global ai_mode_active, websearch_mode_active, latest_transcription, latest_response
        latest_transcription = transcription
        
        # Process the transcription based on mode
        try:
            if "ai mode" in transcription.lower():
                ai_mode_active = True
                websearch_mode_active = False
                latest_response = "AI mode activated"
            elif "web search mode" in transcription.lower():
                ai_mode_active = False
                websearch_mode_active = True
                latest_response = "Web search mode activated"
            elif websearch_mode_active and transcription.strip().endswith("?"):
                response = websearch_handler.search(transcription)
                if response:
                    latest_response = response
            elif ai_mode_active:
                response = llm_handler.get_response(transcription)
                if response:
                    latest_response = response
        except Exception as e:
            console.print(f"[ERROR] Response processing failed: {e}", style="bold red")
            return jsonify({
                'error': 'Failed to process response',
                'details': str(e)
            }), 500

        console.print("[SUCCESS] Audio processed successfully", style="bold green")
        return jsonify({
            'success': True,
            'transcription': transcription,
            'response': latest_response,
            'mode': "WebSearch" if websearch_mode_active else "AI"
        })

    except Exception as e:
        console.print(f"[ERROR] Unexpected error: {e}", style="bold red")
        return jsonify({
            'error': 'Unexpected error',
            'details': str(e)
        }), 500

@app.before_first_request
def initialize_database():
    console.print("[INFO] Initializing database...", style="bold green")
    try:
        init_db()
    except Exception as e:
        console.print(f"[ERROR] Failed to initialize database: {e}", style="bold red")

@app.before_request
def cleanup_sessions():
    delete_inactive_sessions()

if __name__ == "__main__":
    try:
        init_db()  # Ensure the database is initialized before the app starts
    except Exception as e:
        console.print(f"[FATAL ERROR] Failed to initialize database: {e}", style="bold red")
        exit(1)

    if not GROQ_API_KEY:
        console.print("[FATAL ERROR] GROQ_API_KEY environment variable not set.", style="bold red")
        exit(1)
        
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)