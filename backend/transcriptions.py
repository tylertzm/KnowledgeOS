import torch
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from config import DEVICE, WHISPER_MODEL_ID

class Transcriber:
    def __init__(self):
        self.processor = AutoProcessor.from_pretrained(WHISPER_MODEL_ID)
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(WHISPER_MODEL_ID).to(DEVICE)

    def transcribe(self, audio_data):
        inputs = self.processor(
            audio=audio_data,
            sampling_rate=16000,
            return_tensors="pt"
        )
        input_features = inputs.input_features.to(DEVICE)
        with torch.no_grad():
            ids = self.model.generate(input_features)
            return self.processor.batch_decode(ids, skip_special_tokens=True)[0].strip()