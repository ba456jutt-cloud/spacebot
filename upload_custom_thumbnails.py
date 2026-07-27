import os
import sys
import time
from googleapiclient.http import MediaFileUpload
from agents.upload_agent import get_authenticated_service

def upload_my_thumbnails():
    youtube = get_authenticated_service()
    if not youtube:
        print("[-] Could not authenticate with YouTube.")
        return
        
    thumbnails_map = {
        "9-zUH6lA9s4": "/home/ahmad/.gemini/antigravity/brain/8e43c054-ccae-4160-8f0c-6125a7646b43/deep_sea_thumbnail_1784455063812.png",
        "AiDA7D_5MuU": "/home/ahmad/.gemini/antigravity/brain/8e43c054-ccae-4160-8f0c-6125a7646b43/space_knocking_thumbnail_1784455074465.png",
        "LdvHVwZzVNo": "/home/ahmad/.gemini/antigravity/brain/8e43c054-ccae-4160-8f0c-6125a7646b43/pluto_discovery_thumbnail_1784455084231.png",
        "wRcrLn8QCBE": "/home/ahmad/.gemini/antigravity/brain/8e43c054-ccae-4160-8f0c-6125a7646b43/milky_way_thumbnail_1784455095108.png"
    }
    
    print("[*] Starting custom thumbnail upload...\n")
    for vid, path in thumbnails_map.items():
        print(f"--- Updating Video ID: {vid} ---")
        if not os.path.exists(path):
            print(f"[-] Image not found: {path}")
            continue
            
        try:
            print("[*] Uploading to YouTube API...")
            youtube.thumbnails().set(
                videoId=vid,
                media_body=MediaFileUpload(path)
            ).execute()
            print("[+] Thumbnail updated successfully on YouTube!\n")
        except Exception as e:
            print(f"[-] Failed to upload thumbnail for {vid}: {e}\n")
            
        time.sleep(2)
        
    print("[+] ALL CUSTOM THUMBNAILS UPLOADED!")

if __name__ == "__main__":
    upload_my_thumbnails()
