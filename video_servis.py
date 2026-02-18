from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

# ✅ CORS (bitno za mobile app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

@app.get("/")
def root():
    return {
        "status": "OK",
        "service": "MyAI Video Server",
        "provider": "YouTube Data API"
    }

@app.get("/videos/search")
def search_videos(query: str):
    if not YOUTUBE_API_KEY:
        return {"error": "YOUTUBE_API_KEY not set"}

    try:
        url = "https://www.googleapis.com/youtube/v3/search"

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 8,
            "safeSearch": "strict",
            "key": YOUTUBE_API_KEY
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        videos = []

        for item in data.get("items", []):
            videos.append({
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
            })

        return videos

    except Exception as e:
        return {"error": str(e)}
