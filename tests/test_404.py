import requests
import urllib.parse

def test_radio_files():
    base_url = "http://localhost:8090"
    
    # Test cases reported by user
    test_paths = [
        "/radio/cinematic_aura/4w9T5Ob7X-A__Treachery%20-%20Sosuke%20Aizens%20Theme%20Slowed%20to%20PERFECTI.mp3",
        "/radio/mental_agony/soyriYH5l9w__kaguya%20edit%20%20love%20me%20like%20a%20friend.mp3",
        "/radio/true_warrior/socUqHpFm1Q__I%20have%20no%20enemies%20Dont%20be%20your%20own%20enemy%20Forgive%20y.mp3"
    ]
    
    for path in test_paths:
        full_url = f"{base_url}{path}"
        print(f"[*] Testing: {full_url}")
        resp = requests.get(full_url)
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ERROR: Could not fetch {path}")
            # Try to see if unquoted path exists in local fs (manual check in script)
            import os
            from pathlib import Path
            local_base = Path("/home/barimah/.gemini/antigravity/scratch/vadio/web_app/radio")
            rel = urllib.parse.unquote(path.replace("/radio/", ""))
            local_path = local_base / rel
            print(f"    Local Check: {local_path}")
            print(f"    Exists? {local_path.exists()}")
        else:
            print(f"    SUCCESS: {len(resp.content)} bytes received")
        print("-" * 20)

if __name__ == "__main__":
    test_radio_files()
