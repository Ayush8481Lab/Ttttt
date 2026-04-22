from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/api/metadata')
def get_metadata():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Please provide a YouTube Music URL via the ?url= parameter"}), 400

    # Configure yt-dlp specifically for YouTube Music and Audio-Only extraction
    ydl_opts = {
        'quiet': True,
        'skip_download': True,  # Ensures it executes under 5 seconds
        'extract_flat': False,
        'format': 'bestaudio/best', # Tell yt-dlp we only care about audio streams
        'extractor_args': {
            # THE NEW TRICK: Spoof the YouTube Music specific clients
            'youtube':['client=android_music,web_music,mweb']
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    proxy_url = os.environ.get('PROXY_URL')
    if proxy_url:
        ydl_opts['proxy'] = proxy_url

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract metadata
            info = ydl.extract_info(url, download=False)
            
            # Filter the response specifically for SONGS
            response = {
                "id": info.get("id"),
                "title": info.get("title"),
                "artist": info.get("uploader"), # Captures the Artist name
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                # Filter out video streams, keep ONLY audio formats (m4a, webm, etc)
                "formats":[
                    {
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),         # e.g., 'm4a' or 'webm'
                        "acodec": f.get("acodec"),   # e.g., 'mp4a.40.2'
                        "vcodec": f.get("vcodec"),   # Should be 'none' for songs
                        "abr": f.get("abr"),         # Audio Bitrate
                        "url": f.get("url")          # The direct redirect link!
                    } 
                    for f in info.get("formats", [])
                    if f.get("url") and f.get("acodec") != 'none' and f.get("vcodec") == 'none'
                ]
            }
            return jsonify(response)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Required for Vercel Python runtime
if __name__ == '__main__':
    app.run(debug=True)
