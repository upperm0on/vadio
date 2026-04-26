import http.server
import json
import os
import socketserver
import subprocess

import redis

PORT = 8090
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web_app")
YTDLP_PATH = os.path.join(BASE_DIR, "tools", "yt-dlp")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

VIBE_KEYS = {
    "God Complex": "vibe:god_complex",
    "Spite": "vibe:spite",
    "Discipline": "vibe:discipline",
}


def normalize_vibe(vibe):
    if not isinstance(vibe, str):
        return "Discipline"

    cleaned = vibe.strip().lower()
    if cleaned in {"god complex", "god_complex", "god"}:
        return "God Complex"
    if cleaned in {"spite", "pure spite"}:
        return "Spite"
    return "Discipline"


def redis_client():
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def _random_seed_query(self, vibe):
        normalized = normalize_vibe(vibe)
        key = VIBE_KEYS[normalized]
        client = redis_client()
        query = client.srandmember(key)
        if not query:
            raise RuntimeError(f"No cached queries in Redis set: {key}. Run reddit_matrix.py first.")
        return normalized, query

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
            requested_vibe = data.get("vibe", "Discipline")

            vibe, seed_query = self._random_seed_query(requested_vibe)
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

        except redis.RedisError as exc:
            print(f"[Redis] Failed to read vibe set: {exc}")
            self._send_json(500, {"error": "Redis is unavailable."})
        except subprocess.CalledProcessError as exc:
            print(f"[Stream] Failed to resolve direct source: {exc}")
            self._send_json(500, {"error": "Failed to resolve direct source."})
        except json.JSONDecodeError as exc:
            print(f"[Request] Invalid JSON payload: {exc}")
            self._send_json(400, {"error": "Invalid JSON payload."})
        except Exception as exc:
            print(f"[Server] Unexpected error in do_POST: {exc}")
            self._send_json(500, {"error": str(exc) if str(exc) else "Internal server error."})


with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"[System] Void Ripper online on port {PORT}")
    httpd.serve_forever()
