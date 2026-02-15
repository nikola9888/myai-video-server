from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import yt_dlp
import json
from fastapi import Request
from typing import List

app = FastAPI()

# Postavke za yt-dlp
YDL_OPTS = {
    "format": "best[ext=mp4]/best",
    "quiet": True,
    "no_warnings": True,
    "writesubtitles": True,
    "writeautomaticsub": True,
    "subtitlesformat": "vtt",
    "skip_download": True
}

# Endpoints
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
        <html>
            <head>
                <title>Video Server</title>
            </head>
            <body>
                <h1>Dobrodošli na Video Server</h1>
                <p>Video server koji omogućava pregled video sadržaja preko WebView-a u aplikaciji.</p>
            </body>
        </html>
    """

@app.get("/video/stream")
async def stream_video(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)

            # Pronađi MP4 stream
            stream_url = None
            for f in info.get("formats", []):
                if f.get("ext") == "mp4" and f.get("acodec") != "none":
                    stream_url = f.get("url")
                    break

            # Titlovi
            captions = []
            subs = info.get("subtitles") or info.get("automatic_captions")
            if subs:
                for lang, tracks in subs.items():
                    for t in tracks:
                        if t.get("ext") == "vtt":
                            captions.append({
                                "language": lang,
                                "url": t.get("url")
                            })
                            break
                    break  # samo jedan jezik

            return {
                "video_id": video_id,
                "title": info.get("title"),
                "stream_url": stream_url,
                "captions": captions
            }

    except Exception as e:
        return {"error": str(e)}

# HTML za prikazivanje videa putem WebView-a
@app.get("/video/player/{video_id}")
async def video_player(video_id: str):
    video_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1"
    html_code = f"""
    <html>
        <head>
            <title>Video Player</title>
        </head>
        <body>
            <h1>Video Player</h1>
            <iframe width="560" height="315" src="{video_url}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        </body>
    </html>
    """
    return HTMLResponse(content=html_code)

    # Služi kao API endpoint za pretragu video sadržaja.

@app.get("/videos/search")
async def search_videos(query: str):
    try:
        search_query = f"ytsearch10:{query}"

        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            results = ydl.extract_info(search_query, download=False)

        videos = []

        for entry in results.get("entries", []):
            if not entry:
                continue

            videos.append({
                "video_id": entry.get("id"),
                "title": entry.get("title"),
                "thumbnail": entry.get("thumbnail")
            })

        return videos

    except Exception as e:
        return {"error": str(e)}
        
# Start servera
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
