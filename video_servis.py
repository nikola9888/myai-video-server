from fastapi import FastAPI, HTTPException
import requests
from yt_dlp import YoutubeDL
import os

app = FastAPI()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# ===============================
# HEALTH CHECK
# ===============================
@app.get("/")
def home():
    return {
        "status": "OK",
        "service": "MyAI Video Server",
        "provider": "YouTube Data API + yt-dlp Preview"
    }


# ===============================
# SEARCH VIDEO (precizna pretraga)
# ===============================
@app.get("/search")
def search_video(query: str):

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": query,
        "key": YOUTUBE_API_KEY,
        "maxResults": 1,
        "type": "video",
        "videoEmbeddable": "true"
    }

    r = requests.get(url, params=params)
    data = r.json()

    if "items" not in data or not data["items"]:
        raise HTTPException(status_code=404, detail="No video found")

    video = data["items"][0]

    video_id = video["id"]["videoId"]
    title = video["snippet"]["title"]
    thumbnail = video["snippet"]["thumbnails"]["high"]["url"]

    return {
        "video_id": video_id,
        "title": title,
        "thumbnail": thumbnail
    }


# ===============================
# PREVIEW (yt-dlp trailer engine)
# ===============================
@app.get("/preview/{video_id}")
def preview(video_id: str):

    ydl_opts = {
        "quiet": True,
        "format": "best[height<=360][ext=mp4]",
        "noplaylist": True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}",
                download=False
            )

            preview_url = info.get("url")

            if not preview_url:
                raise Exception("Preview URL not found")

            return {
                "video_id": video_id,
                "preview_url": preview_url
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
