import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

# Import discovery logic
from reddit_matrix import VIBE_KEYS, CATEGORY_RULES, classify_title, seed_query_from_title

BASE_DIR = Path(__file__).resolve().parent
WEB_APP_DIR = BASE_DIR / "web_app"
RADIO_DIR = WEB_APP_DIR / "radio"
YTDLP_BIN = BASE_DIR / "tools" / "yt-dlp"

# High-fidelity settings
SLEEP_BETWEEN_DOWNLOADS_SECONDS = 2
BITRATE = "320"
# Directory mapping (Unified with server.py)
VIBE_TO_DIR = {
    "Cinematic Aura": "cinematic_aura",
    "Mental Agony": "mental_agony",
    "True Warrior": "true_warrior",
    "God Complex": "god_complex",
}

def ensure_directories() -> None:
    for folder in VIBE_TO_DIR.values():
        (RADIO_DIR / folder).mkdir(parents=True, exist_ok=True)

async def run_command(*args: str) -> tuple[int, str, str]:
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return process.returncode, stdout.decode("utf-8", errors="ignore"), stderr.decode("utf-8", errors="ignore")

async def discover_metadata(query: str) -> Optional[dict]:
    """Surgically finds high-impact edits (Preferred 2026)."""
    import random
    code, out, err = await run_command(
        str(YTDLP_BIN),
        "--no-warnings",
        "--skip-download",
        "--print",
        "id,title,uploader,duration,webpage_url",
        f"ytsearch20:{query}",
    )
    if code != 0:
        return None
    
    all_lines = out.strip().splitlines()
    results = []
    for i in range(0, len(all_lines), 5):
        if i + 4 < len(all_lines):
            try:
                duration_str = all_lines[i+3]
                parts = list(map(int, duration_str.split(':')))
                total_seconds = 0
                if len(parts) == 1: total_seconds = parts[0]
                elif len(parts) == 2: total_seconds = parts[0] * 60 + parts[1]
                
                # Edits are usually short and impactful
                if 5 <= total_seconds <= 120:
                    results.append({
                        "id": all_lines[i],
                        "title": all_lines[i+1],
                        "uploader": all_lines[i+2],
                        "duration": total_seconds,
                        "url": all_lines[i+4]
                    })
            except Exception: continue
    
    if not results:
        return None
    return random.choice(results)

def already_downloaded(vibe_dir: Path, video_id: str) -> bool:
    return any(vibe_dir.glob(f"{video_id}__*.mp3"))

async def harvest_track(vibe: str, query: str) -> bool:
    folder = VIBE_TO_DIR.get(vibe, "true_warrior")
    vibe_dir = RADIO_DIR / folder
    meta = await discover_metadata(query)
    if not meta:
        return False

    video_id = meta["id"]
    if already_downloaded(vibe_dir, video_id):
        print(f"[=] Skip existing track [{vibe}] '{meta['title']}'")
        return True

    # High-class file naming
    safe_title = "".join([c for c in meta["title"] if c.isalnum() or c in " _-"]).strip()[:50]
    filename_base = f"{video_id}__{safe_title}"
    output_path = vibe_dir / f"{filename_base}.mp3"
    meta_path = vibe_dir / f"{filename_base}.json"

    print(f"[+] Harvesting [{vibe}] '{meta['title']}' (High Fidelity {BITRATE}k)")

    code, _, err = await run_command(
        str(YTDLP_BIN),
        "--no-warnings",
        "--extract-audio",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",  # Best quality
        "--metadata-from-title", "%(artist)s - %(title)s",
        "--add-metadata",
        "-o",
        str(output_path),
        meta["url"],
    )

    if code == 0:
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        print(f"[✓] Harvest complete: {output_path.name}")
        return True
    else:
        print(f"[-] Harvest failed: {err.strip()}")
        return False

async def run_harvester() -> None:
    from reddit_matrix import fetch_titles, classify_title, seed_query_from_title, REDDIT_FEEDS
    ensure_directories()
    print("[*] Void Deep Harvester 3.0 (Matrix-Linked) online.")

    # TikTok Elite Creators & Trends (Paradox, Aezfarul, Reap, FF3F)
    VIBE_BASE = {
        "Cinematic Aura": [
            "2026 tiktok anime edit @ff3f.films tanjiro love me", 
            "2026 tiktok anime edit @reap.iko shinobu love me",
            "2026 tiktok batman dark knight @paradox.creations aura",
            "2026 gojo satoru aura audio tough tiktok",
            "2026 cinematic anime edit audio elite creator",
            "2026 anime aura edit @ff3f.films viral"
        ],
        "Mental Agony": [
            "2026 tiktok anime agony @reap.iko shinobu edit", 
            "2026 tragedy anime edit audio emotional tiktok",
            "2026 thorfinn scream edit audio agonizing tiktok",
            "2026 kaneki ken breakdown dialogue tiktok",
            "2026 agonizing anime edit audio @ff3f.films",
            "2026 mental agony anime edit peak tiktok"
        ],
        "True Warrior": [
            "2026 thorfinn no enemies dub edit tiktok", 
            "2026 vinland saga stoic dialogue @paradox.creations",
            "2026 musashi miyamoto discipline audio tiktok",
            "2026 vagabond manga aesthetic edit audio tiktok",
            "2026 stoic warrior motivation tiktok @aezfarul.x",
            "2026 peaceful warrior dialogue anime tiktok"
        ],
        "God Complex": [
            "2026 toji fushiguro this mf is different @aezfarul.x",
            "2026 batman bruce wayne menacing @paradox.creations",
            "2026 sukuna stand proud english dub tiktok edit",
            "2026 madara uchiha arrogant dialogue tiktok",
            "2026 tough anime edit dub testosterone tiktok",
            "2026 toji fushiguro aggressive audio tiktok",
            "2026 gilgamesh arrogant king edit audio tiktok",
            "2026 comeback arc motivation anime edit tiktok",
            "2026 homelander egoistic edit audio tiktok"
        ]
    }

    while True:
        # 1. Harvest from Reddit Matrix (Fresh Trends)
        print("[*] Matrix Sync: Polling Reddit for new trends...")
        for name, url in REDDIT_FEEDS.items():
            titles = fetch_titles(url)
            for title in titles:
                vibe = classify_title(title)
                query = seed_query_from_title(title)
                if vibe in VIBE_BASE:
                    await harvest_track(vibe, query)
                    await asyncio.sleep(SLEEP_BETWEEN_DOWNLOADS_SECONDS)

        # 2. Harvest from Base Pool (Consistent Vibe)
        for vibe, queries in VIBE_BASE.items():
            import random
            query = random.choice(queries) # Randomly pick from base pool
            try:
                await harvest_track(vibe, query)
            except Exception as exc:
                print(f"[-] System error: {exc}")
            await asyncio.sleep(SLEEP_BETWEEN_DOWNLOADS_SECONDS)
        
        print("[*] Cycle complete. Idling...")
        await asyncio.sleep(30)

if __name__ == "__main__":
    try:
        asyncio.run(run_harvester())
    except KeyboardInterrupt:
        print("\n[*] Harvester stopped.")
