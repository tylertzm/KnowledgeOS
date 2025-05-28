import torch
import numpy as np
import sounddevice as sd
import queue
import threading
import time
import os
import requests
import sys
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from dotenv import load_dotenv
from rich.console import Console # Import Console from rich
from rich.text import Text # Import Text from rich

# Initialize Rich Console
console = Console()

# Load environment variables from .env file
load_dotenv()

# Setup devices
device = "cuda:0" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

# Setup Whisper
WHISPER_MODEL_ID = "openai/whisper-large-v3-turbo"
# Use a smaller model for faster startup/testing if needed
# WHISPER_MODEL_ID = "openai/whisper-tiny.en"
whisper_processor = AutoProcessor.from_pretrained(WHISPER_MODEL_ID)
whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained(WHISPER_MODEL_ID).to(device)

# --- Groq API Setup ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    console.print("[FATAL ERROR] GROQ_API_KEY environment variable not set.", style="bold red")
    sys.exit(1)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
# ----------------------

# Audio parameters
SAMPLE_RATE = 16000
CHUNK_DURATION = 4  # seconds
OVERLAP_DURATION = 2  # seconds
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_DURATION
OVERLAP_SAMPLES = SAMPLE_RATE * OVERLAP_DURATION

audio_queue = queue.Queue()
stop_flag = threading.Event()

def audio_callback(indata, frames, time_info, status):
    if status:
        console.print(f"[AUDIO WARNING] {status}", style="bold yellow")
    # Ensure we're getting mono audio
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

def get_groq_response(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    data = {
        "model": GROQ_MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100 # Adjust as needed
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        result = response.json()
        # Extract the content from the response
        if result and result.get("choices"):
            return result["choices"][0].get("message", {}).get("content", "").strip()
        return ""
    except requests.exceptions.RequestException as e:
        console.print(f"[ERROR] Groq API request failed: {e}", style="bold red")
        return None
    except Exception as e:
        console.print(f"[ERROR] Error processing Groq API response: {e}", style="bold red")
        return None


def process_and_chat_loop():
    buffer = np.zeros((0, 1), dtype='int16')
    # print("🎯 Processing and Chat loop started...") # Removed this log
    while not stop_flag.is_set():
        try:
            # Wait for enough data in the queue
            while buffer.shape[0] < CHUNK_SAMPLES and not stop_flag.is_set():
                try:
                    chunk = audio_queue.get(timeout=0.1) # Add timeout to check stop_flag
                    buffer = np.concatenate((buffer, chunk), axis=0)
                except queue.Empty:
                    if stop_flag.is_set():
                        break
                    continue

            if stop_flag.is_set():
                # print("Stop flag set, exiting processing loop.") # Removed this log
                break

            # Process chunk
            current_chunk = buffer[:CHUNK_SAMPLES + OVERLAP_SAMPLES]
            buffer = buffer[-OVERLAP_SAMPLES:]

            # Convert to float32 and normalize for Whisper
            audio_data = current_chunk.astype(np.float32) / 32768.0
            audio_data = audio_data.flatten() # Ensure 1D

            # Transcribe using Whisper
            inputs = whisper_processor(
                audio=audio_data, # Use the numpy array directly
                sampling_rate=SAMPLE_RATE,
                return_tensors="pt"
            )
            input_features = inputs.input_features.to(device)

            with torch.no_grad():
                ids = whisper_model.generate(
                    input_features,
                    forced_decoder_ids=whisper_processor.get_decoder_prompt_ids(
                        language="en", # Changed to English based on your previous edit
                        task="transcribe" # Changed to transcribe based on your likely intent
                    )
                )
                transcription = whisper_processor.batch_decode(ids, skip_special_tokens=True)[0].strip()
                
            # Print transcription only if it's not empty or just a dot
            if transcription and transcription != '.':
                 console.print(Text(f"🗣️ You said: {transcription}", style="bold blue"))
                
                 # Send transcription to Groq API and get response
                 groq_response = get_groq_response(transcription)
                 
                 if groq_response is not None:
                    console.print(Text(f"🤖 Groq replied: {groq_response}", style="bold magenta"))

            # else: # Removed this else block as no output is desired for empty/dot transcriptions
            #      print("⏭️ Skipping Groq API call: Transcription is empty or just a dot.")

        except Exception as e:
            console.print(f"[ERROR] Processing and Chat loop failed: {e}", style="bold red")
            time.sleep(1) # Prevent rapid error looping

if __name__ == "__main__":
    # Check if API key is set after loading .env
    if not GROQ_API_KEY:
         sys.exit(1) # Exit if key is not set (message already printed)

    try:
        # Start the audio recorder thread
        recorder_thread_instance = threading.Thread(target=recorder_thread, daemon=True)
        recorder_thread_instance.start()

        # Start the main processing and chat loop in the main thread
        process_and_chat_loop()

    except KeyboardInterrupt:
        console.print("👋 Stopping...", style="bold yellow")
        stop_flag.set()
    except Exception as e:
        console.print(f"[FATAL ERROR] Main application failed: {e}", style="bold red")
    finally:
        stop_flag.set()
        console.print("✅ Shutdown complete.", style="bold green")