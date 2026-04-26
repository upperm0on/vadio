import http.server
import json
import os
import random
import socketserver
import subprocess

PORT = 8090
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web_app")
YTDLP_PATH = os.path.join(BASE_DIR, "tools", "yt-dlp")
MATRIX_PATH = os.path.join(WEB_DIR, "matrix.json")
DEFAULT_MATRIX = {
    "God Complex": ["sigma phonk god complex edit", "alpha grindset domination phonk"],
    "Spite": ["revenge workout phonk edit", "prove them wrong gym motivation"],
    "Discipline": ["discipline over motivation gym edit", "cold routine no excuses phonk"],
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def _load_matrix(self):
        if not os.path.isfile(MATRIX_PATH):
            return DEFAULT_MATRIX

        try:
            with open(MATRIX_PATH, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            if not isinstance(data, dict):
                return DEFAULT_MATRIX
            return data
        except (OSError, json.JSONDecodeError):
            return DEFAULT_MATRIX

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
            vibe = data.get("vibe", "Discipline")

            matrix = self._load_matrix()
            options = matrix.get(vibe) or DEFAULT_MATRIX.get(vibe) or DEFAULT_MATRIX["Discipline"]
            seed_query = random.choice(options)
            print(f"[Master] Vibe={vibe} | Seed={seed_query}")

            cmd = [
                YTDLP_PATH,
                "--get-url",
                f"ytsearch1:{seed_query}",
                "--no-warnings",
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            stream_url = (result.stdout or "").strip().splitlines()
            if not stream_url:
                raise RuntimeError("No direct stream URL returned by yt-dlp.")

            self._send_json(200, {"url": stream_url[0], "vibe": vibe, "seed": seed_query})

        except subprocess.CalledProcessError as exc:
            print(f"[Stream] Failed to resolve direct source: {exc}")
            self._send_json(500, {"error": "Failed to resolve direct source."})
        except json.JSONDecodeError as exc:
            print(f"[Request] Invalid JSON payload: {exc}")
            self._send_json(400, {"error": "Invalid JSON payload."})
        except Exception as exc:
            print(f"[Server] Unexpected error in do_POST: {exc}")
            self._send_json(500, {"error": "Internal server error."})


with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"[System] Void Ripper online on port {PORT}")
    httpd.serve_forever()
