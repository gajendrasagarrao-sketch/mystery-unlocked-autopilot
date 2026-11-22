
import os
import json
from pathlib import Path
from google import genai
from google.genai import types

# Mystery Unlocked - Main Program

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing")

client = genai.Client(api_key=API_KEY)

OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)

TOPIC = "What happens if you fall into a black hole?"

def generate_script():
    print("Generating documentary script...")

    prompt = f"""
    Create an engaging English documentary for the YouTube
    channel Mystery Unlocked.

    Topic: {TOPIC}

    Requirements:
    - Approximately 5 minutes of narration.
    - Interesting opening hook.
    - Scientifically responsible explanations.
    - No invented facts or fake quotations.
    - Easy-to-understand English.
    - Strong ending.

    Return valid JSON with these fields:
    title, description, tags, narration.
    """

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    data = json.loads(response.text)

    with open(OUTPUT / "script.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Script generated successfully.")
    return data


def generate_voice(narration):
    print("Generating male documentary narration...")

    response = client.models.generate_content(
        model="gemini-3.8-flash-tts",
        contents=narration,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon"
                    )
                )
            )
        )
    )

    audio_parts = [
        part.inline_data.data
        for part in response.parts
        if part.inline_data
    ]

    if not audio_parts:
        raise RuntimeError("Voice generation returned no audio.")

    with open(OUTPUT / "narration.wav", "wb") as f:
        for audio in audio_parts:
            f.write(audio)

    print("Narration generated successfully.")


def main():
    data = generate_script()
    generate_voice(data["narration"])

    print("Mystery Unlocked content generation completed.")
    print("Files saved in the output folder.")


if __name__ == "__main__":
    main()
