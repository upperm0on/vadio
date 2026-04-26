import json
import os
import subprocess
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.environ.get("VOID_CONFIG_FILE", os.path.join(BASE_DIR, "void_config.json"))
SCRAPER_SCRIPT = os.path.join(BASE_DIR, "scraper.py")


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def run_scrape_pipeline(target_query: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    command = ["python3", SCRAPER_SCRIPT, target_query, "--out", output_dir]
    print(f"[Daemon] Pulling direct source: {target_query}")
    subprocess.run(command, check=True)

    latest_files = sorted(
        [os.path.join(output_dir, name) for name in os.listdir(output_dir)],
        key=os.path.getmtime,
        reverse=True,
    )
    if not latest_files:
        raise RuntimeError("Scraper completed without producing output.")
    return latest_files[0]


def run_daemon():
    print("[*] Void Autonomous Daemon Initialized.")
    while True:
        try:
            config = load_config()
            if not config.get("AUTONOMY_MODE", False):
                print("[*] Autonomy mode is OFF. Sleeping.")
                time.sleep(10)
                continue

            output_dir = config.get("OUTPUT_DIR", os.path.join(BASE_DIR, "web_app", "generated_edits"))
            target_dorks = config.get("TARGET_DORKS") or []
            cycle_sleep = int(config.get("AUTONOMY_INTERVAL_SECONDS", 30))

            if not target_dorks:
                print("[-] No TARGET_DORKS configured. Sleeping.")
                time.sleep(cycle_sleep)
                continue

            print("[*] Autonomy mode is ON. Executing direct-source pull pipeline...")
            for target_query in target_dorks:
                try:
                    artifact_path = run_scrape_pipeline(target_query, output_dir)
                    print(f"[+] Pull complete for '{target_query}'. Output: {artifact_path}")
                except subprocess.CalledProcessError as e:
                    print(f"[-] Pull failed for '{target_query}' with exit code {e.returncode}")
                except Exception as e:
                    print(f"[-] Pull failed for '{target_query}': {e}")

            time.sleep(cycle_sleep)

        except Exception as e:
            print(f"[-] Daemon error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    run_daemon()
