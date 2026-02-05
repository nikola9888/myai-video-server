from fastapi import FastAPI
import requests
import os

app = FastAPI()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

@app.get("/videos/search")
def search_videos(q: str):
    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "key": YOUTUBE_API_KEY,
        "q": q,
        "part": "snippet",
        "type": "video",
        "maxResults": 5,
        "regionCode": "RS",
        "relevanceLanguage": "sr"
    }

    r = requests.get(url, params=params)
    data = r.json()

    print("YOUTUBE RAW:", data)  # 🔥 OVO JE KLJUČNO

    results = []

    for item in data.get("items", []):
        results.append({
            "title": item["snippet"]["title"],
            "video_id": item["id"]["videoId"],
            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
        })

    return results
    
