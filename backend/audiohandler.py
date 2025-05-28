import numpy as np
import sounddevice as sd
import queue
import threading
from config import console, SAMPLE_RATE, CHUNK_SAMPLES

class AudioHandler:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.stop_flag = threading.Event()

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            console.print(f"[AUDIO WARNING] {status}", style="bold yellow")
        if indata.shape[1] > 1:
            indata = indata.mean(axis=1, keepdims=True)
        self.audio_queue.put(indata.copy())

    def start_recording(self):
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='int16',
                callback=self.audio_callback,
                blocksize=CHUNK_SAMPLES
            ):
                console.print("🎙️  Recording... Press Ctrl+C to stop.", style="bold green")
                while not self.stop_flag.is_set():
                    threading.Event().wait(0.1)
        except Exception as e:
            console.print(f"[ERROR] Audio stream failed: {e}", style="bold red")
            self.stop_flag.set()