from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/api/metadata')
def get_metadata():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Please provide a YouTube URL via the ?url= parameter"}), 400

    # Configure yt-dlp to bypass bot checks WITHOUT authentication
    ydl_opts = {
        'quiet': True,
        'skip_download': True,  # Ensures it executes under 5 seconds
        'extract_flat': False,
        # THE MAGIC TRICK: Spoof internal Android/iOS clients to bypass web captchas
        'extractor_args': {
            'youtube': ['client=android,ios,tv']
        }
    }

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
                # We extract exactly what you need: formats, codecs, and direct URLs
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
