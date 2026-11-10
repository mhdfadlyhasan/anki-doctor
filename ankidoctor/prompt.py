"""Prompt builders and defensive JSON parsing for the local model."""

import json
import re

SYSTEM_PROMPT = (
    "You are a Japanese language tutor. You produce concise, natural example "
    "sentences and translations. Always respond with valid JSON only and no prose."
)


def describe_field(name):
    """Return a one-line instruction for what belongs in a field."""
    key = re.sub(r"[^a-z0-9]", "", name.lower())
    if "sentencemeaning" in key or "senttrans" in key:
        return "English translation of the example sentence"
    if "sentence" in key or "example" in key:
        return "a natural example sentence using the word"
    if "reading" in key or "kana" in key or "furigana" in key or "よみ" in name:
        return "hiragana reading of the word"
    if any(t in key for t in ("meaning", "definition", "gloss", "english")):
        return "concise English definition"
    if "link" in key or "url" in key:
        return "an empty string"
    if any(t in key for t in ("image", "picture", "audio", "sound", "media")):
        return "an empty string"
    if "note" in key or "usage" in key:
        return "optional usage note, or an empty string"
    if any(
        t in key
        for t in ("japanese", "word", "expression", "vocab", "term", "kanji", "front")
    ):
        return "the word or phrase as written in Japanese"
    return f"appropriate content for the field named {name!r}"


def make_card_prompt(word, fields):
    instructions = "\n".join(
        f'- "{name}": {describe_field(name)}' for name in fields
    )
    return (
        f"For the Japanese word or phrase: {word!r}\n"
        "Return a JSON object with exactly these keys:\n"
        f"{instructions}\n"
        "Respond with valid JSON only and no prose. Use empty strings for "
        "fields that should stay blank.\n"
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
