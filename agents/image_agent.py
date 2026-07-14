import os
import time
import requests
import urllib.parse
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

def _download_image(scene, output_dir):
    # Add a random delay (jitter) so all threads don't hit the server at the exact same millisecond
    time.sleep(random.uniform(1.0, 4.0))
    
    prompt = scene["prompt"]
    scene_id = scene["scene_id"]

    encoded_prompt = urllib.parse.quote(prompt)
    dynamic_seed = random.randint(100000, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed={dynamic_seed}"

    image_path = os.path.join(output_dir, f"scene_{scene_id:03d}.jpg")

    success = False
    for attempt in range(10): # Increased to 10 attempts to NEVER skip a scene
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(response.content)
                print(f"  [+] Downloaded Scene {scene_id}")
                scene["image_path"] = image_path
                success = True
                break
            elif response.status_code == 429:
                sleep_time = 15 * (attempt + 1)
                print(f"  [!] Rate limited on Scene {scene_id}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)  # Exponential backoff
            else:
                print(f"  [-] Failed Scene {scene_id} - HTTP {response.status_code}")
                time.sleep(10)
        except Exception as e:
            print(f"  [-] Exception Scene {scene_id} (Attempt {attempt+1}): {e}")
            time.sleep(10)

    if not success:
        scene["image_path"] = None

    time.sleep(2) # Small delay to not overwhelm the API too much
    return scene

def generate_scene_images(scenes: list, output_dir: str = "assets") -> list:
    """
    Takes a list of scenes and generates an AI image for each scene's prompt concurrently.
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Image Agent: Generating {len(scenes)} images via Pollinations.ai (Multithreaded)...")

    updated_scenes = []
    # Use max_workers=3 instead of 10 to avoid getting banned/rate limited by the free API
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(_download_image, scene, output_dir): scene for scene in scenes}
        for future in as_completed(futures):
            updated_scenes.append(future.result())

    # Sort the scenes back by scene_id because concurrent execution scrambles the order
    updated_scenes.sort(key=lambda x: x["scene_id"])
    return updated_scenes

if __name__ == "__main__":
    # Test
    test_scenes = [
        {"scene_id": 1, "prompt": "Futuristic moon base, glowing lights, 8k"},
        {"scene_id": 2, "prompt": "Astronaut walking on Mars, red dust, cinematic"}
    ]
    updated = generate_scene_images(test_scenes, "assets")
    print(updated)
