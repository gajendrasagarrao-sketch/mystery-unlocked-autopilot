
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

# Primary and backup script-generation models
SCRIPT_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash"
]

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


def is_temporary_error(error):
    message = str(error).upper()

    return any(code in message for code in [
        "503",
        "UNAVAILABLE",
        "500",
        "502",
        "504",
        "INTERNAL SERVER ERROR"
    ])


def generate_script_text(prompt):
    for model in SCRIPT_MODELS:
        print(f"Trying script model: {model}")

        for attempt in range(3):
            try:
                print(
                    f"Attempt {attempt + 1} of 3 "
                    f"using {model}..."
                )

                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json"
                    }
                )

                if not response.text:
                    raise ValueError("Gemini returned an empty response")

                print(f"Script generated using {model}")
                return response.text

            except Exception as error:
                print(f"Attempt failed: {error}")

                if not is_temporary_error(error):
                    raise

                if attempt < 2:
                    wait = [30, 60][attempt]
                    print(f"Waiting {wait} seconds...")
                    time.sleep(wait)
                else:
                    print(
                        f"{model} unavailable. "
                        "Switching to backup model..."
                    )

    raise RuntimeError(
        "Both Gemini models failed. "
        "Please try again later."
    )


def generate_script():
    print(f"Generating {LANGUAGE} documentary...")
    print(f"Category: {TODAY_CATEGORY}")

    if LANGUAGE == "hindi":
        language_instruction = """
Write the entire narration in natural, fluent Hindi
using Devanagari script.
Use simple Indian Hindi suitable for listening.
Keep the title and description in Hindi.
Write approximately 600 to 750 Hindi words.
"""
        minimum_words = 600
        maximum_words = 750

    else:
        language_instruction = """
Write the entire narration in clear, natural English.
Keep the title and description in English.
Write approximately 650 to 850 English words.
"""
        minimum_words = 650
        maximum_words = 850

    prompt = f"""
You are the documentary storyteller for Mystery Unlocked.

Create an original video in this category:
{TODAY_CATEGORY}

Choose a fresh and interesting topic.

{language_instruction}

Requirements:
- Aim for approximately 5 to 6 minutes of narration.
- Start with a powerful opening hook.
- Keep the storytelling engaging.
- Include a satisfying conclusion.
- Do not present invented facts as real.
- Science must be scientifically responsible.
- Fiction must be clearly fictional.
- Horror must avoid graphic violence.
- Children's stories must be gentle and age-appropriate.
- Devotional stories must be respectful.
- Avoid unnecessary repetition.
- Do not make the narration too short.

Return valid JSON with exactly these fields:
title, description, tags, narration, category, made_for_kids.

Set made_for_kids to true only for children's bedtime
and moral stories. Otherwise set it to false.

Set tags as a JSON array of strings.
"""

    response_text = generate_script_text(prompt)

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

    narration = data["narration"]

    if not isinstance(narration, str) or not narration.strip():
        raise ValueError("Narration is empty or invalid")

    word_count = len(narration.split())

    print(f"Narration word count: {word_count}")

    if not minimum_words <= word_count <= maximum_words:
        raise ValueError(
            f"Expected {minimum_words}-{maximum_words} words, "
            f"but received {word_count}."
        )

    if not isinstance(data["tags"], list):
        raise ValueError("Tags must be a JSON array")

    data["language"] = LANGUAGE
    data["category"] = TODAY_CATEGORY

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
                        "Deep, calm, engaging male "
                        "documentary narration"
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
