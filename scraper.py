import argparse
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YTDLP_PATH = os.environ.get("VOID_YTDLP_PATH", os.path.join(BASE_DIR, "tools", "yt-dlp"))


def scrape_quote(query, output_dir):
    print("[*] Initializing Void Scraper...")
    print(f"[*] Target: '{query}'")

    os.makedirs(output_dir, exist_ok=True)

    if not os.path.isfile(YTDLP_PATH):
        raise FileNotFoundError(f"yt-dlp binary not found at: {YTDLP_PATH}")

    command = [
        YTDLP_PATH,
        f"ytsearch1:{query}",
        "-f",
        "bestaudio/best",
        "-o",
        f"{output_dir}/%(title)s.%(ext)s",
        "--quiet",
        "--no-warnings",
        "--restrict-filenames",
    ]

    print("[*] Pulling direct media stream (no local mix)...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        if result.stdout.strip():
            print(result.stdout.strip())
        print(f"[+] Success. Media secured in {output_dir}/")
        return True
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        stdout = (e.stdout or "").strip()
        print("[-] Failed to pull media stream.")
        if stdout:
            print(f"[yt-dlp stdout] {stdout}")
        if stderr:
            print(f"[yt-dlp stderr] {stderr}")
        return False
    except Exception as e:
        print(f"[-] Unexpected scraper failure: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Void Engine - Direct Media Scraper")
    parser.add_argument("query", help="Search query or URL")
    parser.add_argument("--out", default="./web_app/raw_audio", help="Output directory")
    args = parser.parse_args()

    success = scrape_quote(args.query, args.out)
    if not success:
        sys.exit(1)
