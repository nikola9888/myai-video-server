from fastapi import FastAPI
import os
import requests

app = FastAPI()

YOUTUBE_API_KEY = os.getenv("YT_API_KEY")


@app.get("/")
def root():
    return {"status": "video server alive"}


@app.get("/videos/search")
def search_videos(q: str):
    if not YOUTUBE_API_KEY:
        return []

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": q,
        "key": YOUTUBE_API_KEY,
        "maxResults": 6,
        "type": "video"
    }

    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    videos = []
    for item in data.get("items", []):
        videos.append({
            "title": item["snippet"]["title"],
            "thumb": item["snippet"]["thumbnails"]["medium"]["url"],
            "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        })

    return videos
    
