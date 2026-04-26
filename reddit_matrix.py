import json
import os
import re
import urllib.error
import urllib.request

import redis

USER_AGENT = "void-matrix/2.0"
REDDIT_FEEDS = {
    "animeedits": "https://www.reddit.com/r/animeedits/hot.json?limit=60",
    "GymMotivation": "https://www.reddit.com/r/GymMotivation/hot.json?limit=60",
}

VIBE_KEYS = {
    "God Complex": "vibe:god_complex",
    "Spite": "vibe:spite",
    "Discipline": "vibe:discipline",
}

CATEGORY_RULES = {
    "God Complex": [
        "god", "sigma", "alpha", "aura", "king", "monster", "domination", "supreme", "overlord",
        "invincible", "awakened", "conquer",
    ],
    "Spite": [
        "revenge", "spite", "hate", "prove", "doubt", "enemy", "rage", "anger", "wrong",
        "betray", "pain", "humiliate",
    ],
    "Discipline": [
        "discipline", "routine", "consistency", "focus", "grind", "no excuses", "stoic", "hard work",
        "dedication", "habit", "self control", "lock in",
    ],
}


def redis_client_from_env():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return redis.Redis.from_url(redis_url, decode_responses=True)


def fetch_titles(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))

    children = payload.get("data", {}).get("children", [])
    return [item.get("data", {}).get("title", "").strip() for item in children if item.get("data", {}).get("title")]


def normalize(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def classify_title(title):
    lowered = normalize(title)
    for vibe, keywords in CATEGORY_RULES.items():
        if any(keyword in lowered for keyword in keywords):
            return vibe
    return "Discipline"


def seed_query_from_title(title):
    cleaned = normalize(title)
    cleaned = re.sub(r"[^a-z0-9\s'-]", "", cleaned).strip()
    return cleaned[:120]


def write_to_redis(client, titles):
    inserted = {"God Complex": 0, "Spite": 0, "Discipline": 0}

    for raw_title in titles:
        vibe = classify_title(raw_title)
        query = seed_query_from_title(raw_title)
        if not query:
            continue

        key = VIBE_KEYS[vibe]
        inserted[vibe] += client.sadd(key, query)

    return inserted


def main():
    client = redis_client_from_env()
    client.ping()

    collected = []
    errors = []

    for name, url in REDDIT_FEEDS.items():
        try:
            titles = fetch_titles(url)
            collected.extend(titles)
            print(f"[*] r/{name}: collected {len(titles)} titles")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append(f"r/{name}: {exc}")

    if not collected:
        raise RuntimeError("No Reddit titles collected. Nothing to seed into Redis.")

    inserted = write_to_redis(client, collected)
    for vibe, count in inserted.items():
        key = VIBE_KEYS[vibe]
        total = client.scard(key)
        print(f"[+] {vibe} -> {key} added={count} total={total}")

    if errors:
        print("[!] Partial fetch errors:")
        for err in errors:
            print(f"    - {err}")


if __name__ == "__main__":
    main()
