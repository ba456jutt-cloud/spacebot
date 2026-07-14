import os
from moviepy.editor import (
    ImageClip, AudioFileClip, concatenate_videoclips,
    CompositeVideoClip, CompositeAudioClip, TextClip,
    VideoFileClip
)
import textwrap

def assemble_video(scenes: list, output_path: str = "output/final_video.mp4") -> bool:
    """
    Takes a list of scenes with image and audio paths.
    Stitches them together using MoviePy 1.0.3.
    """
    print(f"[*] Video Agent: Assembling {len(scenes)} scenes into final documentary...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    video_clips = []
    
    for scene in scenes:
        img_path = scene.get("image_path")
        aud_path = scene.get("audio_path")
        
        if not img_path or not aud_path or not os.path.exists(img_path) or not os.path.exists(aud_path):
            print(f"  [-] Skipping Scene {scene.get('scene_id')} - Missing files.")
            continue
            
        try:
            # 1. Load Audio to get duration
            audio_clip = AudioFileClip(aud_path)
            duration = audio_clip.duration + 0.5  # Tiny pause between scenes
            
            # 2. Load Image or Animation
            anim_path = scene.get("animated_path")
            if anim_path and anim_path.endswith(".mp4") and os.path.exists(anim_path):
                video_clip = VideoFileClip(anim_path)
                # Loop or trim to match audio duration
                if video_clip.duration < duration:
                    from moviepy.video.fx.loop import loop
                    video_clip = loop(video_clip, duration=duration)
                else:
                    video_clip = video_clip.subclip(0, duration)
            else:
                # Fallback to static image and add a slow zoom-in effect (Ken Burns)
                def zoom(t):
                    return 1 + 0.04 * (t / max(duration, 0.01))
                video_clip = ImageClip(img_path).set_duration(duration).resize(zoom)
            
            # 3. Add Animated Subtitles
            text = scene.get("voice", "")
            if text:
                try:
                    # method='caption' and size=(1600, None) automatically wraps text.
                    # We use stroke_color and stroke_width for cinematic text instead of an ugly black box.
                    txt_clip = TextClip(
                        text, 
                        fontsize=60, 
                        color='white',
                        stroke_color='black',
                        stroke_width=2.5,
                        method='caption', 
                        size=(1600, None)
                    )
                    # Floating animation: moves slightly upward in 1080p landscape
                    def make_float(dur):
                        def float_up(t):
                            y = int(850 - 40 * (t / max(dur, 0.01)))
                            return ('center', y)
                        return float_up
                    txt_clip = txt_clip.set_position(make_float(duration)).set_duration(duration)
                    comp = CompositeVideoClip([video_clip.set_position('center')], size=(1920, 1080))
                    comp = CompositeVideoClip([comp, txt_clip], size=(1920, 1080))
                except Exception as txt_err:
                    print(f"  [-] TextClip skipped: {txt_err}")
                    comp = CompositeVideoClip([video_clip.set_position('center')], size=(1920, 1080))
            else:
                comp = CompositeVideoClip([video_clip.set_position('center')], size=(1920, 1080))
                
            comp = comp.set_duration(duration).set_audio(audio_clip)
            video_clips.append(comp)
            
        except Exception as e:
            print(f"  [-] Error processing scene {scene.get('scene_id')}: {e}")
            
    if not video_clips:
        print("[-] Video Agent: No valid clips to assemble!")
        return False
        
    print(f"[*] Video Agent: Rendering {len(video_clips)} clips (This will take a while)...")
    
    try:
        final_video = concatenate_videoclips(video_clips, method="compose")
        
        # 4. Add Background Music (BGM)
        bgm_path = "assets/bgm.wav"
        if os.path.exists(bgm_path):
            try:
                from moviepy.audio.fx.audio_loop import audio_loop
                from moviepy.audio.fx.volumex import volumex
                bgm = AudioFileClip(bgm_path)
                bgm = audio_loop(bgm, duration=final_video.duration)
                bgm = volumex(bgm, 0.1)
                if final_video.audio:
                    mixed_audio = CompositeAudioClip([final_video.audio, bgm])
                else:
                    mixed_audio = bgm
                final_video = final_video.set_audio(mixed_audio)
                print("[+] Background music added at 10% volume.")
            except Exception as bgm_err:
                print(f"[-] BGM skipped: {bgm_err}")
        
        # Write to file
        final_video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger=None
        )
        print(f"[+] Video Agent: Final documentary saved to {output_path}")
        return True
    except Exception as e:
        print(f"[-] Video Agent: Rendering failed: {e}")
        return False

if __name__ == "__main__":
    pass
