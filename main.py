import torch
import numpy as np
import sounddevice as sd
import queue
import threading
import time
import os
import sys
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

device = "cuda:0" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

WHISPER_MODEL_ID = "openai/whisper-large-v3-turbo"
whisper_processor = AutoProcessor.from_pretrained(WHISPER_MODEL_ID)
whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained(WHISPER_MODEL_ID).to(device)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("[FATAL ERROR] GROQ_API_KEY environment variable not set.")
    sys.exit(1)

client = Groq(api_key=GROQ_API_KEY)
GROQ_MODEL_NAME = "meta-llama/llama-4-maverick-17b-128e-instruct"

SAMPLE_RATE = 16000
CHUNK_DURATION = 4
OVERLAP_DURATION = 2
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_DURATION
OVERLAP_SAMPLES = SAMPLE_RATE * OVERLAP_DURATION

audio_queue = queue.Queue()
stop_flag = threading.Event()
message_history = []

def audio_callback(indata, frames, time_info, status):
    if indata.shape[1] > 1:
        indata = indata.mean(axis=1, keepdims=True)
    audio_queue.put(indata.copy())

def recorder_thread():
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16',
                            callback=audio_callback, blocksize=CHUNK_SAMPLES):
            while not stop_flag.is_set():
                time.sleep(0.1)
    except Exception as e:
        print(f"[ERROR] Audio stream failed: {e}")
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
            # )
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
        return f"[ERROR] Groq API request failed: {e}"

# --- GUI code ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("KnowledgeOS Voice GUI")
        self.text = ScrolledText(root, wrap=tk.WORD, width=80, height=30, font=("Menlo", 12))
        self.text.pack(expand=True, fill=tk.BOTH)
        self.text.config(state=tk.DISABLED)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.pulse_active = False
        self.pulse_state = False
        self.default_bg = self.root.cget("bg")
        self.pulse_colors = ["#ffe6f7", "#e0c3fc"]  # Soft pulsing colors

        self.thread = threading.Thread(target=main_loop, args=(self.print_to_gui, self), daemon=True)
        self.thread.start()
        self.recorder_thread = threading.Thread(target=recorder_thread, daemon=True)
        self.recorder_thread.start()

    def print_to_gui(self, msg):
        def append():
            self.text.config(state=tk.NORMAL)
            self.text.insert(tk.END, msg)
            self.text.see(tk.END)
            self.text.config(state=tk.DISABLED)
        self.root.after(0, append)

    def start_pulse(self):
        if not self.pulse_active:
            self.pulse_active = True
            self._pulse()

    def stop_pulse(self):
        self.pulse_active = False
        self.root.configure(bg=self.default_bg)
        self.text.configure(bg=self.default_bg)

    def _pulse(self):
        if self.pulse_active:
            color = self.pulse_colors[self.pulse_state]
            self.root.configure(bg=color)
            self.text.configure(bg=color)
            self.pulse_state = not self.pulse_state
            self.root.after(500, self._pulse)  # Change color every 500ms

    def on_close(self):
        stop_flag.set()
        self.root.destroy()

# Modify main_loop to accept the app instance and control pulsing
def main_loop(gui_callback, app):
    buffer = np.zeros((0, 1), dtype='int16')
    ai_mode_active = False
    gui_callback("Say 'ai mode' to enable LLM, 'transcription mode' to disable it.\n")
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
                gui_callback(f"🗣️ You said: {transcription}\n")
                # Mode switching by voice
                if "ai mode" in transcription.lower():
                    ai_mode_active = True
                    gui_callback("[AI mode activated!]\n")
                    app.start_pulse()  # Start pulsing background
                    continue
                elif "transcription mode" in transcription.lower():
                    ai_mode_active = False
                    gui_callback("[Transcription mode activated!]\n")
                    app.stop_pulse()  # Stop pulsing background
                    continue
                # If in AI mode, send to LLM
                if ai_mode_active:
                    groq_response = get_groq_response(transcription)
                    if groq_response is not None:
                        gui_callback(f"🤖 Groq replied: {groq_response}\n")
        except Exception as e:
            gui_callback(f"[ERROR] Main loop failed: {e}\n")
            time.sleep(1)

if __name__ == "__main__":
    if not GROQ_API_KEY:
        sys.exit(1)
    root = tk.Tk()
    app = App(root)
    root.mainloop()