from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import numpy as np
import threading
import queue
import sys
import os
from config import (
    console,
    CHUNK_SAMPLES,
    OVERLAP_SAMPLES,
    GROQ_API_KEY
)
from audiohandler import AudioHandler
from transcriptions import Transcriber
from llm_handler import LLMHandler
from websearch_handler import WebSearchHandler

app = Flask(__name__)
CORS(app)

# Global state
ai_mode_active = False
websearch_mode_active = False
latest_transcription = ""
latest_response = ""

# Initialize components
audio_handler = AudioHandler()
transcriber = Transcriber()
llm_handler = LLMHandler()
websearch_handler = WebSearchHandler()

def main_loop():
    global ai_mode_active, websearch_mode_active, latest_transcription, latest_response
    
    while not audio_handler.stop_flag.is_set():
        try:
            # Get audio chunk with overlap from audio handler
            audio_data = audio_handler.get_audio_chunk()
            if audio_data is None:
                continue
                    
            transcription = transcriber.transcribe(audio_data.flatten())
            if transcription and transcription != ".":
                # Only show transcription in web search mode if it ends with a question mark
                if websearch_mode_active and not transcription.strip().endswith('?'):
                    continue

                latest_transcription = transcription
                console.print(f"🗣️ You said: {transcription}", style="bold blue")
                
                if "ai mode" in transcription.lower():
                    ai_mode_active = True
                    websearch_mode_active = False
                    latest_response = "AI mode activated"
                    continue
                elif "transcription mode" in transcription.lower():
                    ai_mode_active = False
                    websearch_mode_active = False
                    latest_response = "Transcription mode activated"
                    continue
                elif "web search mode" in transcription.lower():
                    ai_mode_active = False
                    websearch_mode_active = True
                    latest_response = "Web search mode activated"
                    continue
                
                if websearch_mode_active:
                    if transcription.strip().endswith('?'):
                        response = websearch_handler.search(transcription)
                        if response:
                            latest_response = response
                            console.print(f"🌐 Web search replied: {response}", style="bold cyan")
                elif ai_mode_active:
                    response = llm_handler.get_response(transcription)
                    if response:
                        latest_response = response
                        console.print(f"🤖 Groq replied: {response}", style="bold magenta")
                        
        except Exception as e:
            console.print(f"[ERROR] Main loop failed: {e}", style="bold red")
            audio_handler.reset_buffer()  # Reset buffer on error

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    mode = "WebSearch" if websearch_mode_active else "AI" if ai_mode_active else "Transcription"
    return jsonify({
        "mode": mode,
        "transcription": latest_transcription,
        "response": latest_response if (websearch_mode_active or ai_mode_active) else ""
    })

@app.route('/audio', methods=['OPTIONS'])
def handle_audio_options():
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response, 200

@app.route('/audio', methods=['POST'])
def handle_audio():
    if request.method == "OPTIONS":
        return handle_audio_options()
        
    try:
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

        # Convert audio data to numpy array with error handling
        try:
            audio_array = np.array(audio_data, dtype=np.float32)
        except Exception as e:
            console.print(f"[ERROR] Failed to convert audio data: {e}", style="bold red")
            return jsonify({
                'error': 'Failed to process audio data'
            }), 400

        # Check audio array validity
        if audio_array.size == 0:
            console.print("[ERROR] Empty audio data", style="bold red")
            return jsonify({
                'error': 'Empty audio data'
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
            elif websearch_mode_active and transcription.strip().endswith('?'):
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

if __name__ == "__main__":
    if not GROQ_API_KEY:
        console.print("[FATAL ERROR] GROQ_API_KEY environment variable not set.", style="bold red")
        sys.exit(1)
        
    threading.Thread(target=audio_handler.start_recording, daemon=True).start()
    threading.Thread(target=main_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)