"""Thin wrapper around Groq's OpenAI-compatible chat completions API.

The key is read from ``GROQ_API_KEY`` first, then from the local
``groq_api_key.txt`` file. Without a key, ``generate()`` falls back to template
mode so the rest of the pipeline remains runnable.
"""

import os
import json

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(PROJECT_DIR, "groq_api_key.txt")
MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


def _api_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key:
        return key
    try:
        with open(KEY_FILE, encoding="utf-8") as key_file:
            return key_file.read().strip()
    except FileNotFoundError:
        return ""


def _mock_response(system: str, prompt: str) -> str:
    return (
        "[MOCK MODE — no GROQ_API_KEY set, this is placeholder output]\n"
        "Set GROQ_API_KEY or add the key to groq_api_key.txt for real generated content here.\n"
        f"(Prompt received {len(prompt)} chars)"
    )


def generate(system: str, prompt: str, max_tokens: int = 1500) -> str:
    api_key = _api_key()
    if not api_key:
        return _mock_response(system, prompt)

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content or ""


def generate_json(system: str, prompt: str, max_tokens: int = 1500) -> dict:
    """Same as generate(), but asks for and parses strict JSON output."""
    json_instruction = "\n\nRespond with ONLY valid JSON. No markdown fences, no preamble."
    raw = generate(system, prompt + json_instruction, max_tokens)
    if raw.startswith("[MOCK MODE"):
        return {"mock": True, "raw": raw}
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "failed to parse JSON", "raw": raw}
