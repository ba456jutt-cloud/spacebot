import os
import json
import re
import requests
from dotenv import load_dotenv

load_dotenv()

TARGET_SCENES = 120  # Exactly 120 scenes for a 10-minute video

CHUNK_SIZE = min(TARGET_SCENES, 30)

def generate_script(trend_data: dict) -> list:
    """
    Calls the Gemini API to write a documentary script in chunks.
    Returns a list of dicts: [{'scene_id': 1, 'prompt': '...', 'voice': '...'}, ...]
    """
    print(f"[*] Script Agent: Generating {TARGET_SCENES}-scene script for '{trend_data['title']}' in chunks of {CHUNK_SIZE}...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("[-] GEMINI_API_KEY not set. Using fallback script.")
        return _get_fallback_script()
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    tags_str = ", ".join(trend_data.get("tags", []))
    
    prompt_text = f"""You are an expert documentary scriptwriter and AI image prompt engineer.
Create a cinematic documentary script about the following topic.

Topic: "{trend_data['title']}"
Description: "{trend_data['description']}"
Keywords: {tags_str}

STRICT REQUIREMENTS:
1. You MUST output EXACTLY {CHUNK_SIZE} scenes for this part.
2. Each scene represents 5 seconds of video.
3. The VOICE text for each scene MUST be between 10 and 20 words ONLY. Short sentences. Punchy. Dramatic.
4. The PROMPT must be a vivid, hyper-detailed image generation prompt mentioning: cinematic, 8k, photorealistic, dramatic lighting.
5. Do NOT add any introduction, conclusion, or extra commentary. Output ONLY the scenes below.

OUTPUT FORMAT (repeat exactly {CHUNK_SIZE} times):
[SCENE 1]
PROMPT: <detailed image generation prompt here>
VOICE: <10 to 20 words of dramatic narration here>

[SCENE 2]
PROMPT: <detailed image generation prompt here>
VOICE: <10 to 20 words of dramatic narration here>

... continue for all {CHUNK_SIZE} scenes ...
[SCENE {CHUNK_SIZE}]
PROMPT: <detailed image generation prompt here>
VOICE: <10 to 20 words of dramatic narration here>
"""

    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 65536
        }
    }
    
    try:
        print(f"[*] Calling Gemini API (Chunk 1: {CHUNK_SIZE} scenes)...")
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=120)
        response.raise_for_status()
        result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        scenes = parse_script_output(result_text)
        
        # Loop until we reach TARGET_SCENES
        while len(scenes) < TARGET_SCENES:
            print(f"[!] Got {len(scenes)} scenes, need {TARGET_SCENES}. Requesting next chunk...")
            scenes = _extend_scenes(scenes, trend_data, api_key, url)
        
        # Truncate if Gemini hallucinated more scenes than asked
        return scenes[:TARGET_SCENES]
    except Exception as e:
        print(f"[-] Script Agent Error: {e}")
        return _get_fallback_script()

def _extend_scenes(existing_scenes: list, trend_data: dict, api_key: str, url: str) -> list:
    """Request additional scenes to reach TARGET_SCENES count."""
    current_count = len(existing_scenes)
    needed = min(TARGET_SCENES - current_count, 30) # Ask for max 30 at a time
    start_id = current_count + 1
    end_id = current_count + needed
    
    extend_prompt = f"""Continue the documentary about "{trend_data['title']}".
Write {needed} MORE scenes continuing from scene {start_id}.
Each scene: PROMPT (image prompt) and VOICE (10-20 words max).
Use EXACTLY this format:

[SCENE {start_id}]
PROMPT: ...
VOICE: ...

Continue until [SCENE {end_id}]"""

    payload = {
        "contents": [{"parts": [{"text": extend_prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 65536}
    }
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=120)
        response.raise_for_status()
        extra_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        extra_scenes = parse_script_output(extra_text)
        
        # Re-number scenes sequentially
        for i, s in enumerate(extra_scenes):
            s["scene_id"] = current_count + i + 1
            
        combined = existing_scenes + extra_scenes
        print(f"[+] Extended to {len(combined)} scenes total.")
        return combined
    except Exception as e:
        print(f"[-] Extension failed: {e}. Returning {current_count} scenes. Will retry.")
        return existing_scenes

def parse_script_output(text: str) -> list:
    scenes = []
    pattern = r"\[SCENE \d+\].*?PROMPT:\s*(.*?)\n\s*VOICE:\s*(.*?)(?=\n\s*\[SCENE|\Z)"
    matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
    
    for i, match in enumerate(matches):
        prompt = match.group(1).strip()
        voice = match.group(2).strip()
        # Trim overly long voice text to keep scenes short
        words = voice.split()
        if len(words) > 25:
            voice = " ".join(words[:22]) + "..."
        scenes.append({
            "scene_id": i + 1,
            "prompt": prompt,
            "voice": voice
        })
        
    print(f"[+] Script Agent: Parsed {len(scenes)} scenes.")
    return scenes

def _get_fallback_script():
    """Generates a minimal fallback script for testing."""
    topics = [
        ("A glowing black hole with a swirling accretion disk, cinematic 8k", "The universe hides monsters too massive for human minds to comprehend."),
        ("Deep space nebula in purple and blue, photorealistic, 8k", "Vast clouds of gas and dust drift silently between dying stars."),
        ("A neutron star emitting powerful jets of plasma, cinematic", "Some stellar deaths leave behind cores so dense they warp spacetime."),
        ("Earth seen from deep space, tiny and fragile, cinematic 8k", "From far enough away, our entire world is just a pale blue dot."),
        ("Dark matter visualization, glowing web of cosmic structure", "Most of the universe is invisible. We have never seen dark matter directly."),
    ]
    # Repeat topics to fill 120 scenes
    scenes = []
    for i in range(TARGET_SCENES):
        t = topics[i % len(topics)]
        scenes.append({"scene_id": i + 1, "prompt": t[0], "voice": t[1]})
    return scenes

if __name__ == "__main__":
    pass
