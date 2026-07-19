
import os
import subprocess
import glob

def get_audio_duration(audio_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except:
        return 5.0

def float_to_ass_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{millis:02d}"

def generate_scene_ass(scene_id: str, text: str, duration: float) -> str:
    ass_path = f"assets/scene_{scene_id}.ass"
    start_time = float_to_ass_time(0)
    end_time = float_to_ass_time(duration)
    
    ass_content = f'''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Anton,80,&H0000FFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,4,0,2,10,10,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}
'''
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
    return ass_path

def assemble_video(scenes: list, output_path: str = "output/final_video.mp4") -> bool:
    print(f"[*] Video Agent: Assembling {len(scenes)} scenes using FFmpeg...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs("assets/temp_scenes", exist_ok=True)
    
    mp4_files = []
    
    for idx, scene in enumerate(scenes):
        scene_id = scene.get("scene_id", f"{idx:03d}")
        img_path = scene.get("image_path")
        audio_path = scene.get("audio_path")
        text = scene.get("voice", "")
        
        if not img_path or not audio_path or not os.path.exists(img_path) or not os.path.exists(audio_path):
            print(f"  [-] Skipping Scene {scene_id} - Missing files.")
            continue
            
        print(f"  [+] Processing Scene {scene_id} ({idx+1}/{len(scenes)})...")
        
        out_mp4 = f"assets/temp_scenes/scene_{scene_id}.mp4"
        duration = get_audio_duration(audio_path) + 0.1
        frames = int(duration * 24)
        
        ass_path = generate_scene_ass(scene_id, text, duration)
        
        zoom_expr = "min(zoom+0.0005,1.05)"
        zoompan = f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080"
        subtitles = f"subtitles={ass_path}:fontsdir=assets"
        
        vf_chain = f"{zoompan},{subtitles}"
        af_chain = "apad=pad_dur=0.1"
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img_path,
            "-i", audio_path,
            "-vf", vf_chain,
            "-af", af_chain,
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration),
            out_mp4
        ]
        
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0 and os.path.exists(out_mp4):
            mp4_files.append(out_mp4)
        else:
            print(f"  [-] FFmpeg failed on Scene {scene_id}")

    if not mp4_files:
        print("[-] Video Agent: No valid scenes generated!")
        return False
        
    print("[*] Concatenating scenes...")
    concat_file = "assets/temp_scenes/concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for mp4 in mp4_files:
            f.write(f"file '{os.path.abspath(mp4)}'
")
            
    temp_concat = "assets/temp_scenes/temp_concat.mp4"
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        temp_concat
    ]
    subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if not os.path.exists(temp_concat):
        print("[-] Concatenation failed.")
        return False
        
    bgm_path = "assets/bgm.wav"
    if os.path.exists(bgm_path):
        print("[*] Adding Background Music...")
        cmd_bgm = [
            "ffmpeg", "-y",
            "-i", temp_concat,
            "-stream_loop", "-1", "-i", bgm_path,
            "-filter_complex", "[0:a]volume=1.0[a1];[1:a]volume=0.1[a2];[a1][a2]amix=inputs=2:duration=first[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ]
        subprocess.run(cmd_bgm, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        shutil.copy(temp_concat, output_path)

    # Cleanup temp
    for f in glob.glob("assets/temp_scenes/*"):
        os.remove(f)
    for f in glob.glob("assets/scene_*.ass"):
        os.remove(f)
        
    if os.path.exists(output_path):
        print(f"[+] Video Agent: Final documentary saved to {output_path}")
        return True
    return False

if __name__ == '__main__':
    pass
