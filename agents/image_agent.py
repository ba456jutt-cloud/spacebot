import os
import time
import requests
import urllib.parse
import random

def generate_scene_images(scenes: list, output_dir: str = "assets") -> list:
    """
    Takes a list of scenes and generates an AI image for each scene's prompt.
    Returns the updated list of scenes with the 'image_path' added.
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Image Agent: Generating {len(scenes)} images via Pollinations.ai...")
    
    for i, scene in enumerate(scenes):
        prompt = scene["prompt"]
        scene_id = scene["scene_id"]
        
        # Clean and encode prompt
        encoded_prompt = urllib.parse.quote(prompt)
        # Use dynamic random seed to ensure uniqueness per run
        dynamic_seed = random.randint(100000, 999999)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={dynamic_seed}"
        
        image_path = os.path.join(output_dir, f"scene_{scene_id:03d}.jpg")
        
        success = False
        for attempt in range(3): # Retry up to 3 times
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                    print(f"  [+] Downloaded Scene {scene_id}/{len(scenes)}")
                    scene["image_path"] = image_path
                    success = True
                    break
                elif response.status_code == 429:
                    print(f"  [!] Rate limited on Scene {scene_id}. Retrying in 10s...")
                    time.sleep(10)
                else:
                    print(f"  [-] Failed Scene {scene_id} - HTTP {response.status_code}")
                    break
            except Exception as e:
                print(f"  [-] Exception Scene {scene_id} (Attempt {attempt+1}): {e}")
                time.sleep(5)
                
        if not success:
            scene["image_path"] = None
            
        # Respect rate limits for free API
        time.sleep(3)
        
    return scenes

if __name__ == "__main__":
    # Test
    test_scenes = [
        {"scene_id": 1, "prompt": "Futuristic moon base, glowing lights, 8k"},
        {"scene_id": 2, "prompt": "Astronaut walking on Mars, red dust, cinematic"}
    ]
    updated = generate_scene_images(test_scenes, "assets")
    print(updated)
