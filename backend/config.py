"""
Configuration settings for the KnowledgeOS application.
Handles environment variables and parameters for audio processing and ML models.
"""

import os
from dotenv import load_dotenv
from rich.console import Console

# Initialize environment and console
load_dotenv()
console = Console()

# API Keys and Model Configuration
# ------------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    console.print("[WARNING] GROQ_API_KEY not found in environment", style="bold yellow")

# Model IDs
# ---------
GROQ_MODEL_NAME = "meta-llama/llama-4-maverick-17b-128e-instruct"
GROQ_WHISPER_MODEL = "whisper-large-v3"

# Audio Processing Parameters
# -------------------------
SAMPLE_RATE = 16000  # Hz
CHUNK_DURATION = 4   # seconds
OVERLAP_DURATION = 2 # seconds

# Derived Audio Parameters
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_DURATION
OVERLAP_SAMPLES = SAMPLE_RATE * OVERLAP_DURATION