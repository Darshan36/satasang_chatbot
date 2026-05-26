"""Thin Gemini REST helpers shared by the pipeline scripts (raw `requests`)."""
import json
import re
import time

import requests

import config

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _retry_delay_seconds(resp, default):
    """Pull the server-suggested retry delay out of a 429 body, else `default`."""
    try:
        for d in resp.json().get("error", {}).get("details", []):
            if d.get("@type", "").endswith("RetryInfo") and "retryDelay" in d:
                m = re.match(r"([\d.]+)s", d["retryDelay"])
                if m:
                    return float(m.group(1)) + 2.0
    except (ValueError, KeyError, AttributeError):
        pass
    return default


def generate_json(prompt, schema, temperature=0.0, max_retries=8, timeout=120):
    """Call gemini generateContent with a forced JSON responseSchema.

    Returns the parsed JSON object. On 429 it waits the server-suggested
    retryDelay (handles the rolling free-tier window); on 5xx/network it backs
    off exponentially.
    """
    key = config.get_api_key()
    url = f"{_BASE}/{config.GEN_MODEL}:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
            "responseSchema": schema,
        },
    }
    delay = 2
    last_err = None
    for attempt in range(max_retries):
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            if r.status_code == 200:
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            if r.status_code == 429:
                wait = _retry_delay_seconds(r, default=delay)
                delay = min(delay * 2, 64)  # grow in case the next 429 has no retryDelay
                last_err = f"HTTP 429 (rate limit); waiting {wait:.0f}s"
                print(f"    [rate limit] waiting {wait:.0f}s...")
                time.sleep(wait)
                continue
            if r.status_code >= 500:
                last_err = f"HTTP {r.status_code}: {r.text[:200]}"
                time.sleep(delay)
                delay = min(delay * 2, 32)
                continue
            raise RuntimeError(f"Gemini error HTTP {r.status_code}: {r.text[:300]}")
        except (requests.RequestException, KeyError, ValueError) as e:
            last_err = str(e)
            time.sleep(delay)
            delay = min(delay * 2, 32)
    raise RuntimeError(f"generate_json failed after {max_retries} tries: {last_err}")


def batch_embed(texts, task_type, max_retries=10, timeout=120):
    """Embed a list of texts with gemini-embedding-001. Returns list of vectors
    (lists of floats) aligned to `texts`. NOT normalized — caller must L2-normalize.
    """
    key = config.get_api_key()
    m = config.EMBED_MODEL
    url = f"{_BASE}/{m}:batchEmbedContents?key={key}"
    reqs = [
        {
            "model": f"models/{m}",
            "content": {"parts": [{"text": t}]},
            "taskType": task_type,
            "outputDimensionality": config.EMBED_DIM,
        }
        for t in texts
    ]
    delay = 2
    last_err = None
    for attempt in range(max_retries):
        try:
            r = requests.post(url, json={"requests": reqs}, timeout=timeout)
            if r.status_code == 200:
                return [e["values"] for e in r.json()["embeddings"]]
            if r.status_code == 429:
                wait = _retry_delay_seconds(r, default=delay)
                delay = min(delay * 2, 64)  # grow in case the next 429 has no retryDelay
                last_err = f"HTTP 429 (rate limit); waiting {wait:.0f}s"
                print(f"    [rate limit] waiting {wait:.0f}s...")
                time.sleep(wait)
                continue
            if r.status_code >= 500:
                last_err = f"HTTP {r.status_code}: {r.text[:200]}"
                time.sleep(delay)
                delay = min(delay * 2, 32)
                continue
            raise RuntimeError(f"Embed error HTTP {r.status_code}: {r.text[:300]}")
        except (requests.RequestException, KeyError, ValueError) as e:
            last_err = str(e)
            time.sleep(delay)
            delay = min(delay * 2, 32)
    raise RuntimeError(f"batch_embed failed after {max_retries} tries: {last_err}")
