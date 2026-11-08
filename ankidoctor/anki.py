"""Anki integration: AnkiConnect for writes, read-only SQLite for scanning."""

import json
import sqlite3
import urllib.error
import urllib.request

ANCICONNECT_HOST = "http://127.0.0.1:8765"

FIELD_SEP = "\x1f"


class AnkiConnectError(RuntimeError):
    pass


def _request(action, **params):
    payload = json.dumps(
        {"action": action, "version": 6, "params": params}
    ).encode("utf-8")
    req = urllib.request.Request(
        ANCICONNECT_HOST, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise AnkiConnectError(
            f"could not reach AnkiConnect at {ANCICONNECT_HOST} "
            f"— is Anki running with AnkiConnect installed? ({exc})"
        ) from exc
    if data.get("error"):
        raise AnkiConnectError(data["error"])
    return data.get("result")


def add_note(model_name, fields, deck="Default", tags=None):
    return _request(
        "addNote",
        note={
            "deckName": deck,
            "modelName": model_name,
            "fields": fields,
            "tags": tags or [],
        },
    )


def update_note_fields(note_id, fields):
    return _request(
        "updateNoteFields", note={"id": note_id, "fields": fields}
    )


def get_field_names(model_name):
    return _request("modelFieldNames", modelName=model_name)


def _open_readonly(path):
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def scan_notes(path, notetype=None, limit=None):
    """Return notes with at least one empty field.

    Each result is a dict with: id, note_type, fields (name -> value),
    and missing (list of empty field names). `notetype` may be a name or id.
    """
    con = _open_readonly(path)
    cur = con.cursor()

    cur.execute("SELECT id, name FROM notetypes")
    nt_rows = cur.fetchall()
    nt_names = {r[0]: r[1] for r in nt_rows}
    nt_ids = {r[1]: r[0] for r in nt_rows}

    cur.execute("SELECT ntid, name FROM fields ORDER BY ntid, ord")
    field_names_by_nt = {}
    for ntid, name in cur.fetchall():
        field_names_by_nt.setdefault(ntid, []).append(name)

    query = "SELECT id, mid, flds FROM notes"
    params = []
    if notetype is not None:
        ntid = nt_ids.get(notetype)
        if ntid is None:
            try:
                ntid = int(notetype)
            except ValueError:
                con.close()
                raise ValueError(f"unknown note type: {notetype!r}")
        query += " WHERE mid = ?"
        params.append(ntid)
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    cur.execute(query, params)
    results = []
    for nid, mid, flds_str in cur.fetchall():
        names = field_names_by_nt.get(mid, [])
        values = flds_str.split(FIELD_SEP)
        fields = {}
        for i, name in enumerate(names):
            fields[name] = values[i] if i < len(values) else ""
        missing = [name for name, val in fields.items() if not val.strip()]
        if missing:
            results.append(
                {
                    "id": nid,
                    "note_type": nt_names.get(mid, str(mid)),
                    "fields": fields,
                    "missing": missing,
                }
            )
    con.close()
    return results
