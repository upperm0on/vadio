import asyncio
from void_daemon import harvest_track, VIBE_TO_DIR

async def seed_god_complex():
    print("[*] Seeding God Complex library...")
    queries = [
        "site:tiktok.com 2026 sukuna stand proud english dub edit",
        "site:instagram.com 2026 david goggins stay driven audio",
        "site:tiktok.com 2026 gilgamesh arrogant king edit audio"
    ]
    for q in queries:
        await harvest_track("God Complex", q)
    print("[*] Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_god_complex())
