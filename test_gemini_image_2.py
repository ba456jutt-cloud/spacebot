import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def test_model(model_name):
    print(f"Testing {model_name}...")
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "A cinematic shot of space"}]}]
    }
    try:
        resp = requests.post(url, json=payload)
        print(resp.status_code)
        if resp.status_code != 200:
            print(resp.text[:500])
        else:
            print("Success!")
    except Exception as e:
        print(e)

test_model("models/gemini-3.1-flash-image")
test_model("models/gemini-3.1-flash-lite-image")
test_model("models/gemini-3-pro-image")
