import requests
from config import console

class WebSearchHandler:
    def __init__(self):
        self.base_url = "https://text.pollinations.ai"
        
    def search(self, query):
        try:
            # Make GET request instead of POST for simpler queries
            response = requests.get(
                f"{self.base_url}/{query}",
                params={"model": "searchgpt"},
                headers={'Accept': 'text/plain'}
            )
            response.raise_for_status()
            
            # Debug logging
            console.print(f"[DEBUG] Raw response: {response.text[:100]}", style="yellow")
            
            try:
                # Try parsing as JSON first
                data = response.json()
                return data.get('content', str(data))
            except requests.exceptions.JSONDecodeError:
                # If not JSON, return the raw text
                return response.text.strip()
                
        except Exception as e:
            console.print(f"[ERROR] Web search failed: {e}", style="bold red")
            console.print(f"[DEBUG] Response content: {response.text[:200]}", style="yellow")
            return "Sorry, the web search failed. Please try again."
