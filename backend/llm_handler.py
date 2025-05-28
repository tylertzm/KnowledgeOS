from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL_NAME, console

class LLMHandler:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.message_history = []

    def get_response(self, prompt):
        self.message_history.append({"role": "user", "content": prompt})
        trimmed = [m for m in self.message_history if m["role"] == "user"][-2:]
        assistant = [m for m in self.message_history if m["role"] == "assistant"]
        if assistant:
            trimmed.insert(1, assistant[-1])
        
        try:
            completion = self.client.chat.completions.create(
                model=GROQ_MODEL_NAME,
                messages=trimmed,
                max_tokens=100
            )
            reply = completion.choices[0].message.content.strip()
            self.message_history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            console.print(f"[ERROR] Groq API request failed: {e}", style="bold red")
            return None