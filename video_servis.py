from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

YDL_OPTS = {
    "quiet": True,
    "skip_download": True,
    "extract_flat": False,
    "format": "best[ext=mp4]/best",
}

def search_youtube(query, limit=7):
    results = []

    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        search_url = f"ytsearch{limit}:{query}"
        info = ydl.extract_info(search_url, download=False)

        for entry in info.get("entries", []):
            if not entry:
                continue

            results.append({
                "title": entry.get("title"),
                "thumbnail": entry.get("thumbnail"),
                "video_url": entry.get("url"),
                "embed_url": f"https://www.youtube.com/embed/{entry.get('id')}",
                "duration": entry.get("duration"),
            })

    return results


@app.route("/videos/search", methods=["GET"])
def search_videos():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query"}), 400

    try:
        videos = search_youtube(query)
        return jsonify(videos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/videos/player", methods=["GET"])
def video_player():
    video_id = request.args.get("id")
    if not video_id:
        return "Missing video id", 400

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                margin: 0;
                background: black;
            }}
            iframe {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                border: none;
            }}
        </style>
    </head>
    <body>
        <iframe 
            src="https://www.youtube.com/embed/{video_id}?autoplay=1&controls=1"
            allow="autoplay; encrypted-media"
            allowfullscreen>
        </iframe>
    </body>
    </html>
    """


@app.route("/")
def health():
    return {"status": "ok", "service": "video-server"}
    
