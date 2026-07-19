
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

def generate_scene_ass(scene_id: str, text: str, duration: float, is_short: bool = False) -> str:
    ass_path = f"assets/scene_{scene_id}.ass"
    start_time = float_to_ass_time(0)
    end_time = float_to_ass_time(duration)
    
    res_x = 1080 if is_short else 1920
    res_y = 1920 if is_short else 1080
    font_size = 110 if is_short else 80
    margin_v = 300 if is_short else 60
    
    ass_content = f'''[Script Info]
ScriptType: v4.00+
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Anton,{font_size},&H0000FFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,4,0,2,10,10,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}
'''
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
    return ass_path

def assemble_video(scenes: list, output_path: str = "output/final_video.mp4", is_short: bool = False) -> bool:
    print(f"[*] Video Agent: Assembling {len(scenes)} scenes (is_short={is_short})...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    temp_dir = "assets/temp_short" if is_short else "assets/temp_scenes"
    os.makedirs(temp_dir, exist_ok=True)
    
    mp4_files = []
    
    for idx, scene in enumerate(scenes):
        scene_id = scene.get("scene_id", f"{idx:03d}")
        img_path = scene.get("image_path")
        audio_path = scene.get("audio_path")
        text = scene.get("voice", "")
        
        if not img_path or not audio_path or not os.path.exists(img_path) or not os.path.exists(audio_path):
            continue
            
        print(f"  [+] Processing Scene {scene_id}...")
        
        out_mp4 = f"{temp_dir}/scene_{scene_id}.mp4"
        duration = get_audio_duration(audio_path) + 0.1
        frames = int(duration * 24)
        
        ass_path = generate_scene_ass(scene_id, text, duration, is_short)
        
        zoom_expr = "min(zoom+0.0005,1.05)"
        if is_short:
            # Crop to 9:16 first, then zoom
            zoompan = f"crop=ih*(9/16):ih,zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920"
        else:
            zoompan = f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080"
            
        subtitles = f"subtitles={ass_path}:fontsdir=assets"
        
        sfx_path = "assets/sfx.wav"
        has_sfx = os.path.exists(sfx_path)
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img_path,
            "-i", audio_path
        ]
        
        if has_sfx:
            cmd.extend(["-i", sfx_path])
            cmd.extend([
                "-filter_complex",
                f"[0:v]{zoompan},{subtitles}[vout];[1:a]apad=pad_dur=0.1[a_voice];[a_voice][2:a]amix=inputs=2:duration=first[aout]",
                "-map", "[vout]",
                "-map", "[aout]"
            ])
        else:
            cmd.extend([
                "-vf", f"{zoompan},{subtitles}",
                "-af", "apad=pad_dur=0.1"
            ])
            
        cmd.extend([
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration),
            out_mp4
        ])
        
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0 and os.path.exists(out_mp4):
            mp4_files.append(out_mp4)

    if not mp4_files:
        return False
        
    concat_file = f"{temp_dir}/concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for mp4 in mp4_files:
            f.write(f"file '{os.path.abspath(mp4)}'\n")
            
    temp_concat = f"{temp_dir}/temp_concat.mp4"
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        temp_concat
    ]
    subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    bgm_path = "assets/bgm.wav"
    if os.path.exists(bgm_path):
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
    for f in glob.glob(f"{temp_dir}/*"):
        os.remove(f)
    for f in glob.glob("assets/scene_*.ass"):
        os.remove(f)
        
    return os.path.exists(output_path)

if __name__ == '__main__':
    pass
