
import os
import json
import base64
import time
from datetime import date
from pathlib import Path
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY")
LANGUAGE = os.environ.get("VIDEO_LANGUAGE", "English").strip().lower()

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing")

if LANGUAGE not in ("english", "hindi"):
    raise RuntimeError("VIDEO_LANGUAGE must be English or Hindi")

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

TODAY_CATEGORY = CATEGORIES[
    date.today().toordinal() % len(CATEGORIES)
]

def generate_script():
    print(f"Generating {LANGUAGE} documentary...")
    print(f"Category: {TODAY_CATEGORY}")

    if LANGUAGE == "hindi":
        language_instruction = """
Write the entire narration in natural, fluent Hindi
using Devanagari script.
Use simple Indian Hindi suitable for listening.
Keep the title and description in Hindi.
"""
    else:
        language_instruction = """
Write the entire narration in clear, natural English.
Keep the title and description in English.
"""

    prompt = f"""
You are the documentary storyteller for Mystery Unlocked.

Create an original video in the category:
{TODAY_CATEGORY}

Choose a fresh and interesting topic within this category.

{language_instruction}

Requirements:
- Write between 650 and 850 words for English narration.
- Write between 600 and 750 words for Hindi narration.
- Aim for approximately 5 to 6 minutes of spoken narration.
- Strong opening hook.
- Engaging storytelling.
- No invented facts presented as real.
- Science must be scientifically responsible.
- Fiction must be clearly fictional.
- Horror must avoid graphic violence.
- Children's stories must be gentle, safe and age-appropriate.
- Devotional stories must be respectful.
- Do not invent religious quotations or claim uncertain traditions are facts.

Return valid JSON with exactly these fields:
title, description, tags, narration, category, made_for_kids.

Set made_for_kids to true only for children's bedtime
and moral stories. Otherwise set it to false.
Set tags as a JSON array of strings.
"""

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

            data = json.loads(response_text)

            required = [
                "title",
                "description",
                "tags",
                "narration",
                "category",
                "made_for_kids"
            ]

            for field in required:
                if field not in data:
                    raise ValueError(f"Missing field: {field}")

            data["language"] = LANGUAGE

            with open(
                OUTPUT / "script.json",
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    data,
                    file,
                    indent=2,
                    ensure_ascii=False
                )

            print("Script generated successfully.")
            return data

        except Exception as error:
            print(f"Attempt {attempt + 1} failed: {error}")

            if attempt == 4:
                raise

            time.sleep(15 * (attempt + 1))

def generate_voice(narration):
    print(f"Generating {LANGUAGE} narration...")

    interaction = client.interactions.create(
        model="gemini-3.8-flash-tts",
        input=[{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": narration,
                "annotations": [{
                    "type": "speech_metadata",
                    "style": (
                        "Deep, calm, engaging male documentary narration"
                    )
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

    with open(OUTPUT / "narration.wav", "wb") as file:
        file.write(base64.b64decode(audio.data))

    print("Narration generated successfully.")

def main():
    data = generate_script()
    generate_voice(data["narration"])
    print("Content generation completed successfully.")

if __name__ == "__main__":
    main()
