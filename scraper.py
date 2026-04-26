import os
import subprocess
import argparse
import sys

def scrape_quote(query, output_dir):
    print(f"[*] Initializing Void Scraper...")
    print(f"[*] Target: '{query}'")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # We use yt-dlp to search YouTube/TikTok and rip the highest quality audio directly
    # Format: download best audio, convert to wav for the Void Engine
    command = [
        "yt-dlp",
        f"ytsearch1:{query}", # Grab the top result
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "-o", f"{output_dir}/%(title)s.%(ext)s",
        "--quiet",
        "--no-warnings",
        "--restrict-filenames"
    ]

    print("[*] Engaging target and ripping audio stream...")
    try:
        subprocess.run(command, check=True)
        print(f"[+] Success. Raw audio secured in {output_dir}/")
    except subprocess.CalledProcessError:
        print("[-] Failed to rip audio. The target might be restricted or require cookies.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Void Engine - Quote Scraper")
    parser.add_argument("query", help="The anime quote or dork to search for (e.g., 'Erwin Smith charge speech dub')")
    parser.add_argument("--out", default="./web_app/raw_audio", help="Output directory")
    args = parser.parse_args()
    
    scrape_quote(args.query, args.out)
