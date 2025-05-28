import os
from dotenv import load_dotenv
import torch
from rich.console import Console

# Load environment variables
load_dotenv()

# Console setup
console = Console()

# Device setup
DEVICE = "cuda:0" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

# Whisper setup
WHISPER_MODEL_ID = "openai/whisper-large-v3-turbo"

# Groq setup
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL_NAME = "meta-llama/llama-4-maverick-17b-128e-instruct"

# Audio parameters
SAMPLE_RATE = 16000
CHUNK_DURATION = 4
OVERLAP_DURATION = 2
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_DURATION
OVERLAP_SAMPLES = SAMPLE_RATE * OVERLAP_DURATION