import json


def clean_json_response(text: str) -> dict:
    text = text.strip()

    if not text:
        raise ValueError("Model returned empty response.")

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model response:\n{text}")

    return json.loads(text[start:end + 1])