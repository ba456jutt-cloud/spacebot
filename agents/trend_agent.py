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

        # Integrate Feedback Loop
        from agents.analytics_agent import get_past_performance_feedback
        import requests
        
        past_feedback = get_past_performance_feedback()
        print(f"[*] Fetched past performance feedback:\n{past_feedback}")
        
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key or gemini_api_key == "your_gemini_api_key_here":
            best_video = videos[0]
            print(f"[+] Trend Agent Selected Topic (No Gemini): '{best_video['title']}'")
            return {
                "video_id": best_video["id"],
                "title": best_video["title"],
                "description": best_video["description"],
                "tags": best_video.get("tags", [])
            }
            
        print("[*] Asking Gemini to generate a unique topic based on trends and past feedback...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
        
        # Prepare context of trending videos
        trending_context = "\\n".join([f"- {v['title']} ({v['viewCount']} views)" for v in videos[:5]])
        
        prompt = f"""You are a master YouTube strategist for a Space Documentary channel.
Your goal is to generate a single, mind-blowing, hyper-viral video topic.

Here is how our past videos performed:
{past_feedback}

Here are the current trending topics on YouTube right now:
{trending_context}

REQUIREMENTS:
1. If past videos about "Aliens" or "Knocking" performed poorly, DO NOT suggest them.
2. Formulate a COMPLETELY UNIQUE, dramatic, and terrifying topic that creates an unbearable curiosity gap.
3. The title must be under 85 characters.
4. Output ONLY the JSON with the title and description, nothing else.

OUTPUT FORMAT (Strict JSON):
{{
  "title": "...",
  "description": "..."
}}
"""
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.9}}
        
        try:
            resp = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
            resp.raise_for_status()
            result_text = resp.json()['candidates'][0]['content']['parts'][0]['text']
            result_text = result_text.replace("```json", "").replace("```", "").strip()
            ai_topic = json.loads(result_text)
            
            print(f"[+] Trend Agent (AI) Selected Topic: '{ai_topic['title']}'")
            return {
                "video_id": f"ai_gen_{os.urandom(4).hex()}",
                "title": ai_topic["title"],
                "description": ai_topic["description"],
                "tags": videos[0].get("tags", []) # Just borrow tags from the top trending video
            }
        except Exception as e:
            print(f"[-] Gemini Topic Generation failed: {e}. Falling back to top trending.")
            best_video = videos[0]
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
