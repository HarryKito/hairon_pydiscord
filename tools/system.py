import subprocess
import sys

# Update the yt-dlp
def update_yt_dlp():
    try:
        print("[Update] yt-dlp Version check...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], check=True)
        print("Yt-dlp update Success.")
    except Exception as e:
        print(f"Update failed : {e}")

update_yt_dlp()