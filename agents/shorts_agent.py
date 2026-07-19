
import os
from agents.video_agent import assemble_video, get_audio_duration

def generate_youtube_short(scenes: list, output_path: str = "output/short_video.mp4") -> bool:
    print("[*] Shorts Agent: Preparing a 60-second YouTube Short...")
    
    total_dur = 0
    short_scenes = []
    
    for s in scenes:
        audio_path = s.get("audio_path")
        if not audio_path or not os.path.exists(audio_path):
            continue
            
        dur = get_audio_duration(audio_path) + 0.1
        if total_dur + dur > 59.0: # Keep under 60s
            break
            
        short_scenes.append(s)
        total_dur += dur
        
    if not short_scenes:
        print("[-] Shorts Agent: No valid scenes found.")
        return False
        
    print(f"[*] Compiling {len(short_scenes)} scenes for {total_dur:.2f} seconds...")
    return assemble_video(short_scenes, output_path, is_short=True)
