"""Minimal client for the local Ollama HTTP API (stdlib only)."""

import json
import urllib.error
import urllib.request

DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2:3b"


class OllamaError(RuntimeError):
    pass


def generate(prompt, *, model=DEFAULT_MODEL, host=DEFAULT_HOST, system=None, json_mode=True):
    """Run a single chat completion and return the assistant's text."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {"model": model, "stream": False, "messages": messages}
    if json_mode:
        payload["format"] = "json"

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        host.rstrip("/") + "/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise OllamaError(
            f"could not reach Ollama at {host} — is it running? ({exc})"
        ) from exc

    return data["message"]["content"]
