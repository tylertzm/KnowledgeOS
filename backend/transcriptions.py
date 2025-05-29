from groq import Groq
import numpy as np
import soundfile as sf
import os
from config import console, GROQ_API_KEY, GROQ_WHISPER_MODEL

class Transcriber:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def transcribe(self, audio_data):
        """
        Transcribe audio data using Groq's Whisper API
        """
        try:
            # Debug logging
            console.print(f"[DEBUG] Input audio data shape: {audio_data.shape}", style="blue")
            console.print(f"[DEBUG] Input audio data type: {audio_data.dtype}", style="blue")
            console.print(f"[DEBUG] Audio range: [{audio_data.min():.3f}, {audio_data.max():.3f}]", style="blue")
            
            # Normalize audio if needed
            if audio_data.max() > 1.0 or audio_data.min() < -1.0:
                audio_data = np.clip(audio_data, -1.0, 1.0)
                console.print("[DEBUG] Audio data clipped to [-1, 1]", style="blue")
            
            # Convert numpy array to temporary file
            temp_file = "temp_audio.wav"
            sf.write(temp_file, audio_data, samplerate=16000)
            
            # Verify the written file
            file_info = sf.info(temp_file)
            console.print(f"[DEBUG] WAV file info: {file_info}", style="blue")
            
            with open(temp_file, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(temp_file, file.read()),
                    model=GROQ_WHISPER_MODEL,
                    response_format="verbose_json"
                )
            
            # Clean up temp file
            os.remove(temp_file)
            
            if not transcription or not transcription.text:
                console.print("[WARNING] No transcription generated", style="yellow")
                return None
                
            console.print(f"[SUCCESS] Transcribed: {transcription.text}", style="green")
            return transcription.text
            
        except Exception as e:
            console.print(f"[ERROR] Transcription failed: {e}", style="bold red")
            return None