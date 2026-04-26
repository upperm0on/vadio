import http.server
import json
import os
import socketserver
import subprocess

PORT = 8090
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web_app")
YTDLP_PATH = os.path.join(BASE_DIR, "tools", "yt-dlp")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_POST(self):
        try:
            if self.path != "/generate":
                self.send_response(404)
                self.end_headers()
                return

            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0:
                self._send_json(400, {"error": "Missing POST body."})
                return

            payload = self.rfile.read(content_length)
            data = json.loads(payload.decode("utf-8"))
            quote_query = data.get("quote", "thorfinn no enemies edit")
            print(f"[Master] New task received: {quote_query}")

            cmd = [
                YTDLP_PATH,
                "--get-url",
                f"ytsearch1:{quote_query} tiktok edit",
                "--no-warnings",
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            stream_url = (result.stdout or "").strip().splitlines()
            if not stream_url:
                raise RuntimeError("No direct stream URL returned by yt-dlp.")

            print("[Stream] Direct source ready.")
            self._send_json(200, {"url": stream_url[0]})

        except subprocess.CalledProcessError as e:
            print(f"[Stream] Failed to resolve direct source: {e}")
            self._send_json(500, {"error": "Failed to resolve direct source."})
        except json.JSONDecodeError as e:
            print(f"[Request] Invalid JSON payload: {e}")
            self._send_json(400, {"error": "Invalid JSON payload."})
        except Exception as e:
            print(f"[Server] Unexpected error in do_POST: {e}")
            self._send_json(500, {"error": "Internal server error."})


with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"[System] Void Ripper online on port {PORT}")
    httpd.serve_forever()
