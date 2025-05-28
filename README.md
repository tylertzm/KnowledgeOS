# KnowledgeOS - Real-time Voice Assistant with Whisper and Groq LLM

A real-time voice assistant that transcribes speech using Whisper and processes it through Groq's LLM API, with both command-line and web interfaces.

## Features

- 🎙️ Real-time audio transcription using Whisper
- 🤖 AI chat capabilities using Groq's LLM API
- 🔄 Two modes: Transcription-only and AI Chat
- 💻 Web interface for interaction
- 🚀 Flask backend with REST API
- ⚡ Electron-based frontend

## Project Structure

```
KnowledgeOS/
├── backend/
│   ├── app.py              # Flask application
│   ├── audiohandler.py     # Audio recording and processing
│   ├── config.py           # Configuration and environment setup
│   ├── llm_handler.py      # Groq LLM integration
│   ├── transcriptions.py   # Whisper transcription
│   └── requirements.txt    # Python dependencies
└── frontend/
    ├── index.html         # Web interface
    ├── renderer.js        # Frontend logic
    └── package.json       # Node.js dependencies
```

## Setup

1. run the start script in your terminal
```bash
start.sh 
```

(but if this does not work)

or 

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file in the backend directory:
```
GROQ_API_KEY=your_api_key_here
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

## Usage

1. Start the backend server:
```bash
cd backend
python app.py
```

2. Start the frontend:
```bash
cd frontend
npm start
```

## Modes

- **Transcription Mode**: Only transcribes speech to text
- **AI Mode**: Transcribes speech and sends it to Groq LLM for responses
  - Say "ai mode" to enable AI responses
  - Say "transcription mode" to disable AI responses

## API Endpoints

- `GET /status`: Get current mode and latest transcription/response
- `GET /`: Web interface

## Notes

- Uses Whisper large-v3-turbo for transcription
- Uses Groq's llama-4-maverick-17b-128e-instruct model for AI responses
- Audio is processed in 4-second chunks with 2-second overlap
- Web interface updates in real-time with transcriptions and AI responses

## Troubleshooting

- Ensure your microphone is properly configured
- Check GROQ_API_KEY is properly set in .env
- For audio issues, verify sounddevice is working with your system
- If transcription is slow, consider using a GPU or reducing the chunk size 