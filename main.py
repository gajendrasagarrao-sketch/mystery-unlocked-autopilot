
import os
import json
import base64
import time
from datetime import date
from pathlib import Path
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing")

client = genai.Client(
    api_key=API_KEY,
    http_options={"api_version": "v1beta"}
)

OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)

CATEGORIES = [
    "Mysteries and unexplained events",
    "Science and amazing facts",
    "Fiction and fantasy stories",
    "Horror stories",
    "Children's bedtime and moral stories",
    "Devotional and Indian mythology stories"
]

TODAY_CATEGORY = CATEGORIES[date.today().toordinal() % len(CATEGORIES)]

TOPIC = f"Create an engaging original video about: {TODAY_CATEGORY}. Choose a fresh and interesting topic within this category."

def generate_script():
    print("Generating documentary script...")

    prompt = f"""
Create an engaging English documentary for Mystery Unlocked.

Topic: {TOPIC}

Requirements:
- Approximately 5 minutes of narration.
- Strong opening hook.
- Scientifically responsible explanations.
- No invented facts or quotations.
- Easy-to-understand English.
- Engaging conclusion.

Return JSON with these fields:
title, description, tags and narration.
"""

    response_text = ""

    for attempt in range(5):
        try:
            print(f"Gemini attempt {attempt + 1} of 5...")

            response_text = ""

            for chunk in client.models.generate_content_stream(
                model="gemini-3.1-flash-lite",
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                }
            ):
                if chunk.text:
                    response_text += chunk.text

            if not response_text.strip():
                raise RuntimeError("Gemini returned an empty response")

            data = json.loads(response_text)

            required_fields = [
                "title",
                "description",
                "tags",
                "narration"
            ]

            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing JSON field: {field}")

            with open(
                OUTPUT / "script.json",
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print("Script generated successfully.")
            return data

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")

            if attempt == 4:
                raise

            wait_time = 15 * (attempt + 1)
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)


def generate_voice(narration):
    print("Generating documentary voice...")

    interaction = client.interactions.create(
        model="gemini-3.8-flash-tts",
        input=[{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": narration,
                "annotations": [{
                    "type": "speech_metadata",
                    "style": "Deep, calm, engaging male documentary narration"
                }]
            }]
        }],
        response_format={"type": "audio"},
        generation_config={
            "speech_config": [
                {"voice": "Charon"}
            ]
        }
    )

    audio = interaction.output_audio

    if not audio or not audio.data:
        raise RuntimeError("No audio was generated")

    with open(OUTPUT / "narration.wav", "wb") as f:
        f.write(base64.b64decode(audio.data))

    print("Narration generated successfully.")


def main():
    data = generate_script()
    generate_voice(data["narration"])

    print("Content generation completed successfully.")


if __name__ == "__main__":
    main()
