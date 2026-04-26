import http.server
import json
import os
import random
import socketserver
from pathlib import Path
from collections import deque

PORT = 8090
BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "react_v2" / "dist"
RADIO_DIR = BASE_DIR / "radio"

VIBE_PATHS = {
    "cinematic aura": "cinematic_aura",
    "mental agony": "mental_agony",
    "true warrior": "true_warrior",
    "god complex": "god_complex",
}

# State for entropy check: prevent recent repeats. 
# Map of vibe -> deque of recently played filenames.
RECENT_TRACKS = {v.replace(" ", "_"): deque(maxlen=5) for v in VIBE_PATHS.keys()}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)

    def do_GET(self) -> None:
        if self.path.startswith("/radio/"):
            import urllib.parse
            import mimetypes
            
            # Extract and unquote path, stripping query parameters
            parsed_url = urllib.parse.urlparse(self.path)
            rel_path = parsed_url.path[len("/radio/"):]
            decoded_path = urllib.parse.unquote(rel_path)
            full_path = RADIO_DIR / decoded_path
            
            if full_path.exists() and full_path.is_file():
                content_type, _ = mimetypes.guess_type(str(full_path))
                self.send_response(200)
                self.send_header("Content-Type", content_type or "audio/mpeg")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(full_path.stat().st_size))
                self.end_headers()
                with open(full_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                print(f"[!] 404 ERROR: File not found at {full_path}")
                self._send_json(404, {"error": "File not found."})
                return

        # Fallback to default handler for React assets
        super().do_GET()

    def translate_path(self, path):
        # We don't need the override anymore if we handle do_GET
        return super().translate_path(path)

    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def _resolve_vibe_directory(self, raw_vibe: str | None) -> Path:
        key = (raw_vibe or "discipline").strip().lower()
        folder = VIBE_PATHS.get(key, "discipline")
        return RADIO_DIR / folder

    def do_POST(self) -> None:
        if self.path != "/generate":
            self._send_json(404, {"error": "Not found."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length) if length > 0 else b"{}"
            data = json.loads(payload.decode("utf-8")) if payload else {}
            
            raw_vibe = data.get("vibe", "discipline")
            vibe_dir = self._resolve_vibe_directory(raw_vibe)
            vibe_key = vibe_dir.name

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

            # Entropy Check: Filter out recently played tracks if possible
            recent = RECENT_TRACKS.get(vibe_key, deque())
            available_tracks = [t for t in tracks if t not in recent]
            
            # If all tracks are in recent (e.g., very few tracks downloaded), fall back to any track
            if not available_tracks:
                available_tracks = tracks
                
            filename = random.choice(available_tracks)
            recent.append(filename)

            # Resolve the relative URL for the browser
            # Radio files are served relative to the BASE_DIR
            filename_url = f"/radio/{vibe_key}/{filename}"
            
            # Load High-Fidelity Metadata
            meta_path = vibe_dir / f"{Path(filename).stem}.json"
            track_meta = {}
            if meta_path.exists():
                with open(meta_path, "r") as mf:
                    track_meta = json.load(mf)
                    
            response_payload = {
                "url": filename_url,
                "seed": Path(filename).stem,
                "metadata": track_meta
            }
            self._send_json(200, response_payload)
            
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON payload."})
        except Exception as exc:
            self._send_json(500, {"error": f"Server error: {exc}"})


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"[*] Void Local Delivery API (High Class Edition) online on port {PORT}")
        httpd.serve_forever()
