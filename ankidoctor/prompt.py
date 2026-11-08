"""Prompt builders and defensive JSON parsing for the local model."""

import json
import re

SYSTEM_PROMPT = (
    "You are a Japanese language tutor. You produce concise, natural example "
    "sentences and translations. Always respond with valid JSON only and no prose."
)


def make_card_prompt(word, fields):
    names = ", ".join(f'"{f}"' for f in fields)
    return (
        f"For the Japanese word or phrase: {word!r}\n"
        f"Return a JSON object with exactly these keys: {names}\n"
        "Rules:\n"
        '- "Japanese": the word itself\n'
        '- "Reading": hiragana reading of the word\n'
        '- "Meaning": concise English definition\n'
        '- "Sentence": a natural example sentence using the word\n'
        '- "SentenceMeaning": English translation of Sentence\n'
        '- "Note": optional usage note or empty string\n'
        '- "Link": empty string\n'
    )


def suggest_fill_prompt(field, values):
    filled = {k: v for k, v in values.items() if v}
    ctx = "\n".join(f"{k}: {v}" for k, v in filled.items())
    return (
        f"Fill the missing field for this Japanese Anki note.\n"
        f"Existing fields:\n{ctx}\n\n"
        f'Missing field to fill: "{field}"\n'
        f'Return JSON only: {{"{field}": "..."}}\n'
    )


def parse_json(text):
    """Best-effort extraction of a JSON object from model output."""
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None
