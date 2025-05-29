from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
from config import console, GROQ_API_KEY
from llm_handler import LLMHandler
from websearch_handler import WebSearchHandler
import numpy as np
from transcriptions import Transcriber

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [
            # Main Vercel deployment
            "https://knowledgeos.vercel.app",
            # Preview deployments
            r"https://*-tylertzms-projects.vercel.app",
            r"https://*.vercel.app",
            # Specific preview deployment
            "https://knowledgeos-esjegthix-tylertzms-projects.vercel.app",
            # Local development
            "http://localhost:3000",
            # Firebase deployment
            "https://knowledgeos.web.app"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept", "Authorization"],
        "max_age": 3600,
        "supports_credentials": True,
        "expose_headers": ["Content-Type", "Authorization"]
    }
})

# Global state
ai_mode_active = True
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
    mode = "WebSearch" if websearch_mode_active else "AI" if ai_mode_active else "Transcription"
    return jsonify({
        "mode": mode,
        "transcription": latest_transcription,
        "response": latest_response
    })

@app.route("/process", methods=["POST"])
def process():
    global ai_mode_active, websearch_mode_active, latest_transcription, latest_response
    
    data = request.json
    text = data.get("text", "")
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
        
    latest_transcription = text
    
    if "ai mode" in text.lower():
        ai_mode_active = True
        websearch_mode_active = False
        latest_response = "AI mode activated"
    elif "web search mode" in text.lower():
        ai_mode_active = False
        websearch_mode_active = True
        latest_response = "Web search mode activated"
    elif websearch_mode_active and text.strip().endswith("?"):
        response = websearch_handler.search(text)
        if response:
            latest_response = response
    elif ai_mode_active:
        response = llm_handler.get_response(text)
        if response:
            latest_response = response
            
    return jsonify({
        "mode": "WebSearch" if websearch_mode_active else "AI",
        "transcription": latest_transcription,
        "response": latest_response
    })

# Add an OPTIONS handler for the /audio endpoint
@app.route('/audio', methods=['OPTIONS'])
def handle_audio_options():
    response = jsonify({'status': 'ok'})
    # Use the request's origin if it's in our allowed origins
    origin = request.headers.get('Origin')
    if origin in [
        "https://knowledgeos.vercel.app",
        "https://knowledgeos-esjegthix-tylertzms-projects.vercel.app",
        "http://localhost:3000",
        "https://knowledgeos.web.app"
    ] or origin.endswith('-tylertzms-projects.vercel.app') or origin.endswith('.vercel.app'):
        response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Expose-Headers', 'Content-Type,Authorization')
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

if __name__ == "__main__":
    if not GROQ_API_KEY:
        console.print("[FATAL ERROR] GROQ_API_KEY environment variable not set.", style="bold red")
        exit(1)
        
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)