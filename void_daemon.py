import asyncio
import hashlib
import os
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent
WEB_APP_DIR = BASE_DIR / "web_app"
RADIO_DIR = WEB_APP_DIR / "radio"
YTDLP_BIN = BASE_DIR / "tools" / "yt-dlp"

SLEEP_BETWEEN_DOWNLOADS_SECONDS = 8
SLEEP_BETWEEN_CYCLES_SECONDS = 45

VIBE_QUERIES: Dict[str, List[str]] = {
    "god_complex": [
        "sukuna domain expansion edit audio",
        "gojo hollow purple phonk edit",
        "madara uchiha war arc edit phonk",
        "aizen beyond bankai edit audio",
        "vegeta ultra ego phonk edit",
    ],
    "spite": [
        "toji fushiguro heavenly restriction phonk",
        "itachi revenge edit audio",
        "eren yeager rumbling phonk",
        "ken kaneki rage edit audio",
        "levi ackerman no mercy edit",
    ],
    "discipline": [
        "miyamoto musashi discipline phonk edit",
        "rock lee training edit phonk",
        "goku gravity chamber motivation edit",
        "ippo makunouchi training montage phonk",
        "thorfinn stoic discipline edit audio",
    ],
}


def ensure_directories() -> None:
    for vibe in VIBE_QUERIES.keys():
        (RADIO_DIR / vibe).mkdir(parents=True, exist_ok=True)


async def run_command(*args: str) -> tuple[int, str, str]:
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return process.returncode, stdout.decode("utf-8", errors="ignore"), stderr.decode("utf-8", errors="ignore")


async def discover_video_id(query: str) -> str | None:
    code, out, err = await run_command(
        str(YTDLP_BIN),
        "--no-warnings",
        "--skip-download",
        "--print",
        "id",
        f"ytsearch1:{query}",
    )
    if code != 0:
        print(f"[-] Failed ID discovery for '{query}': {err.strip()}")
        return None
    video_id = out.strip().splitlines()
    return video_id[0] if video_id else None


def query_fingerprint(query: str) -> str:
    return hashlib.sha1(query.encode("utf-8")).hexdigest()[:10]


def already_downloaded(vibe_dir: Path, video_id: str) -> bool:
    return any(vibe_dir.glob(f"{video_id}__*.mp3"))


async def download_query(vibe: str, query: str) -> None:
    vibe_dir = RADIO_DIR / vibe
    video_id = await discover_video_id(query)
    if not video_id:
        return

    if already_downloaded(vibe_dir, video_id):
        print(f"[=] Skip existing track [{vibe}] '{query}' ({video_id})")
        return

    output_template = str(vibe_dir / f"{video_id}__{query_fingerprint(query)}__%(title).80s.%(ext)s")
    print(f"[+] Harvesting [{vibe}] '{query}' -> {video_id}")

    code, _, err = await run_command(
        str(YTDLP_BIN),
        "--no-warnings",
        "--extract-audio",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",
        "--restrict-filenames",
        "-o",
        output_template,
        f"ytsearch1:{query}",
    )

    if code != 0:
        print(f"[-] Download failed [{vibe}] '{query}': {err.strip()}")
        return

    print(f"[✓] Harvest complete [{vibe}] '{query}'")


async def run_harvester() -> None:
    ensure_directories()
    print("[*] Void Harvester online. Running asynchronous infinite harvest loop.")

    while True:
        for vibe, queries in VIBE_QUERIES.items():
            for query in queries:
                try:
                    await download_query(vibe, query)
                except Exception as exc:  # noqa: BLE001
                    print(f"[-] Unexpected error [{vibe}] '{query}': {exc}")
                await asyncio.sleep(SLEEP_BETWEEN_DOWNLOADS_SECONDS)

        print(f"[*] Harvest cycle complete. Sleeping {SLEEP_BETWEEN_CYCLES_SECONDS}s.")
        await asyncio.sleep(SLEEP_BETWEEN_CYCLES_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(run_harvester())
    except KeyboardInterrupt:
        print("\n[*] Harvester stopped by operator.")
