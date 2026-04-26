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
    """Uses yt-dlp to find top 20 matches and filters for surgical 'Edit Audios' (< 90s)."""
    import random
    # Searching for edit audios, scenepacks, and SFX versions
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
                # Convert duration to seconds (H:M:S or M:S)
                parts = list(map(int, duration_str.split(':')))
                total_seconds = 0
                if len(parts) == 1: total_seconds = parts[0]
                elif len(parts) == 2: total_seconds = parts[0] * 60 + parts[1]
                elif len(parts) == 3: total_seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
                
                # STRICT FILTER: Edit audios are usually between 10s and 90s
                if 10 <= total_seconds <= 95:
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
        
    # Pick a random surgical edit
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

    # Iconic "Impact & Agony" Queries (Choirs, Screams, Dialogue)
    VIBE_BASE = {
        "Cinematic Aura": [
            "invincible omniman choir edit audio", 
            "perfect girl slowed reverb orchestral choir",
            "sukuna domain expansion audio with dialogue",
            "gojo hollow purple cinematic choir audio",
            "aizen bankai ethereal choir edit",
            "legendary anime aura audio with choir"
        ],
        "Mental Agony": [
            "thorfinn scream edit audio i'll kill you", 
            "eren yeager rumbling scream edit audio",
            "kaneki ken breakdown dialogue edit audio",
            "mental agony anime edit with raw screams",
            "berserk guts rage audio with dialogue",
            "agonizing anime edit audio for tiktok"
        ],
        "True Warrior": [
            "thorfinn i have no enemies dialogue audio", 
            "vinland saga thors philosophy dialogue edit",
            "musashi miyamoto stoic dialogue audio",
            "vagabond manga aesthetic with nature SFX",
            "stoic warrior anime dialogue audio",
            "peaceful anime warrior edit with dialogue"
        ],
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
