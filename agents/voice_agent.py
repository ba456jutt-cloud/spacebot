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

def generate_scene_voiceovers(scenes: list, output_dir: str = "output") -> list:
    """
    Generates a TTS audio file for each scene using edge-tts.
    Returns the scenes list with 'audio_path' added.
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Voice Agent: Generating audio for {len(scenes)} scenes...")
    
    async def run_all():
        for i, scene in enumerate(scenes):
            voice_text = scene["voice"]
            scene_id = scene["scene_id"]
            
            # Using a very natural, deep documentary voice if available, otherwise default
            voice = "en-US-ChristopherNeural" 
            
            audio_path = os.path.join(output_dir, f"scene_{scene_id:03d}.mp3")
            
            try:
                communicate = edge_tts.Communicate(voice_text, voice)
                await communicate.save(audio_path)
                print(f"  [+] Voice Scene {scene_id}/{len(scenes)} generated.")
                scene["audio_path"] = audio_path
            except Exception as e:
                print(f"  [-] Failed Voice Scene {scene_id}: {e}")
                scene["audio_path"] = None
                
            # slight delay to prevent edge-tts connection reset
            await asyncio.sleep(0.5)
            
    asyncio.run(run_all())
    return scenes

if __name__ == "__main__":
    test_scenes = [
        {"scene_id": 1, "voice": "Space is cold and dark."},
        {"scene_id": 2, "voice": "But full of wonders."}
    ]
    updated = generate_scene_voiceovers(test_scenes, "output")
    print(updated)
