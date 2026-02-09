from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import yt_dlp
import subprocess
import os
import uuid

BASE_URL = "https://video-server-py-1l4e.onrender.com"

app = FastAPI(title="MyAI Video Server")

# ===== PATHS =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAILER_DIR = os.path.join(BASE_DIR, "static", "trailers")
THUMB_DIR = os.path.join(BASE_DIR, "static", "thumbs")

os.makedirs(TRAILER_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)

# ===== STATIC =====
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# =========================================================
# 🎞️ VIDEO SEARCH + TRAILER GENERATION
# =========================================================
@app.get("/videos/search")
def search_videos(q: str):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True
    }

    results = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search = ydl.extract_info(f"ytsearch7:{q}", download=False)

    for entry in search.get("entries", []):
        video_id = entry["id"]
        title = entry["title"]
        thumb_url = entry["thumbnail"]

        local_trailer = os.path.join(TRAILER_DIR, f"{video_id}.mp4")

        # 🎬 GENERATE TRAILER IF NOT EXISTS
        if not os.path.exists(local_trailer):
            generate_trailer(video_id, local_trailer)

        results.append({
            "id": video_id,
            "title": title,
            "thumbnail": thumb_url,
            "trailer_url": f"{BASE_URL}/static/trailers/{video_id}.mp4",
            "player_url": f"{BASE_URL}/player/{video_id}"
        })

    return JSONResponse(results)


# =========================================================
# ✂️ TRAILER GENERATOR (7s, no audio)
# =========================================================
def generate_trailer(video_id, out_path):
    url = f"https://www.youtube.com/watch?v={video_id}"

    tmp_file = f"/tmp/{uuid.uuid4()}.mp4"

    ydl_opts = {
        "format": "mp4",
        "outtmpl": tmp_file,
        "quiet": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", tmp_file,
            "-t", "7",
            "-an",
            "-movflags", "faststart",
            out_path
        ], check=True)

    except Exception as e:
        print("TRAILER ERROR:", e)

    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)


# =========================================================
# ▶️ UNIFIED PROFESSIONAL PLAYER
# =========================================================
@app.get("/player/{video_id}", response_class=HTMLResponse)
def player(request: Request, video_id: str):
    video_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1&controls=1&rel=0"

    return templates.TemplateResponse(
        "player.html",
        {
            "request": request,
            "video_url": video_url
        }
    )


# =========================================================
# ❤️ HEALTH CHECK
# =========================================================
@app.get("/")
def health():
    return {"status": "OK", "message": "MyAI Video Server running"}
    
