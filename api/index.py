from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/api/metadata')
def get_metadata():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Please provide a YouTube URL via the ?url= parameter"}), 400

    # Configure yt-dlp with FIX 1: TV Client & Fake User-Agent
    ydl_opts = {
        'quiet': True,
        'skip_download': True,  # Ensures it executes under 5 seconds
        'extract_flat': False,
        'extractor_args': {
            # Bypasses mobile/web checks by acting like a Smart TV
            'youtube': ['client=tv']
        },
        'http_headers': {
            # Mimic a real Windows Chrome browser instead of a Python script
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    # Configure yt-dlp with FIX 2: Proxy Support (If needed)
    # If Vercel's IP is still blocked, add a PROXY_URL environment variable in your Vercel Dashboard
    proxy_url = os.environ.get('PROXY_URL')
    if proxy_url:
        ydl_opts['proxy'] = proxy_url

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract metadata without downloading
            info = ydl.extract_info(url, download=False)
            
            # Filter down the massive JSON to save bandwidth and prevent Vercel crashes
            response = {
                "id": info.get("id"),
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "formats":[
                    {
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),
                        "resolution": f.get("resolution"),
                        "vcodec": f.get("vcodec"),
                        "acodec": f.get("acodec"),
                        "url": f.get("url")
                    } 
                    for f in info.get("formats", [])
                    if f.get("url") # Ensure we only return entries that have a direct URL
                ]
            }
            return jsonify(response)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Required for Vercel Python runtime
if __name__ == '__main__':
    app.run(debug=True)
