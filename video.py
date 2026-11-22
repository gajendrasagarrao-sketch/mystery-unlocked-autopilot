
import os
import json
import subprocess
import requests
from pathlib import Path

PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")

if not PIXABAY_API_KEY:
    raise RuntimeError("PIXABAY_API_KEY is missing")

OUTPUT = Path("output")
VIDEO_DIR = OUTPUT / "clips"

OUTPUT.mkdir(exist_ok=True)
VIDEO_DIR.mkdir(exist_ok=True)

NARRATION = OUTPUT / "narration.wav"
FINAL_VIDEO = OUTPUT / "mystery-unlocked.mp4"


def run(command):
    subprocess.run(command, check=True)


def get_video_duration():
    result = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(NARRATION)
    ])
    return float(result.decode().strip())


def download_clips():
    print("Searching Pixabay for space footage...")

    response = requests.get(
        "https://pixabay.com/api/videos/",
        params={
            "key": PIXABAY_API_KEY,
            "q": "space galaxy stars nebula",
            "per_page": 12,
            "safesearch": "true"
        },
        timeout=30
    )
    response.raise_for_status()

    videos = response.json().get("hits", [])

    if not videos:
        raise RuntimeError("No Pixabay videos found")

    downloaded = []

    for index, video in enumerate(videos[:10]):
        video_url = (
            video.get("videos", {}).get("medium", {}).get("url")
            or video.get("videos", {}).get("small", {}).get("url")
        )

        if not video_url:
            continue

        source = VIDEO_DIR / f"source_{index}.mp4"

        print(f"Downloading clip {index + 1}...")

        result = requests.get(video_url, timeout=60)
        result.raise_for_status()
        source.write_bytes(result.content)

        downloaded.append(source)

    if not downloaded:
        raise RuntimeError("Could not download any video clips")

    return downloaded


def prepare_clips(downloaded):
    prepared = []

    for index, source in enumerate(downloaded):
        destination = VIDEO_DIR / f"clip_{index}.mp4"

        print(f"Preparing clip {index + 1}...")

        run([
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", str(source),
            "-t", "15",
            "-vf",
            "scale=1280:720:force_original_aspect_ratio=increase,"
            "crop=1280:720,fps=30",
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            str(destination)
        ])

        prepared.append(destination)

    return prepared


def create_video(clips):
    print("Combining footage and narration...")

    duration = get_video_duration()
    repetitions = int(duration / (len(clips) * 15)) + 2

    playlist = OUTPUT / "clips.txt"

    with open(playlist, "w", encoding="utf-8") as file:
        for _ in range(repetitions):
            for clip in clips:
                file.write(f"file '{clip.resolve()}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(playlist),
        "-i", str(NARRATION),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-movflags", "+faststart",
        str(FINAL_VIDEO)
    ])

    print("Video created successfully!")


def main():
    if not NARRATION.exists():
        raise RuntimeError("narration.wav is missing from output folder")

    downloaded = download_clips()
    clips = prepare_clips(downloaded)
    create_video(clips)

    print("Final video:", FINAL_VIDEO)


if __name__ == "__main__":
    main()
