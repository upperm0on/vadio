import asyncio
from void_daemon import discover_metadata

async def test_search():
    q = "2026 sukuna stand proud english dub edit"
    print(f"[*] Testing search for: {q}")
    res = await discover_metadata(q)
    print(f"[*] Result: {res}")

if __name__ == "__main__":
    asyncio.run(test_search())
