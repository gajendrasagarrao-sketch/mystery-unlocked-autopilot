
import os
import json
import random
import subprocess
import requests
from pathlib import Path

OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)

VIDEO_FILE = OUTPUT / "mystery-unlocked.mp4"
AUDIO_FILE = OUTPUT / "narration.wav"
SCRIPT_FILE = OUTPUT / "script.json"
CLIPS_DIR = OUTPUT / "clips"

PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

if not PIXABAY_API_KEY:
    raise RuntimeError("PIXABAY_API_KEY is missing")

def run_command(command):
    subprocess.run(command, check=True)

def get_search_terms(data):
    category = data.get("category", "").lower()

    if "science" in category:
        return ["space science", "galaxy", "universe"]
    if "children" in category:
        return ["cartoon nature", "cute animals", "fairytale"]
    if "devotional" in category:
        return ["Indian temple", "Indian nature", "ancient India"]
    if "horror" in category:
        return ["dark forest", "foggy mansion", "abandoned house"]
    if "fiction" in category:
        return ["fantasy castle", "magical forest", "fantasy world"]

    return ["mystery", "ancient ruins", "dark forest"]

def download_clips(data):
    print("Searching for video footage...")

    CLIPS_DIR.mkdir(exist_ok=True)

    terms = get_search_terms(data)
    downloaded = []

    for term in terms:
        url = "https://pixabay.com/api/videos/"

        response = requests.get(
            url,
            params={
                "key": PIXABAY_API_KEY,
                "q": term,
                "per_page": 10,
                "safesearch": "true"
            },
            timeout=30
        )

        response.raise_for_status()
        videos = response.json().get("hits", [])

        if not videos:
            continue

        random.shuffle(videos)

        for video in videos[:2]:
            variants = video.get("videos", {})
            file_info = (
                variants.get("medium")
                or variants.get("small")
                or variants.get("large")
            )

            if not file_info:
                continue

            filename = CLIPS_DIR / f"clip_{len(downloaded)}.mp4"

            clip_response = requests.get(
                file_info["url"],
                timeout=90
            )
            clip_response.raise_for_status()

            filename.write_bytes(clip_response.content)
            downloaded.append(filename)

    if not downloaded:
        raise RuntimeError("No Pixabay footage could be downloaded")

    return downloaded

def create_video(clips):
    print("Creating final video...")

    if not AUDIO_FILE.exists():
        raise FileNotFoundError("Narration audio is missing")

    normalized = []

    for index, clip in enumerate(clips):
        output_clip = CLIPS_DIR / f"normalized_{index}.mp4"

        run_command([
            "ffmpeg", "-y",
            "-i", str(clip),
            "-vf",
            "scale=1280:720:force_original_aspect_ratio=increase,"
            "crop=1280:720,fps=25,format=yuv420p",
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            str(output_clip)
        ])

        normalized.append(output_clip)

    list_file = CLIPS_DIR / "list.txt"

    with open(list_file, "w", encoding="utf-8") as file:
        for clip in normalized:
            file.write(f"file '{clip.resolve()}'\n")

    silent_video = CLIPS_DIR / "silent.mp4"

    run_command([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(silent_video)
    ])

    run_command([
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(silent_video),
        "-i", str(AUDIO_FILE),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(VIDEO_FILE)
    ])

    print("Video created:", VIDEO_FILE)

def main():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    clips = download_clips(data)
    create_video(clips)

if __name__ == "__main__":
    main()
