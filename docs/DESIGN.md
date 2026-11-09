# anki-doctor — Design

## Overview

`anki-doctor` is a local command-line tool with two jobs:

1. **Make a card** — turn a Japanese word/phrase into a complete Anki note using a
   local LLM (sentence + translation + reading).
2. **Find missing columns** — scan the user's Anki collection for notes that have
   empty fields, and (optionally) use the LLM to propose and write fills.

It runs entirely on the user's machine: the LLM is served by [Ollama](https://ollama.com)
and cards are written through [AnkiConnect](https://ankiweb.net/shared/info/2055492159).

## Goals / non-goals

**Goals**

- Zero cloud dependency; no API keys.
- No changes to the user's Anki schema. Writes go through AnkiConnect so Anki owns
  all invariants (checksums, card rows, sync state).
- Minimal dependencies: Python stdlib only (`sqlite3`, `urllib`, `json`, `argparse`).

**Non-goals**

- A GUI or web UI (for now).
- Writing directly to `collection.anki2` (rejected due to schema-version mismatch
  between the PyPI `anki` package and the installed desktop app, plus corruption risk).
- Multi-note-type "make" auto-detection (the user targets a note type explicitly).

## Architecture

```
┌─────────────┐     HTTP      ┌──────────────┐
│   CLI       │──────────────▶│   Ollama     │  (127.0.0.1:11434)
│ __main__.py │               │  llama3.2:3b │
└──────┬──────┘               └──────────────┘
       │
       │  SQLite (read-only)     ┌────────────────────────┐
       ├────────────────────────▶│ collection.anki2       │  scanning only
       │                         └────────────────────────┘
       │  HTTP                   ┌────────────────────────┐
       └────────────────────────▶│ AnkiConnect (Anki app) │  (127.0.0.1:8765)
                                 └────────────────────────┘
```

### Modules

- `ankidoctor/__main__.py` — argparse CLI, wires the subcommands together.
- `ankidoctor/ollama.py` — thin wrapper over Ollama's `/api/chat`, `format=json`.
- `ankidoctor/anki.py` — two concerns:
  - AnkiConnect client (`addNote`, `updateNoteFields`, `modelFieldNames`).
  - Read-only SQLite scanner (`scan_notes`) that reports empty fields.
- `ankidoctor/prompt.py` — prompt builders + defensive JSON extraction.

## Anki data model notes

These are the facts the scanner relies on (schema version 18, Anki 25.x):

- `notes` — one row per note. `mid` is the note type id; `flds` is all field values
  joined by `\x1f` (0x1f, unit separator); `sfld`/`csum` are derived from the first field.
- `notetypes` — `id`, `name`, `config` (JSON, but stored compressed in newer Anki).
- `fields` — `ntid`, `ord`, `name` (the "columns" of a note type).
- `cards` — generated from the note type's templates; we never create these directly.

Because `notetypes.config` is stored compressed, the scanner reads field names from the
dedicated `fields` table instead of parsing `config`.

## Commands

### `make <word>`

1. `get_field_names` (AnkiConnect) fetches the target note type's fields.
2. `make_card_prompt` asks the model for a JSON object keyed by those fields.
3. `parse_json` extracts the object (tolerates markdown fences / stray prose).
4. `add_note` inserts the note into the target deck.
5. With `--dry-run`, prints the prepared fields and deck without writing anything.

### `check [--suggest] [--apply]`

1. `scan_notes` opens the collection read-only (`mode=ro`) and yields notes with at
   least one empty field, grouped info per note type.
2. Without flags: just report. With `--suggest`: for each missing field, send the note's
   populated fields + the empty field name to the model and print the proposed fill.
3. With `--apply`: after suggesting, `update_note_fields` writes fills back via
   AnkiConnect (so Anki recomputes `sfld`/`csum` and updates sync state safely).

## Prompting strategy

- Single shared `SYSTEM_PROMPT` forces a strict JSON-only response, and requests are sent
  with Ollama's `format=json` so the model is steered toward valid JSON.
- `make` asks for all fields at once (the model fills the ones it can).
- `suggest_fill` asks for exactly one missing field, conditioned on the note's existing
  content — this keeps context small and relevance high.
- `parse_json` is defensive: strips code fences, falls back to the first `{...}`/`[...]`
  block, and finally to the raw string so the CLI never crashes on a malformed reply.

## Safety & failure modes

| Failure                      | Handling                                                              |
| ---------------------------- | --------------------------------------------------------------------- |
| Ollama not running           | `OllamaError` with a clear message                                    |
| Anki/AnkiConnect not running | `AnkiConnectError` with a clear message                               |
| Model returns non-JSON       | `parse_json` fallback; `make` exits non-zero, `check` prints raw text |
| Unknown note type            | `scan_notes` raises `ValueError`                                      |
| Collection schema mismatch   | scanner is read-only; writes are always via AnkiConnect               |

## Future work

- `--model` flag already exists; swap `llama3.2:3b` for `qwen2.5:7b` (better Japanese).
- Batch `check --suggest` requests or dedupe identical missing-field contexts.
- Config file (`~/.config/anki-doctor.toml`) for deck, note type, and model defaults.
