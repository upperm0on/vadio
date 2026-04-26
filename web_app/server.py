import http.server
import socketserver
import json
import subprocess
import os

PORT = 8090
WEB_DIR = "/data/workspace/web_app"
FFMPEG_PATH = "/data/workspace/tools/ffmpeg"
YTDLP_PATH = "/data/workspace/tools/yt-dlp"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_POST(self):
        if self.path == '/generate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            quote_query = data.get('quote', 'Thorfinn no enemies edit')
            print(f"[Master] New task received: {quote_query}")
            
            out_file = f"{WEB_DIR}/final_edit.mp3"
            if os.path.exists(out_file):
                os.remove(out_file)

            # Route through SoundCloud to completely bypass TikTok/YouTube datacenter IP blocks
            print(f"[Extractor] Ripping from SoundCloud database: {quote_query}")
            cmd = [
                YTDLP_PATH, 
                f"scsearch1:{quote_query} phonk audio", 
                "-x", 
                "--audio-format", "mp3", 
                "--audio-quality", "0",
                "--ffmpeg-location", FFMPEG_PATH,
                "-o", f"{WEB_DIR}/final_edit.%(ext)s", 
                "--force-overwrites"
            ]
            
            try:
                subprocess.run(cmd, check=True)
                print("[Audio] Audio successfully ripped.")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"url": "/final_edit.mp3"}).encode())
            except Exception as e:
                print(f"[Audio] Failed to rip: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Failed to extract audio from source."}).encode())
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"[System] Void Ripper online on port {PORT}")
    httpd.serve_forever()
