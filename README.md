# anki-doctor

Generate Anki cards with a local LLM, and find/fill missing note fields — all running locally.

## What it does

1. **`make`** — give it a Japanese word or phrase; a local model (Ollama) writes the
   reading, meaning, and an example sentence + translation, then adds a card to Anki.
2. **`check`** — scans your Anki collection for notes with empty fields ("missing
   columns") and, optionally, asks the model to suggest what belongs there and writes
   it back.

## Prerequisites

- Anki desktop running, with the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on installed
  (Tools → Add-ons → Get Add-ons → code `2055492159`).
- [Ollama](https://ollama.com) running with a model pulled, e.g. `ollama pull llama3.2:3b`.

## Usage

```sh
# create a card for 勉強
python -m ankidoctor make 勉強

# target a specific deck / note type / model
python -m ankidoctor make 勉強 --deck "Japanese" --notetype "Basic+" --model qwen2.5:7b

# list notes with empty fields
python -m ankidoctor check

# AI proposes fills for each missing field
python -m ankidoctor check --suggest

# ...and writes them back into Anki
python -m ankidoctor check --apply
```

## Project layout

```
ankidoctor/
  __main__.py   CLI entry point (make / check)
  ollama.py     local LLM client (Ollama HTTP API)
  anki.py       AnkiConnect client + read-only SQLite scanner
  prompt.py     prompt builders + JSON parsing
docs/DESIGN.md  architecture and design notes
```

See `docs/DESIGN.md` for details.
