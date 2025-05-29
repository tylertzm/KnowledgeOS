from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
from config import console, GROQ_API_KEY
from llm_handler import LLMHandler
from websearch_handler import WebSearchHandler

app = Flask(__name__)
CORS(app)

# Global state
ai_mode_active = True
websearch_mode_active = False
latest_transcription = ""
latest_response = ""

# Initialize handlers
llm_handler = LLMHandler()
websearch_handler = WebSearchHandler()

@app.route("/")
def index():
    return jsonify({"status": "ok"})

@app.route("/status")
def status():
    mode = "WebSearch" if websearch_mode_active else "AI" if ai_mode_active else "Transcription"
    return jsonify({
        "mode": mode,
        "transcription": latest_transcription,
        "response": latest_response
    })

@app.route("/process", methods=["POST"])
def process():
    global ai_mode_active, websearch_mode_active, latest_transcription, latest_response
    
    data = request.json
    text = data.get("text", "")
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
        
    latest_transcription = text
    
    if "ai mode" in text.lower():
        ai_mode_active = True
        websearch_mode_active = False
        latest_response = "AI mode activated"
    elif "web search mode" in text.lower():
        ai_mode_active = False
        websearch_mode_active = True
        latest_response = "Web search mode activated"
    elif websearch_mode_active and text.strip().endswith("?"):
        response = websearch_handler.search(text)
        if response:
            latest_response = response
    elif ai_mode_active:
        response = llm_handler.get_response(text)
        if response:
            latest_response = response
            
    return jsonify({
        "mode": "WebSearch" if websearch_mode_active else "AI",
        "transcription": latest_transcription,
        "response": latest_response
    })

if __name__ == "__main__":
    if not GROQ_API_KEY:
        console.print("[FATAL ERROR] GROQ_API_KEY environment variable not set.", style="bold red")
        exit(1)
        
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)