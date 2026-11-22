
import os
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

OUTPUT = Path("output")
VIDEO_FILE = OUTPUT / "mystery-unlocked.mp4"
SCRIPT_FILE = OUTPUT / "script.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]

def upload_video():
    print("Preparing YouTube upload...")

    if not VIDEO_FILE.exists():
        raise FileNotFoundError("Video file not found")

    with open(SCRIPT_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    credentials = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        scopes=SCOPES
    )

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    language = data.get("language", "english").lower()

    title = data["title"][:100]

    description = (
        data["description"]
        + "\n\n"
        + "Mystery Unlocked | "
        + language.upper()
        + "\n"
        + "Subscribe for more stories, mysteries and discoveries."
    )

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": data.get("tags", []),
            "categoryId": "24"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": bool(
                data.get("made_for_kids", False)
            )
        }
    }

    media = MediaFileUpload(
        str(VIDEO_FILE),
        mimetype="video/mp4",
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = request.execute()

    print("Upload completed successfully!")
    print("Language:", language)
    print("YouTube video ID:", response["id"])
    print(
        "Video link:",
        "https://www.youtube.com/watch?v=" + response["id"]
    )

if __name__ == "__main__":
    upload_video()
