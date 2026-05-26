"""Groq (OpenAI-compatible) chat helper with JSON output + rate-limit handling.

Groq free tier: high RPD (~1000) but a tight tokens-per-minute budget, so the
retry honors the `retry-after` header on 429 (token-bucket refills each minute).
"""
import json
import time

import requests

import config

_URL = "https://api.groq.com/openai/v1/chat/completions"


def chat_json(prompt, max_retries=8, timeout=90, temperature=0.0):
    """Send one chat completion in JSON mode; return the parsed JSON object."""
    key = config.get_groq_key()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": config.GROQ_MODEL,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": prompt}],
    }
    delay = 3
    last_err = None
    for _ in range(max_retries):
        try:
            r = requests.post(_URL, headers=headers, json=payload, timeout=timeout)
            if r.status_code == 200:
                return json.loads(r.json()["choices"][0]["message"]["content"])
            if r.status_code == 429:
                wait = _parse_retry_after(r, default=delay)
                delay = min(delay * 2, 64)
                print(f"    [groq rate limit] waiting {wait:.0f}s...")
                time.sleep(wait)
                continue
            if r.status_code >= 500:
                last_err = f"HTTP {r.status_code}: {r.text[:200]}"
                time.sleep(delay)
                delay = min(delay * 2, 32)
                continue
            raise RuntimeError(f"Groq error HTTP {r.status_code}: {r.text[:300]}")
        except (requests.RequestException, KeyError, ValueError) as e:
            last_err = str(e)
            time.sleep(delay)
            delay = min(delay * 2, 32)
    raise RuntimeError(f"chat_json failed after {max_retries} tries: {last_err}")


def _parse_retry_after(resp, default):
    ra = resp.headers.get("retry-after")
    if ra:
        try:
            return float(ra) + 1.0
        except ValueError:
            pass
    # Fall back to the token-bucket reset hint if present (e.g. "440ms", "1m26.4s").
    reset = resp.headers.get("x-ratelimit-reset-tokens", "")
    secs = 0.0
    import re
    m = re.search(r"(\d+)m", reset)
    if m:
        secs += int(m.group(1)) * 60
    m = re.search(r"([\d.]+)s", reset)
    if m:
        secs += float(m.group(1))
    return (secs + 1.0) if secs else default
