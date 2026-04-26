import json
import os
import re
import urllib.error
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MATRIX_PATH = os.path.join(BASE_DIR, "web_app", "matrix.json")
USER_AGENT = "void-matrix/1.0"
REDDIT_FEEDS = {
    "animeedits": "https://www.reddit.com/r/animeedits/hot.json?limit=40",
    "phonk": "https://www.reddit.com/r/phonk/hot.json?limit=40",
    "gymmotivation": "https://www.reddit.com/r/GymMotivation/hot.json?limit=40",
}

DEFAULT_MATRIX = {
    "God Complex": [
        "sigma phonk god complex edit",
        "alpha grindset domination phonk",
        "anime power awakening edit phonk",
    ],
    "Spite": [
        "revenge workout phonk edit",
        "prove them wrong gym motivation",
        "hate fueled training phonk",
    ],
    "Discipline": [
        "discipline over motivation gym edit",
        "cold routine no excuses phonk",
        "focus consistency grindset audio",
    ],
}

CATEGORY_RULES = {
    "God Complex": [
        "god", "sigma", "alpha", "aura", "king", "monster", "domination", "supreme", "overlord",
    ],
    "Spite": [
        "revenge", "spite", "hate", "prove", "doubt", "enemy", "rage", "anger", "wrong",
    ],
    "Discipline": [
        "discipline", "routine", "consistency", "focus", "grind", "no excuses", "stoic", "hard work",
    ],
}


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


def build_matrix(titles):
    matrix = {"God Complex": [], "Spite": [], "Discipline": []}

    for raw_title in titles:
        vibe = classify_title(raw_title)
        cleaned = normalize(raw_title)
        if cleaned:
            matrix[vibe].append(cleaned)

    for vibe, defaults in DEFAULT_MATRIX.items():
        unique = []
        seen = set()
        for item in matrix[vibe] + defaults:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        matrix[vibe] = unique[:50]

    return matrix


def save_matrix(matrix):
    os.makedirs(os.path.dirname(MATRIX_PATH), exist_ok=True)
    with open(MATRIX_PATH, "w", encoding="utf-8") as fp:
        json.dump(matrix, fp, indent=2)
    print(f"[+] Saved matrix to {MATRIX_PATH}")


def main():
    collected = []
    errors = []

    for name, url in REDDIT_FEEDS.items():
        try:
            titles = fetch_titles(url)
            collected.extend(titles)
            print(f"[*] {name}: collected {len(titles)} titles")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append(f"{name}: {exc}")

    if not collected:
        print("[-] Network fetch failed. Writing default matrix fallback.")
        save_matrix(DEFAULT_MATRIX)
        return

    matrix = build_matrix(collected)
    save_matrix(matrix)

    if errors:
        print("[!] Partial fetch errors:")
        for err in errors:
            print(f"    - {err}")


if __name__ == "__main__":
    main()
