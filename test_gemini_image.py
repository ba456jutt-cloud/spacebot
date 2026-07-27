import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={api_key}"

payload = {
    "instances": [
        {
            "prompt": "A beautiful cinematic deep space nebula"
        }
    ],
    "parameters": {
        "sampleCount": 1
    }
}

try:
    resp = requests.post(url, json=payload)
    print(resp.status_code)
    print(resp.text[:500])
except Exception as e:
    print(e)
