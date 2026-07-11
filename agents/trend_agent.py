import os
import json
from googleapiclient.discovery import build
from dotenv import load_dotenv
from agents.db_agent import is_trend_processed

load_dotenv()

def get_trending_space_topic() -> dict:
    """
    Searches YouTube for highly viewed, recent videos in the Space & Universe niche.
    Returns a dictionary with the title, description, tags, and video_id of a high-performing video
    that hasn't been processed yet.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    fallback_data = {
        "video_id": "fallback_123",
        "title": "The Fermi Paradox: Where Are All The Aliens?",
        "description": "An exploration of the Fermi Paradox and the search for extraterrestrial life.",
        "tags": ["space", "universe", "aliens", "fermi paradox"]
    }
    
    if not api_key or api_key == "your_youtube_api_key_here":
        print("[-] YOUTUBE_API_KEY not set. Using a fallback topic.")
        return fallback_data

    print("[*] Trend Agent: Searching YouTube for trending Space topics...")
    youtube = build("youtube", "v3", developerKey=api_key)
    
    try:
        # Search for recent highly relevant space videos
        search_response = youtube.search().list(
            q="space universe documentary mystery",
            part="id,snippet",
            maxResults=15,
            type="video",
            order="viewCount",
            relevanceLanguage="en",
            publishedAfter="2025-01-01T00:00:00Z"
        ).execute()

        videos = []
        for search_result in search_response.get("items", []):
            if search_result["id"]["kind"] == "youtube#video":
                video_id = search_result["id"]["videoId"]
                
                # Check DB for duplicates
                if is_trend_processed(video_id):
                    print(f"  [-] Skipping already processed video: {video_id}")
                    continue
                    
                title = search_result["snippet"]["title"].split("|")[0].strip()
                description = search_result["snippet"].get("description", "")
                videos.append({"id": video_id, "title": title, "description": description})

        if not videos:
            print("[-] No new trends found. Using fallback.")
            return fallback_data

        # Fetch stats to calculate view velocity and get tags
        video_ids = ",".join([v["id"] for v in videos])
        stats_response = youtube.videos().list(
            part="statistics,snippet",
            id=video_ids
        ).execute()

        for i, stat in enumerate(stats_response.get("items", [])):
            videos[i]["viewCount"] = int(stat["statistics"].get("viewCount", 0))
            videos[i]["tags"] = stat["snippet"].get("tags", [])

        # Sort by views
        videos.sort(key=lambda x: x["viewCount"], reverse=True)
        best_video = videos[0]
        
        print(f"[+] Trend Agent Selected Topic: '{best_video['title']}' (Views: {best_video['viewCount']})")
        
        return {
            "video_id": best_video["id"],
            "title": best_video["title"],
            "description": best_video["description"],
            "tags": best_video.get("tags", [])
        }
    except Exception as e:
        print(f"[-] Trend Agent Error: {e}")
        return fallback_data

if __name__ == "__main__":
    trend = get_trending_space_topic()
    print(f"Test Selected Topic:\n{json.dumps(trend, indent=2)}")
