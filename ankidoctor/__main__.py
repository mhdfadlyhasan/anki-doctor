import argparse
import os
import sys

from . import anki, ollama, prompt

DEFAULT_MODEL = "llama3.2:3b"
DEFAULT_NOTE_TYPE = "jp.takoboto+"


def _default_collection():
    home = os.path.expanduser("~")
    return os.path.join(
        home, "Library", "Application Support", "Anki2", "User 1", "collection.anki2"
    )


def cmd_make(args):
    fields = anki.get_field_names(args.notetype)
    raw = ollama.generate(
        prompt.make_card_prompt(args.word, fields),
        model=args.model,
        system=prompt.SYSTEM_PROMPT,
    )
    data = prompt.parse_json(raw)
    if not isinstance(data, dict):
        print(f"Could not parse model output as JSON:\n{raw}", file=sys.stderr)
        sys.exit(1)

    note_fields = {f: data.get(f, "") for f in fields}
    if args.dry_run:
        print(f"Dry run: would add note to deck '{args.deck}' ({args.notetype})")
        for name, value in note_fields.items():
            print(f"  {name}: {value}")
        if args.tags:
            print(f"  tags: {', '.join(args.tags)}")
        return
    note_id = anki.add_note(args.notetype, note_fields, deck=args.deck, tags=args.tags)
    print(f"Added note {note_id} to deck '{args.deck}'")


def cmd_check(args):
    notes = anki.scan_notes(args.collection, notetype=args.notetype, limit=args.limit)
    if not notes:
        print("No notes with missing fields.")
        return

    print(f"{len(notes)} note(s) with missing fields:\n")
    for n in notes:
        missing = ", ".join(n["missing"])
        print(f"  [{n['id']}] {n['note_type']}: missing {missing}")
        if args.suggest or args.apply:
            fills = {}
            for field in n["missing"]:
                raw = ollama.generate(
                    prompt.suggest_fill_prompt(field, n["fields"]),
                    model=args.model,
                    system=prompt.SYSTEM_PROMPT,
                )
                data = prompt.parse_json(raw)
                val = data.get(field) if isinstance(data, dict) else None
                if val is None:
                    val = raw.strip()
                fills[field] = val
                print(f"      {field}: {val}")
            if args.apply:
                anki.update_note_fields(n["id"], fills)
                print("      -> applied")
    if args.apply:
        print("\nDone.")


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="anki-doctor",
        description="Generate and repair Anki cards with a local LLM.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name")
    sub = parser.add_subparsers(dest="command", required=True)

    make = sub.add_parser("make", help="create a card from a word/phrase")
    make.add_argument("word")
    make.add_argument("--deck", default="Default")
    make.add_argument("--notetype", default=DEFAULT_NOTE_TYPE)
    make.add_argument("--tags", nargs="*", default=[])
    make.add_argument(
        "--dry-run", action="store_true", help="preview the card without writing it"
    )
    make.set_defaults(func=cmd_make)

    check = sub.add_parser("check", help="find notes with empty fields")
    check.add_argument("--collection", default=_default_collection())
    check.add_argument("--notetype", help="limit to a note type (name or id)")
    check.add_argument("--limit", type=int)
    check.add_argument("--suggest", action="store_true", help="AI proposes fills")
    check.add_argument("--apply", action="store_true", help="write suggestions into Anki")
    check.set_defaults(func=cmd_check)

    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
