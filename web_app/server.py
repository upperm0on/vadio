import http.server
import json
import os
import random
import socketserver
from pathlib import Path

PORT = 8090
WEB_DIR = Path(__file__).resolve().parent
RADIO_DIR = WEB_DIR / "radio"

VIBE_PATHS = {
    "god complex": "god_complex",
    "god_complex": "god_complex",
    "god": "god_complex",
    "spite": "spite",
    "pure spite": "spite",
    "discipline": "discipline",
    "cold discipline": "discipline",
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _resolve_vibe_directory(self, raw_vibe: str | None) -> Path:
        key = (raw_vibe or "discipline").strip().lower()
        folder = VIBE_PATHS.get(key, "discipline")
        return RADIO_DIR / folder

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/generate":
            self._send_json(404, {"error": "Not found."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length) if length > 0 else b"{}"
            data = json.loads(payload.decode("utf-8")) if payload else {}
            vibe_dir = self._resolve_vibe_directory(data.get("vibe"))

            if not vibe_dir.exists():
                vibe_dir.mkdir(parents=True, exist_ok=True)

            tracks = [f for f in os.listdir(vibe_dir) if f.lower().endswith(".mp3")]
            if not tracks:
                self._send_json(
                    503,
                    {
                        "error": "No local tracks available yet. Harvester is still collecting audio.",
                        "status": "harvesting",
                    },
                )
                return

            filename = random.choice(tracks)
            rel_dir = vibe_dir.relative_to(WEB_DIR).as_posix()
            seed = Path(filename).stem
            self._send_json(200, {"url": f"/{rel_dir}/{filename}", "seed": seed})
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON payload."})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"error": f"Server error: {exc}"})


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"[System] Void local radio server online on port {PORT}")
        httpd.serve_forever()
