import os
import asyncio
import edge_tts
import json

async def _generate_voiceover_async(scenes: list, output_audio: str, output_srt: str) -> bool:
    # Combine all voiceover texts into a single string for seamless reading
    # Alternatively, we could generate audio per scene and concatenate, but single file is smoother.
    # To keep exact sync, we can generate audio per scene.
    # Given the requirements, generating per scene allows perfect image-to-audio synchronization.
    
    # Wait, MoviePy can handle lists of audio clips!
    # Let's generate one audio file per scene.
    pass

async def _download_voice(scene, output_dir, semaphore):
    async with semaphore:
        voice_text = scene["voice"]
        scene_id = scene["scene_id"]
        voice = "en-US-ChristopherNeural"
        audio_path = os.path.join(output_dir, f"scene_{scene_id:03d}.mp3")

        try:
            communicate = edge_tts.Communicate(voice_text, voice, rate='-10%')
            await communicate.save(audio_path)
            print(f"  [+] Voice Scene {scene_id} generated.")
            scene["audio_path"] = audio_path
        except Exception as e:
            print(f"  [-] Failed Voice Scene {scene_id}: {e}")
            scene["audio_path"] = None

        await asyncio.sleep(0.1) # minimal delay to prevent overwhelming edge-tts
        return scene

def generate_scene_voiceovers(scenes: list, output_dir: str = "output") -> list:
    """
    Generates a TTS audio file for each scene using edge-tts concurrently.
    Returns the scenes list with 'audio_path' added.
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Voice Agent: Generating audio for {len(scenes)} scenes (Async)...")

    async def run_all():
        semaphore = asyncio.Semaphore(10) # process up to 10 voices concurrently
        tasks = [_download_voice(scene, output_dir, semaphore) for scene in scenes]
        return await asyncio.gather(*tasks)

    updated_scenes = asyncio.run(run_all())
    # Sort just in case gather returns them out of order (though gather usually preserves order)
    updated_scenes.sort(key=lambda x: x["scene_id"])
    return updated_scenes

if __name__ == "__main__":
    test_scenes = [
        {"scene_id": 1, "voice": "Space is cold and dark."},
        {"scene_id": 2, "voice": "But full of wonders."}
    ]
    updated = generate_scene_voiceovers(test_scenes, "output")
    print(updated)
