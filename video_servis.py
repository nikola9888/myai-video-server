from fastapi import FastAPI, Query
import requests
import os

app = FastAPI()

YOUTUBE_API_KEY = os.getenv("AIzaSyDAyoNnRdGKoWVyTuGaK0S6Ks6V01Zhj6Y")

@app.get("/videos/search")
def search_videos(q: str = Query(...)):
    if not YOUTUBE_API_KEY:
        return {"error": "YOUTUBE_API_KEY missing"}

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": q,
        "key": YOUTUBE_API_KEY,
        "maxResults": 5,
        "type": "video"
    }

    r = requests.get(url, params=params)
    data = r.json()

    videos = []
    for item in data.get("items", []):
        videos.append({
            "title": item["snippet"]["title"],
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
            "video_id": item["id"]["videoId"]
        })

    return videos
    
