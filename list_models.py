import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
resp = requests.get(url).json()

for model in resp.get("models", []):
    name = model.get("name", "")
    print(name)
