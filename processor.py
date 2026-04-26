import os
import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TOOLS_DIR = BASE_DIR / "tools"
FFMPEG_BIN = TOOLS_DIR / "ffmpeg"
RADIO_DIR = BASE_DIR / "web_app" / "radio"

def normalize_audio(file_path: Path):
    """Normalizes audio to -1dB peak using ffmpeg."""
    print(f"[*] Processing: {file_path.name}")
    
    # Temporary file for output
    temp_output = file_path.with_suffix(".tmp.mp3")
    
    # FFmpeg command for normalization
    # loudnorm is better, but simple peak normalization is faster
    command = [
        str(FFMPEG_BIN),
        "-y",
        "-i", str(file_path),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", # EBU R128 standard
        "-ar", "44100",
        "-b:a", "320k",
        str(temp_output)
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True)
        os.replace(temp_output, file_path)
        print(f"[✓] Normalized: {file_path.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] FFmpeg error: {e.stderr.decode()}")
        if temp_output.exists():
            temp_output.unlink()
        return False

def process_all():
    """Finds all MP3s in the radio directory and normalizes them."""
    for vibe_dir in RADIO_DIR.iterdir():
        if vibe_dir.is_dir():
            for mp3 in vibe_dir.glob("*.mp3"):
                # We can use a simple flag file or check metadata to avoid re-processing
                processed_flag = mp3.with_suffix(".processed")
                if not processed_flag.exists():
                    if normalize_audio(mp3):
                        processed_flag.touch()

if __name__ == "__main__":
    process_all()
