"""Tiny OpenRouter chat client (the only network dependency in this kit).

Reads OPENROUTER_API_KEY from the environment. Honors HTTP(S)_PROXY env vars
automatically via `requests`, which is what you need on a corporate network
where a direct call to OpenRouter times out.
"""
import os
import time

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TIMEOUT = 120


class LLMError(RuntimeError):
    pass


def _api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise LLMError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env and put your "
            "key there, or `export OPENROUTER_API_KEY=...`. Get one at "
            "https://openrouter.ai/keys"
        )
    return key


def chat(prompt: str, model: str, temperature: float = 0.0, max_tokens: int = 4096,
         timeout: int = DEFAULT_TIMEOUT, retries: int = 4) -> str:
    """Send a single user message to OpenRouter and return the assistant text."""
    headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.post(OPENROUTER_URL, headers=headers, json=body, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            if resp.status_code in (429, 500, 502, 503, 504):
                last_err = LLMError(f"OpenRouter HTTP {resp.status_code}: {resp.text[:300]}")
                time.sleep(2 ** attempt)
                continue
            raise LLMError(f"OpenRouter HTTP {resp.status_code}: {resp.text[:500]}")
        except requests.exceptions.Timeout as e:
            last_err = e
            time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as e:
            last_err = e
            time.sleep(2 ** attempt)
    raise LLMError(
        f"OpenRouter call failed after {retries} attempts: {last_err}. "
        "On the office network a timeout usually means the request is being blocked; "
        "set HTTPS_PROXY (see .env.example) and try again."
    )
