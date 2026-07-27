import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

from agents.db_agent import init_db, mark_trend_processed, log_upload
from agents.trend_agent import get_trending_space_topic
from agents.script_agent import generate_script
from agents.image_agent import generate_scene_images
from agents.animation_agent import generate_3d_animations
from agents.music_agent import generate_music
from agents.voice_agent import generate_scene_voiceovers
from agents.video_agent import assemble_video
from agents.shorts_agent import generate_multiple_shorts
from agents.upload_agent import generate_seo_metadata, upload_to_youtube
from agents.thumbnail_agent import generate_custom_thumbnail

def main():
    print("="*60)
    print("🚀 FUGU SPACE AGENT V2.0 - PROFESSIONAL AUTOMATION")
    print("="*60)
    
    # Initialize SQLite Database
    init_db()

    # 1. Topic Discovery (Deduplicated)
    print("\n[PHASE 1] Trend Discovery & Deduplication")
    trend_data = get_trending_space_topic()
    if not trend_data:
        print("[-] Fatal Error: Could not fetch a valid trend.")
        return

    # 2. Script Generation (Using rich SEO context)
    print("\n[PHASE 2] Script & Prompt Engineering")
    scenes = generate_script(trend_data)
    if not scenes:
        return
        
    MAX_TEST_SCENES = None # Set to None for full 10-minute video
    if MAX_TEST_SCENES:
        print(f"[*] Limiting to {MAX_TEST_SCENES} scenes for this test run.")
        scenes = scenes[:MAX_TEST_SCENES]

    # 3. Image Generation (With dynamic seeds)
    print("\n[PHASE 3] Visual Generation (Pollinations AI)")
    scenes = generate_scene_images(scenes)

    # 3.5 3D Animation (DepthFlow)
    print("\n[PHASE 3.5] 3D Animation (DepthFlow)")
    # scenes = generate_3d_animations(scenes)  # Disabled to fix OOM; Zoom is now handled by video_agent via FFmpeg

    # 3.75 Music Generation
    print("\n[PHASE 3.75] AI Music Generation (MusicGen)")
    generate_music()

    # 4. Voiceover Generation
    print("\n[PHASE 4] Audio Generation (Edge-TTS)")
    scenes = generate_scene_voiceovers(scenes)

    # 5. Assemble Video
    print("\n[PHASE 5] Video Assembly & Rendering")
    output_file = f"output/documentary_{int(time.time())}.mp4"
    success = assemble_video(scenes, output_file)
    
    if success:
        # 5.5 SEO & Thumbnail Generation
        print("\n[PHASE 5.5] SEO & Custom Thumbnail Generation")
        seo_data = generate_seo_metadata(trend_data["title"])
        thumbnail_path = generate_custom_thumbnail(seo_data["title"], trend_data["title"])
        if not thumbnail_path:
            thumbnail_path = scenes[0].get("image_path") # Fallback to first scene
            
        # 5.75 YouTube Shorts Generation
        print("\n[PHASE 5.75] Generating Multiple YouTube Shorts (9:16)")
        short_output_file = output_file.replace(".mp4", "_short.mp4")
        generated_shorts = generate_multiple_shorts(scenes, num_shorts=8, base_output_path=short_output_file)

        # 6. YouTube Auto Upload
        print("\n[PHASE 6] YouTube Automated Upload (Long Video)")
        upload_video_id = upload_to_youtube(output_file, thumbnail_path, seo_data)
        
        if upload_video_id and generated_shorts:
            print("\n[*] Uploading and Scheduling YouTube Shorts...")
            
            # Start scheduling 3 hours from now
            schedule_time = datetime.utcnow() + timedelta(hours=3)
            
            for i, short_vid in enumerate(generated_shorts):
                print(f"[*] Processing Short {i+1}/{len(generated_shorts)}")
                
                short_seo = seo_data.copy()
                # Ensure title has #Shorts and fits
                base_title = short_seo["title"].replace("...", "").strip()
                short_title = f"{base_title} (Part {i+1})"
                if len(short_title) > 85:
                    short_title = short_title[:82] + "..."
                short_seo["title"] = short_title + " #Shorts"
                
                # Funnel back to long video
                funnel_text = f"📺 Watch the FULL Video Here: https://youtu.be/{upload_video_id}\n\n"
                short_seo["description"] = funnel_text + short_seo["description"]
                
                # Format time for YouTube API (ISO 8601, Zulu time)
                publish_at_str = schedule_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                
                upload_to_youtube(short_vid, None, short_seo, publish_at=publish_at_str)
                
                # Increment time by 3 hours for the next short
                schedule_time += timedelta(hours=3)

        
        print("\n" + "="*60)
        if upload_video_id:
            print(f"✅ FUGU RUN COMPLETE! Video uploaded successfully (ID: {upload_video_id}).")
            # 7. Log to Database
            print("[*] Logging success to SQLite database...")
            mark_trend_processed(trend_data["video_id"], trend_data["title"])
            log_upload(upload_video_id, trend_data["video_id"], seo_data["title"])
        else:
            print(f"⚠️ FUGU RUN FINISHED, but YouTube Upload failed. Video saved to: {output_file}")
        print("="*60)
    else:
        print("\n[-] FUGU RUN FAILED during video assembly.")

if __name__ == "__main__":
    main()
