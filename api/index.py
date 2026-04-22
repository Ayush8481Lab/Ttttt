from flask import Flask, request, jsonify
import yt_dlp
import os
import shutil

app = Flask(__name__)

@app.route('/api/metadata')
def get_metadata():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Please provide a YouTube URL via the ?url= parameter"}), 400

    # 1. Get the path to your static cookies.txt inside the read-only deployment directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    source_cookie_path = os.path.join(current_dir, 'cookies.txt')
    
    # 2. Define a writable path in the serverless /tmp directory
    tmp_cookie_path = '/tmp/cookies.txt'
    cookie_status = "Missing"
    
    # 3. Copy the cookie file to /tmp/ so yt-dlp can safely read/write/lock it
    if os.path.exists(source_cookie_path):
        try:
            shutil.copy(source_cookie_path, tmp_cookie_path)
            cookie_status = "Found and Copied to /tmp"
        except Exception as e:
            return jsonify({"error": f"Failed to copy cookies to tmp: {str(e)}"}), 500
    else:
        tmp_cookie_path = None

    # Configure yt-dlp to USE the writable temp cookies file
    ydl_opts = {
        'quiet': True,
        'skip_download': True,  # Ensures it executes under 5 seconds
        'extract_flat': False,
        'cookiefile': tmp_cookie_path, # Pass the /tmp/ path here!
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
                        "url": f.get("url") # The direct redirect link
                    } 
                    for f in info.get("formats", [])
                    if f.get("url") # Only return streams that have a valid URL
                ]
            }
            return jsonify(response)
            
    except Exception as e:
        return jsonify({
            "error": str(e), 
            "cookie_status": cookie_status
        }), 500

# Required for Vercel Python runtime
if __name__ == '__main__':
    app.run(debug=True)
