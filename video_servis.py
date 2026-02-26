 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/video_servis.py b/video_servis.py
index 7d1dfd56b43da0254e263b2e036cbaa5857f200e..687ee89c699924fe4707edc8adab711d1b9835b7 100644
--- a/video_servis.py
+++ b/video_servis.py
@@ -1,88 +1,227 @@
-from fastapi import FastAPI, HTTPException
+import os
+from functools import lru_cache
+from typing import Any
+
 import requests
+from fastapi import FastAPI, HTTPException, Query
+from requests.adapters import HTTPAdapter
+from urllib3.util.retry import Retry
 from yt_dlp import YoutubeDL
-import os
 
-app = FastAPI()
+app = FastAPI(
+    title="MyAI Video Server",
+    description="Fast YouTube trailer search + preview API for AI applications.",
+    version="2.0.0",
+)
 
 YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
+YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
+YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
+DEFAULT_RESULT_COUNT = 7
+
+
+@lru_cache(maxsize=1)
+def get_http_session() -> requests.Session:
+    """Shared HTTP session with connection pooling + retry for better latency and stability."""
+    session = requests.Session()
+    retry_strategy = Retry(
+        total=3,
+        backoff_factor=0.3,
+        status_forcelist=(429, 500, 502, 503, 504),
+        allowed_methods=("GET",),
+    )
+    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=retry_strategy)
+    session.mount("https://", adapter)
+    session.mount("http://", adapter)
+    return session
+
 
-# ===============================
-# HEALTH CHECK
-# ===============================
 @app.get("/")
-def home():
+def home() -> dict[str, str]:
     return {
         "status": "OK",
         "service": "MyAI Video Server",
-        "provider": "YouTube Data API + yt-dlp Preview"
+        "provider": "YouTube Data API + yt-dlp Preview",
+        "version": "2.0.0",
     }
 
 
-# ===============================
-# SEARCH VIDEO (precizna pretraga)
-# ===============================
-@app.get("/search")
-def search_video(query: str):
+def ensure_api_key() -> None:
+    if not YOUTUBE_API_KEY:
+        raise HTTPException(
+            status_code=500,
+            detail="YOUTUBE_API_KEY is not configured on the server.",
+        )
 
-    url = "https://www.googleapis.com/youtube/v3/search"
 
-    params = {
-        "part": "snippet",
-        "q": query,
-        "key": YOUTUBE_API_KEY,
-        "maxResults": 1,
-        "type": "video",
-        "videoEmbeddable": "true"
-    }
+def pick_best_thumbnail(thumbnails: dict[str, Any]) -> str | None:
+    for key in ("maxres", "standard", "high", "medium", "default"):
+        thumb = thumbnails.get(key)
+        if thumb and thumb.get("url"):
+            return thumb["url"]
+    return None
 
-    r = requests.get(url, params=params)
-    data = r.json()
-
-    if "items" not in data or not data["items"]:
-        raise HTTPException(status_code=404, detail="No video found")
-
-    video = data["items"][0]
-
-    video_id = video["id"]["videoId"]
-    title = video["snippet"]["title"]
-    thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
-
-    return {
-        "video_id": video_id,
-        "title": title,
-        "thumbnail": thumbnail
-    }
-
-
-# ===============================
-# PREVIEW (yt-dlp trailer engine)
-# ===============================
-@app.get("/preview/{video_id}")
-def preview(video_id: str):
 
+def get_preview_url(video_id: str) -> str | None:
+    """Extract direct preview stream URL for one video using yt-dlp."""
     ydl_opts = {
         "quiet": True,
-        "format": "best[height<=360][ext=mp4]",
-        "noplaylist": True
+        "no_warnings": True,
+        "format": "best[height<=360][ext=mp4]/best[height<=360]/best",
+        "noplaylist": True,
     }
 
     try:
         with YoutubeDL(ydl_opts) as ydl:
             info = ydl.extract_info(
                 f"https://www.youtube.com/watch?v={video_id}",
-                download=False
+                download=False,
             )
+            return info.get("url")
+    except Exception:
+        return None
 
-            preview_url = info.get("url")
 
-            if not preview_url:
-                raise Exception("Preview URL not found")
+@app.get("/search")
+def search_video(query: str = Query(..., min_length=2, description="Search term")) -> dict[str, Any]:
+    """Backward-compatible endpoint for single best result."""
+    result = search_trailers(query=query, limit=1, include_preview=False)
+    if not result["results"]:
+        raise HTTPException(status_code=404, detail="No video found")
+    item = result["results"][0]
+    return {
+        "video_id": item["video_id"],
+        "title": item["title"],
+        "thumbnail": item["thumbnail"],
+    }
+
+
+@app.get("/trailers")
+def search_trailers(
+    query: str = Query(..., min_length=2, description="AI question/topic"),
+    limit: int = Query(
+        DEFAULT_RESULT_COUNT,
+        ge=1,
+        le=10,
+        description="Number of trailers to return (default is 7).",
+    ),
+    include_preview: bool = Query(
+        True,
+        description="Whether to include direct preview_url from yt-dlp.",
+    ),
+) -> dict[str, Any]:
+    """
+    Professional endpoint for AI apps:
+    - returns up to 7 trailers per query,
+    - includes rich metadata + thumbnail list,
+    - optional preview stream URL per trailer.
+    """
+    ensure_api_key()
+
+    session = get_http_session()
+
+    search_params = {
+        "part": "snippet",
+        "q": f"{query} official trailer",
+        "key": YOUTUBE_API_KEY,
+        "maxResults": limit,
+        "type": "video",
+        "videoEmbeddable": "true",
+        "safeSearch": "moderate",
+        "regionCode": "US",
+        "relevanceLanguage": "en",
+        "order": "relevance",
+    }
 
-            return {
-                "video_id": video_id,
-                "preview_url": preview_url
+    try:
+        search_response = session.get(YOUTUBE_SEARCH_URL, params=search_params, timeout=8)
+        search_response.raise_for_status()
+        search_data = search_response.json()
+    except requests.RequestException as exc:
+        raise HTTPException(status_code=502, detail=f"YouTube search failed: {exc}") from exc
+
+    items = search_data.get("items", [])
+    if not items:
+        return {
+            "query": query,
+            "count": 0,
+            "image_count": 0,
+            "images": [],
+            "results": [],
+        }
+
+    video_ids = [item["id"]["videoId"] for item in items if item.get("id", {}).get("videoId")]
+
+    details_by_id: dict[str, dict[str, Any]] = {}
+    if video_ids:
+        details_params = {
+            "part": "contentDetails,statistics,snippet",
+            "id": ",".join(video_ids),
+            "key": YOUTUBE_API_KEY,
+            "maxResults": len(video_ids),
+        }
+        try:
+            details_response = session.get(YOUTUBE_VIDEO_URL, params=details_params, timeout=8)
+            details_response.raise_for_status()
+            details_data = details_response.json()
+            details_by_id = {
+                v["id"]: v for v in details_data.get("items", []) if v.get("id")
             }
+        except requests.RequestException:
+            details_by_id = {}
+
+    results: list[dict[str, Any]] = []
+    images: list[str] = []
+
+    for item in items:
+        vid = item.get("id", {}).get("videoId")
+        snippet = item.get("snippet", {})
+        if not vid:
+            continue
+
+        details = details_by_id.get(vid, {})
+        thumbs = snippet.get("thumbnails", {})
+        main_thumbnail = pick_best_thumbnail(thumbs)
+        if main_thumbnail:
+            images.append(main_thumbnail)
+
+        results.append(
+            {
+                "video_id": vid,
+                "title": snippet.get("title"),
+                "description": snippet.get("description"),
+                "channel_title": snippet.get("channelTitle"),
+                "published_at": snippet.get("publishedAt"),
+                "thumbnail": main_thumbnail,
+                "thumbnails": {
+                    key: value.get("url")
+                    for key, value in thumbs.items()
+                    if isinstance(value, dict) and value.get("url")
+                },
+                "youtube_url": f"https://www.youtube.com/watch?v={vid}",
+                "embed_url": f"https://www.youtube.com/embed/{vid}",
+                "duration": details.get("contentDetails", {}).get("duration"),
+                "view_count": details.get("statistics", {}).get("viewCount"),
+                "preview_url": get_preview_url(vid) if include_preview else None,
+            }
+        )
+
+    return {
+        "query": query,
+        "count": len(results),
+        "image_count": len(images),
+        "images": images,
+        "results": results,
+    }
+
 
-    except Exception as e:
-        raise HTTPException(status_code=500, detail=str(e))
+@app.get("/preview/{video_id}")
+def preview(video_id: str) -> dict[str, str]:
+    preview_url = get_preview_url(video_id)
+    if not preview_url:
+        raise HTTPException(status_code=500, detail="Preview URL not found")
+
+    return {
+        "video_id": video_id,
+        "preview_url": preview_url,
+    }
 
EOF
)
