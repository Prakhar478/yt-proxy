from flask import Flask, jsonify
import yt_dlp
import os

app = Flask(__name__)

COOKIES_FILE = "cookies.txt"

@app.route("/stream/<video_id>")
def get_stream(video_id):
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }
        if os.path.exists(COOKIES_FILE):
            ydl_opts["cookiefile"] = COOKIES_FILE

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            formats = info.get("formats", [])

            # Pick best audio-only format
            audio = [f for f in formats if f.get("acodec") not in (None, "none") and f.get("vcodec") in (None, "none") and f.get("url")]
            
            # Fallback: any format with a url
            if not audio:
                audio = [f for f in formats if f.get("url")]

            if not audio:
                return jsonify({"error": "No formats found"}), 404

            best = sorted(audio, key=lambda x: x.get("abr") or x.get("tbr") or x.get("br") or 0, reverse=True)[0]
            
            return jsonify({
                "streamUrl": best["url"],
                "mimeType": best.get("ext", ""),
                "duration": int(info.get("duration", 0)),
                "title": info.get("title", ""),
                "thumbnail": info.get("thumbnail", "")
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/formats/<video_id>")
def list_formats(video_id):
    try:
        ydl_opts = {"quiet": True}
        if os.path.exists(COOKIES_FILE):
            ydl_opts["cookiefile"] = COOKIES_FILE
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            formats = [{"id": f.get("format_id"), "ext": f.get("ext"), "acodec": f.get("acodec"), "vcodec": f.get("vcodec"), "abr": f.get("abr"), "url_exists": bool(f.get("url"))} for f in info.get("formats", [])]
            return jsonify(formats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
