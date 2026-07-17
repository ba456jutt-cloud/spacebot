import os
import subprocess
import time
from googleapiclient.http import MediaFileUpload
from agents.thumbnail_agent import generate_custom_thumbnail
from agents.upload_agent import get_authenticated_service

CHANNEL_URL = "https://www.youtube.com/@GalacticDiscoveries-u8v/videos"

def get_channel_videos():
    """Uses yt-dlp to get all video IDs and titles from the channel."""
    print(f"[*] Batch Updater: Fetching videos from {CHANNEL_URL}...")
    try:
        # Run yt-dlp
        result = subprocess.run(
            ["./venv/bin/yt-dlp", "--print", "%(id)s|%(title)s", CHANNEL_URL],
            capture_output=True, text=True, check=True
        )
        videos = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line and not line.startswith("WARNING"):
                parts = line.split("|", 1)
                videos.append({"id": parts[0].strip(), "title": parts[1].strip()})
        return videos
    except subprocess.CalledProcessError as e:
        print(f"[-] yt-dlp failed: {e.stderr}")
        return []

def main():
    print("============================================================")
    print("🚀 FUGU BATCH THUMBNAIL UPDATER (MRBEAST STYLE)")
    print("============================================================")
    
    youtube = get_authenticated_service()
    if not youtube:
        print("[-] Could not authenticate with YouTube.")
        return
        
    videos = get_channel_videos()
    if not videos:
        print("[-] No videos found or failed to fetch.")
        return
        
    print(f"[+] Found {len(videos)} videos to update!\n")
    
    for i, video in enumerate(videos):
        vid = video["id"]
        title = video["title"]
        print(f"--- Updating Video {i+1}/{len(videos)} ---")
        print(f"ID: {vid} | Title: {title}")
        
        # 1. Generate Thumbnail
        thumb_path = f"assets/thumb_{vid}.jpg"
        generated_path = generate_custom_thumbnail(title, "Space Documentary", thumb_path)
        
        if not generated_path or not os.path.exists(generated_path):
            print(f"[-] Failed to generate thumbnail for {vid}. Skipping.")
            continue
            
        # 2. Upload Thumbnail
        try:
            print("[*] Uploading to YouTube API...")
            youtube.thumbnails().set(
                videoId=vid,
                media_body=MediaFileUpload(generated_path)
            ).execute()
            print("[+] Thumbnail updated successfully on YouTube!\n")
        except Exception as e:
            print(f"[-] Failed to upload thumbnail for {vid}: {e}\n")
            
        # Sleep to avoid rate limits
        time.sleep(5)
        
    print("[+] BATCH UPDATE COMPLETE!")

if __name__ == "__main__":
    main()
