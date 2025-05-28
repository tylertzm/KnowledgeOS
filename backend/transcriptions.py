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
            # Convert numpy array to temporary file
            temp_file = "temp_audio.wav"
            sf.write(temp_file, audio_data, samplerate=16000)
            
            with open(temp_file, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(temp_file, file.read()),
                    model=GROQ_WHISPER_MODEL,
                    response_format="verbose_json"
                )
            
            # Clean up temp file
            os.remove(temp_file)
            
            return transcription.text
            
        except Exception as e:
            console.print(f"[ERROR] Transcription failed: {e}", style="bold red")
            return None