from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import numpy as np
import threading
import queue
import sys
from config import (
    console,
    CHUNK_SAMPLES,
    OVERLAP_SAMPLES,
    GROQ_API_KEY
)
from audiohandler import AudioHandler
from transcriptions import Transcriber
from llm_handler import LLMHandler

app = Flask(__name__)
CORS(app)

# Global state
ai_mode_active = False
latest_transcription = ""
latest_response = ""

# Initialize components
audio_handler = AudioHandler()
transcriber = Transcriber()
llm_handler = LLMHandler()

def main_loop():
    global ai_mode_active, latest_transcription, latest_response
    buffer = np.zeros((0, 1), dtype='int16')
    
    while not audio_handler.stop_flag.is_set():
        try:
            while buffer.shape[0] < CHUNK_SAMPLES and not audio_handler.stop_flag.is_set():
                try:
                    chunk = audio_handler.audio_queue.get(timeout=0.1)
                    buffer = np.concatenate((buffer, chunk), axis=0)
                except queue.Empty:
                    continue
                    
            if audio_handler.stop_flag.is_set():
                break
                
            current_chunk = buffer[:CHUNK_SAMPLES + OVERLAP_SAMPLES]
            buffer = buffer[-OVERLAP_SAMPLES:]
            audio_data = current_chunk.astype(np.float32) / 32768.0
            
            transcription = transcriber.transcribe(audio_data.flatten())
            if transcription and transcription != ".":
                latest_transcription = transcription
                console.print(f"🗣️ You said: {transcription}", style="bold blue")
                
                if "ai mode" in transcription.lower():
                    ai_mode_active = True
                    latest_response = "AI mode activated"
                    continue
                elif "transcription mode" in transcription.lower():
                    ai_mode_active = False
                    latest_response = "Transcription mode activated"
                    continue
                    
                if ai_mode_active:
                    response = llm_handler.get_response(transcription)
                    if response:
                        latest_response = response
                        console.print(f"🤖 Groq replied: {response}", style="bold magenta")
                        
        except Exception as e:
            console.print(f"[ERROR] Main loop failed: {e}", style="bold red")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    return jsonify({
        "mode": "AI" if ai_mode_active else "Transcription",
        "transcription": latest_transcription,
        "response": latest_response if ai_mode_active else ""
    })

if __name__ == "__main__":
    if not GROQ_API_KEY:
        console.print("[FATAL ERROR] GROQ_API_KEY environment variable not set.", style="bold red")
        sys.exit(1)
        
    threading.Thread(target=audio_handler.start_recording, daemon=True).start()
    threading.Thread(target=main_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5001)