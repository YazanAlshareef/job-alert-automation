"""One adapter for the LLM. Swap provider by editing this file only."""
import json
import os
import time

import requests

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def generate_json(prompt, retries=3):
    key, model = os.environ.get("GEMINI_API_KEY"), os.environ.get("GEMINI_MODEL")
    if not key or not model:
        raise RuntimeError("Set GEMINI_API_KEY and GEMINI_MODEL in .env.local")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}}
    for attempt in range(retries):
        r = requests.post(URL.format(model=model), json=body, headers={"x-goog-api-key": key}, timeout=60)
        if r.status_code in (429, 500, 503) and attempt < retries - 1:
            time.sleep(2 ** (attempt + 1))
            continue
        if not r.ok:  # status and body only: never print the request, it holds the key header
            raise RuntimeError(f"Gemini HTTP {r.status_code}: {r.text[:200]}")
        return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
