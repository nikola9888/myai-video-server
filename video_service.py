from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/videos/search")
def search_videos(q: str = Query(...)):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
        "forcejson": True,
    }

    query = f"ytsearch7:{q} shorts"

    videos = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(query, download=False)

        for e in result.get("entries", []):
            videos.append({
                "title": e.get("title"),
                "video_url": f"https://youtube.com/watch?v={e.get('id')}",
                "thumbnail": e.get("thumbnail"),
            })

    return videos
