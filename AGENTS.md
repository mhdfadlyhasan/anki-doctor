# Agent notes

## Project

`anki-doctor` is a Python stdlib-only CLI (`ankidoctor/`) that generates Anki cards
via a local Ollama model and finds/fills empty fields via AnkiConnect and a read-only
SQLite scan of the collection. See `docs/DESIGN.md` for architecture.

- Run: `python3 -m ankidoctor <command>`
- Build/install: `pip install -e .`
- No test suite yet (prefer stdlib `unittest` if adding one).

## Engineering workflow

This project follows current docs-as-code / design-first practice. Keep explanations
brief but include the reasoning behind workflow decisions.

- `docs/DESIGN.md` is the source of truth. Read it before implementing and update it
  in the same change as any behavior change, so code and design never drift.
- Keep changes small and reviewable; prefer a clear diff over a large rewrite.
- Add or update tests for new behavior when it is practical (no external deps).
- Only commit/branch/push when explicitly asked. When you do, match the existing style.
- Flag design/implementation mismatches instead of silently picking one.
