import os
import json
import time
from dotenv import load_dotenv
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Import thumbnail agent
from agents.thumbnail_agent import generate_custom_thumbnail

load_dotenv()

# We need the full youtube scope to edit video details
SCOPES = ["https://www.googleapis.com/auth/youtube"]
CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_FILE = "token_edit.json"

def get_authenticated_service():
    """Authenticates the user with full YouTube API access and returns the service object."""
    credentials = None
    
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            credentials = Credentials.from_authorized_user_info(json.load(f), SCOPES)
            
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"[-] Fatal Error: '{CLIENT_SECRETS_FILE}' not found. Cannot authenticate.")
                return None
            print("\\n[*] Update Script: Initiating Google OAuth Login Flow...")
            print("[!] PLEASE CHECK YOUR BROWSER AND LOG IN TO YOUTUBE.")
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)
            
        with open(TOKEN_FILE, "w") as f:
            f.write(credentials.to_json())
            
    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

def main():
    print("="*60)
    print("🚀 BATCH UPDATER: SPACE BOT VIDEOS")
    print("="*60)
    
    youtube = get_authenticated_service()
    if not youtube:
        return
        
    print("[*] Fetching all uploaded videos...")
    try:
        channel_response = youtube.channels().list(mine=True, part='contentDetails').execute()
        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except Exception as e:
        print(f"[-] Failed to get channel uploads playlist: {e}")
        return
        
    videos = []
    request = youtube.playlistItems().list(playlistId=uploads_playlist_id, part='snippet', maxResults=50)
    
    while request:
        response = request.execute()
        for item in response['items']:
            videos.append({
                'id': item['snippet']['resourceId']['videoId'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description']
            })
        request = youtube.playlistItems().list_next(request, response)
        
    if not videos:
        print("[-] No videos found on this channel.")
        return
        
    print(f"[+] Found {len(videos)} videos. Processing updates...")
    
    # Process each video
    for i, video in enumerate(videos):
        print(f"\\n--------------------------------------------------")
        print(f"[*] Processing ({i+1}/{len(videos)}): {video['title']}")
        
        # 1. Fetch full snippet details to update properly
        try:
            vid_response = youtube.videos().list(part="snippet", id=video['id']).execute()
            if not vid_response.get("items"):
                print("  [-] Could not fetch full snippet for video. Skipping.")
                continue
            snippet = vid_response["items"][0]["snippet"]
        except Exception as e:
            print(f"  [-] Error fetching snippet: {e}")
            continue

        # 2. Add Watch Next Links to Description
        desc = snippet.get("description", "")
        if "📺 VER A CONTINUACIÓN:" not in desc:
            print("  [*] Updating description with Watch Next links...")
            
            # Get up to 3 OTHER recent videos
            other_vids = [v for v in videos if v['id'] != video['id']][:3]
            
            if other_vids:
                watch_next_text = "\\n\\n📺 VER A CONTINUACIÓN:\\n"
                for v in other_vids:
                    watch_next_text += f"🔗 {v['title']} - https://youtu.be/{v['id']}\\n"
                
                # Update snippet
                snippet["description"] = watch_next_text + "\\n" + desc
                
                try:
                    youtube.videos().update(
                        part="snippet",
                        body={
                            "id": video['id'],
                            "snippet": snippet
                        }
                    ).execute()
                    print("  [+] Description updated successfully!")
                except Exception as e:
                    print(f"  [-] Failed to update description: {e}")
        else:
            print("  [*] Description already contains Watch Next links. Skipping description update.")
            
        # 3. Generate and Set New Thumbnail
        print("  [*] Generating new 2D Cartoon thumbnail...")
        thumbnail_path = generate_custom_thumbnail(video['title'], "Space Documentary", output_path=f"assets/thumb_{video['id']}.jpg")
        
        if thumbnail_path and os.path.exists(thumbnail_path):
            print("  [*] Uploading new thumbnail to YouTube...")
            try:
                youtube.thumbnails().set(
                    videoId=video['id'],
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                print("  [+] Thumbnail updated successfully!")
            except Exception as e:
                print(f"  [-] Failed to update thumbnail: {e}")
        else:
            print("  [-] Failed to generate thumbnail.")
            
        time.sleep(2) # Prevent API rate limits

    print("\\n" + "="*60)
    print("✅ BATCH UPDATE COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    main()
