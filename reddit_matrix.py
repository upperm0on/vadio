import json
import os
import re
import urllib.error
import urllib.request
from typing import Dict, List, Optional

# Constants
USER_AGENT = "void-matrix/2.0"
REDDIT_FEEDS = {
    "animeedits": "https://www.reddit.com/r/animeedits/hot.json?limit=60",
    "GymMotivation": "https://www.reddit.com/r/GymMotivation/hot.json?limit=60",
}

VIBE_KEYS = {
    "Mental Agony": "vibe:mental_agony",
    "Cinematic Aura": "vibe:cinematic_aura",
    "True Warrior": "vibe:true_warrior",
}

CATEGORY_RULES = {
    "Mental Agony": [
        "love me", "breakdown", "tragedy", "pain", "suffering", "psychological", "madness", "despair",
        "lonely", "heartbreak", "emotional", "trauma", "sad", "depressing", "agony"
    ],
    "Cinematic Aura": [
        "cinematic", "epic", "that one sukuna edit", "domain expansion", "masterpiece", "god", 
        "overwhelming", "aura", "4k", "twixtor", "smooth", "transition", "insane"
    ],
    "True Warrior": [
        "where's your sword", "i have no enemies", "peace", "stoic", "discipline", "vinland saga",
        "thors", "thorfinn", "vagabond", "musashi", "philosophy", "calm", "wisdom"
    ],
}

def normalize(text: str) -> str:
    """Cleans and normalizes text for classification."""
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text.lower()).strip()

def classify_title(title: str) -> str:
    """Classifies a title into a vibe based on keywords."""
    lowered = normalize(title)
    for vibe, keywords in CATEGORY_RULES.items():
        if any(keyword in lowered for keyword in keywords):
            return vibe
    return "True Warrior"  # Default vibe

def seed_query_from_title(title: str) -> str:
    """Converts a raw title into a clean search query."""
    cleaned = normalize(title)
    # Refined for mental/cinematic edits rather than phonk
    if not any(x in cleaned for x in ["edit", "amv"]):
        cleaned += " cinematic edit"
    return cleaned[:120]

def fetch_titles(url: str) -> List[str]:
    """Fetches titles from a Reddit JSON feed."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
        children = payload.get("data", {}).get("children", [])
        return [item.get("data", {}).get("title", "").strip() for item in children if item.get("data", {}).get("title")]
    except Exception as e:
        print(f"[-] Fetch error: {e}")
        return []

class MatrixPersistence:
    """Interface for persisting matrix data. Allows for mocking in tests."""
    def save_query(self, vibe: str, query: str) -> bool:
        raise NotImplementedError

class RedisPersistence(MatrixPersistence):
    def __init__(self, redis_url: Optional[str] = None):
        import redis
        self.client = redis.Redis.from_url(redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        
    def save_query(self, vibe: str, query: str) -> bool:
        key = VIBE_KEYS[vibe]
        return self.client.sadd(key, query) > 0

def process_and_store(titles: List[str], persistence: Optional[MatrixPersistence] = None):
    """Processes titles and optionally stores them."""
    results = {"Mental Agony": 0, "Cinematic Aura": 0, "True Warrior": 0}
    for raw_title in titles:
        vibe = classify_title(raw_title)
        query = seed_query_from_title(raw_title)
        if not query:
            continue
            
        if persistence:
            if persistence.save_query(vibe, query):
                results[vibe] += 1
        else:
            results[vibe] += 1 # Just count for dry run/test
            
    return results

def main():
    print("[*] Void Matrix: Harvesting 2026 Trends...")
    collected = []
    for name, url in REDDIT_FEEDS.items():
        titles = fetch_titles(url)
        collected.extend(titles)
        print(f"[*] r/{name}: collected {len(titles)} titles")

    if not collected:
        print("[!] No titles collected.")
        return

    # Try to use Redis if available, otherwise dry run
    persistence = None
    try:
        persistence = RedisPersistence()
        print("[+] Redis persistence active.")
    except (ImportError, Exception):
        print("[!] Redis not available. Running in DRY RUN mode.")

    inserted = process_and_store(collected, persistence)
    for vibe, count in inserted.items():
        print(f"[+] {vibe}: {count} new queries generated.")

if __name__ == "__main__":
    main()
