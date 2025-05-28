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
CHUNK_DURATION = 4  # seconds
OVERLAP_DURATION = 2  # seconds
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_DURATION
OVERLAP_SAMPLES = SAMPLE_RATE * OVERLAP_DURATION

audio_queue = queue.Queue()
stop_flag = threading.Event()

# Conversation history for AI mode
message_history = []

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
    inputs = whisper_processor(
        audio=audio_data,
        sampling_rate=SAMPLE_RATE,
        return_tensors="pt"
    )
    input_features = inputs.input_features.to(device)
    with torch.no_grad():
        ids = whisper_model.generate(
            input_features,
            # forced_decoder_ids=whisper_processor.get_decoder_prompt_ids(
            #     language="en",
            #     task="transcribe"
            #)
        )
        transcription = whisper_processor.batch_decode(ids, skip_special_tokens=True)[0].strip()
    return transcription

def get_groq_response(prompt):
    message_history.append({"role": "user", "content": prompt})
    trimmed_history = []
    user_msgs = [m for m in message_history if m["role"] == "user"]
    assistant_msgs = [m for m in message_history if m["role"] == "assistant"]
    trimmed_history.extend(user_msgs[-2:])
    if assistant_msgs:
        trimmed_history.insert(1, assistant_msgs[-1])
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=trimmed_history,
            max_tokens=100
        )
        reply = completion.choices[0].message.content.strip()
        message_history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        console.print(f"[ERROR] Groq API request failed: {e}", style="bold red")
        return None

def main_loop():
    buffer = np.zeros((0, 1), dtype='int16')
    ai_mode_active = False
    console.print("[bold yellow]Say 'ai mode' to enable LLM, 'transcription mode' to disable it.[/bold yellow]")
    while not stop_flag.is_set():
        try:
            while buffer.shape[0] < CHUNK_SAMPLES and not stop_flag.is_set():
                try:
                    chunk = audio_queue.get(timeout=0.1)
                    buffer = np.concatenate((buffer, chunk), axis=0)
                except queue.Empty:
                    if stop_flag.is_set():
                        break
                    continue
            if stop_flag.is_set():
                break
            current_chunk = buffer[:CHUNK_SAMPLES + OVERLAP_SAMPLES]
            buffer = buffer[-OVERLAP_SAMPLES:]
            audio_data = current_chunk.astype(np.float32) / 32768.0
            audio_data = audio_data.flatten()
            transcription = transcribe_audio(audio_data)
            if transcription and transcription != '.':
                console.print(Text(f"🗣️ You said: {transcription}", style="bold blue"))
                # Mode switching by voice
                if "ai mode" in transcription.lower():
                    ai_mode_active = True
                    console.print("[bold magenta]AI mode activated![/bold magenta]")
                    continue
                elif "transcription mode" in transcription.lower():
                    ai_mode_active = False
                    console.print("[bold cyan]Transcription mode activated![/bold cyan]")
                    continue
                # If in AI mode, send to LLM
                if ai_mode_active:
                    groq_response = get_groq_response(transcription)
                    if groq_response is not None:
                        console.print(Text(f"🤖 Groq replied: {groq_response}", style="bold magenta"))
        except Exception as e:
            console.print(f"[ERROR] Main loop failed: {e}", style="bold red")
            time.sleep(1)

if __name__ == "__main__":
    if not GROQ_API_KEY:
        sys.exit(1)
    try:
        recorder_thread_instance = threading.Thread(target=recorder_thread, daemon=True)
        recorder_thread_instance.start()
        main_loop()
    except KeyboardInterrupt:
        console.print("👋 Stopping...", style="bold yellow")
        stop_flag.set()
    except Exception as e:
        console.print(f"[FATAL ERROR] Main application failed: {e}", style="bold red")
    finally:
        stop_flag.set()
        console.print("✅ Shutdown complete.", style="bold green")