from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/api/metadata')
def get_metadata():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Please provide a YouTube URL via the ?url= parameter"}), 400

    # Get the exact folder path where this index.py script is currently running
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Point yt-dlp exactly to the cookies.txt file in the same folder
    cookie_path = os.path.join(current_dir, 'cookies.txt')

    # Configure yt-dlp to USE the static cookies file
    ydl_opts = {
        'quiet': True,
        'skip_download': True,  # Ensures it executes under 5 seconds
        'extract_flat': False,
        'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
        'extractor_args': {
            'youtube':['client=tv,android,web']
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract metadata and formats
            info = ydl.extract_info(url, download=False)
            
            # Filter the response
            response = {
                "id": info.get("id"),
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "formats":[
                    {
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),
                        "vcodec": f.get("vcodec"),
                        "acodec": f.get("acodec"),
                        "url": f.get("url") # The direct redirect link you want!
                    } 
                    for f in info.get("formats", [])
                    if f.get("url") # Only return streams that have a valid URL
                ]
            }
            return jsonify(response)
            
    except Exception as e:
        return jsonify({
            "error": str(e), 
            "cookie_status": "Found" if os.path.exists(cookie_path) else "Missing"
        }), 500

# Required for Vercel Python runtime
if __name__ == '__main__':
    app.run(debug=True)
