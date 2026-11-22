
import os
import json
import base64
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

TOPIC = "What happens if you fall into a black hole?"

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

Return JSON with title, description, tags and narration.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )

    data = json.loads(response.text)

    with open(OUTPUT / "script.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Script generated successfully.")
    return data


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
