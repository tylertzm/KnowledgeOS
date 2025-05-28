from flask import Flask, render_template, jsonify, request
import torch
import numpy as np
import sounddevice as sd
import queue
import threading
import time
import os
import sys
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from dotenv import load_dotenv
from rich.console import Console
from rich.text import Text
from groq import Groq

from flask_cors import CORS  # ✅ NEW

# Flask App Setup
app = Flask(__name__)
CORS(app)  # ✅ Allow any origin

# Initialize Rich Console
console = Console()

# Load environment variables from .env file
load_dotenv()

# Setup devices
device = "cuda:0" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

# Setup Whisper
WHISPER_MODEL_ID = "openai/whisper-large-v3-turbo"
whisper_processor = AutoProcessor.from_pretrained(WHISPER_MODEL_ID)
whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained(WHISPER_MODEL_ID).to(device)

# --- Groq API Setup ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    console.print("[FATAL ERROR] GROQ_API_KEY environment variable not set.", style="bold red")
    sys.exit(1)

client = Groq(api_key=GROQ_API_KEY)
GROQ_MODEL_NAME = "meta-llama/llama-4-maverick-17b-128e-instruct"
# ----------------------

# Audio parameters
SAMPLE_RATE = 16000
CHUNK_DURATION = 4
OVERLAP_DURATION = 2
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_DURATION
OVERLAP_SAMPLES = SAMPLE_RATE * OVERLAP_DURATION

# Global vars
audio_queue = queue.Queue()
stop_flag = threading.Event()
message_history = []
ai_mode_active = False
latest_transcription = ""
latest_response = ""

# Audio callback
def audio_callback(indata, frames, time_info, status):
    if status:
        console.print(f"[AUDIO WARNING] {status}", style="bold yellow")
    if indata.shape[1] > 1:
        indata = indata.mean(axis=1, keepdims=True)
    audio_queue.put(indata.copy())

def recorder_thread():
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16',
                            callback=audio_callback, blocksize=CHUNK_SAMPLES):
            console.print("🎙️  Recording... Press Ctrl+C to stop.", style="bold green")
            while not stop_flag.is_set():
                time.sleep(0.1)
    except Exception as e:
        console.print(f"[ERROR] Audio stream failed: {e}", style="bold red")
        stop_flag.set()

def transcribe_audio(audio_data):
    inputs = whisper_processor(audio=audio_data, sampling_rate=SAMPLE_RATE, return_tensors="pt")
    input_features = inputs.input_features.to(device)
    with torch.no_grad():
        ids = whisper_model.generate(input_features)
        return whisper_processor.batch_decode(ids, skip_special_tokens=True)[0].strip()

def get_groq_response(prompt):
    global message_history
    message_history.append({"role": "user", "content": prompt})
    trimmed = [m for m in message_history if m["role"] == "user"][-2:]
    assistant = [m for m in message_history if m["role"] == "assistant"]
    if assistant:
        trimmed.insert(1, assistant[-1])
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=trimmed,
            max_tokens=100
        )
        reply = completion.choices[0].message.content.strip()
        message_history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        console.print(f"[ERROR] Groq API request failed: {e}", style="bold red")
        return None

def main_loop():
    global ai_mode_active, latest_transcription, latest_response
    buffer = np.zeros((0, 1), dtype='int16')
    while not stop_flag.is_set():
        try:
            while buffer.shape[0] < CHUNK_SAMPLES and not stop_flag.is_set():
                try:
                    chunk = audio_queue.get(timeout=0.1)
                    buffer = np.concatenate((buffer, chunk), axis=0)
                except queue.Empty:
                    continue
            if stop_flag.is_set():
                break
            current_chunk = buffer[:CHUNK_SAMPLES + OVERLAP_SAMPLES]
            buffer = buffer[-OVERLAP_SAMPLES:]
            audio_data = current_chunk.astype(np.float32) / 32768.0
            transcription = transcribe_audio(audio_data.flatten())
            if transcription and transcription != ".":
                latest_transcription = transcription
                console.print(Text(f"🗣️ You said: {transcription}", style="bold blue"))
                if "ai mode" in transcription.lower():
                    ai_mode_active = True
                    latest_response = "AI mode activated"
                    continue
                elif "transcription mode" in transcription.lower():
                    ai_mode_active = False
                    latest_response = "Transcription mode activated"
                    continue
                if ai_mode_active:
                    response = get_groq_response(transcription + "limit: 100 words")
                    if response:
                        latest_response = response
                        console.print(Text(f"🤖 Groq replied: {response}", style="bold magenta"))
        except Exception as e:
            console.print(f"[ERROR] Main loop failed: {e}", style="bold red")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    # Log all incoming request headers for debugging
    console.print("=== Incoming Request Headers ===", style="bold cyan")
    for header, value in request.headers.items():
        console.print(f"{header}: {value}", style="cyan")
    console.print("================================", style="bold cyan")

    return jsonify({
        "mode": "AI" if ai_mode_active else "Transcription",
        "transcription": latest_transcription,
        "response": latest_response if ai_mode_active else ""
    })

if __name__ == "__main__":
    threading.Thread(target=recorder_thread, daemon=True).start()
    threading.Thread(target=main_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5001)