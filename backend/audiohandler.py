import numpy as np
import sounddevice as sd
import queue
import threading
from config import console, SAMPLE_RATE, CHUNK_SAMPLES, OVERLAP_SAMPLES

class AudioHandler:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.stop_flag = threading.Event()
        self.buffer = np.zeros((0, 1), dtype='int16')

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            console.print(f"[AUDIO WARNING] {status}", style="bold yellow")
        if indata.shape[1] > 1:
            indata = indata.mean(axis=1, keepdims=True)
        self.audio_queue.put(indata.copy())

    def get_audio_chunk(self):
        """Get a chunk of audio data with overlap."""
        try:
            # Add new audio data to buffer until we have enough
            while self.buffer.shape[0] < CHUNK_SAMPLES and not self.stop_flag.is_set():
                try:
                    chunk = self.audio_queue.get(timeout=0.1)
                    self.buffer = np.concatenate((self.buffer, chunk), axis=0)
                except queue.Empty:
                    continue

            if self.stop_flag.is_set():
                return None

            # Get chunk with overlap
            current_chunk = self.buffer[:CHUNK_SAMPLES + OVERLAP_SAMPLES]
            # Keep overlap part for next chunk
            self.buffer = self.buffer[CHUNK_SAMPLES - OVERLAP_SAMPLES:]
            # Convert to float32 and normalize
            return current_chunk.astype(np.float32) / 32768.0
        except Exception as e:
            console.print(f"[ERROR] Error getting audio chunk: {e}", style="bold red")
            return None

    def start_recording(self):
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='int16',
                callback=self.audio_callback,
                blocksize=int(SAMPLE_RATE * 0.1)  # Process in smaller blocks for smoother streaming
            ):
                console.print("🎙️  Recording... Press Ctrl+C to stop.", style="bold green")
                while not self.stop_flag.is_set():
                    threading.Event().wait(0.1)
        except Exception as e:
            console.print(f"[ERROR] Audio stream failed: {e}", style="bold red")
            self.stop_flag.set()

    def reset_buffer(self):
        """Reset the audio buffer."""
        self.buffer = np.zeros((0, 1), dtype='int16')