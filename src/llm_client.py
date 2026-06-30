"""
llm_client.py
-------------
Thin wrapper around the OpenRouter API (OpenAI-compatible) for all LLM
calls used in this pipeline (categorization, sentiment, insight
extraction).

SETUP (do this locally, never commit your key):
  1. Create a file named `.env` in the project root (same folder as this
     `src/` directory) with one line:
         OPENROUTER_API_KEY=sk-or-v1-...
  2. pip install openai python-dotenv
  3. That's it -- every script in src/ loads the key from .env via
     load_dotenv(), so the key never appears in code or notebooks.

We use OpenRouter because it's a single key that can route to many
underlying models (Claude, GPT, Gemini, Llama, etc.) via an
OpenAI-compatible /chat/completions interface, which made it easy to
swap/compare models during development without re-plumbing the client.

Model choice: defaults to "anthropic/claude-sonnet-4.5" via OpenRouter.
Swap MODEL below to try others (e.g. "openai/gpt-4o-mini" for a cheaper/
faster pass, useful when iterating on prompts against all 100 transcripts).
"""

import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY not found. Create a .env file in the project "
        "root with: OPENROUTER_API_KEY=sk-or-v1-..."
    )

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

MODEL = "anthropic/claude-sonnet-4.5"


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = MODEL,
    max_retries: int = 3,
    temperature: float = 0.2,
    json_mode: bool = False,
) -> str:
    """Single LLM call with basic retry/backoff. Returns raw text content."""
    for attempt in range(max_retries):
        try:
            kwargs = dict(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content
        except Exception as e:
            wait = 2 ** attempt
            print(f"  [retry {attempt+1}/{max_retries}] {e} -- waiting {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"LLM call failed after {max_retries} retries")


def _extract_first_json_object(text: str) -> str:
    """Returns the substring spanning the first balanced {...} object in
    text, scanning brace depth so we ignore any trailing content the model
    appended after a complete JSON object (the cause of 'Extra data' errors
    -- e.g. the model emitted valid JSON and then extra commentary/a
    duplicate block after it)."""
    start = text.find("{")
    if start == -1:
        raise ValueError("No '{' found in model output")
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise ValueError("No balanced '}' found to close JSON object")


def call_llm_json(system_prompt: str, user_prompt: str, model: str = MODEL) -> dict:
    """Calls the LLM expecting a JSON object back, parses it, with
    progressively more aggressive cleanup if parsing fails:
      1. parse as-is
      2. strip markdown code fences
      3. extract just the first balanced {...} object, discarding any
         trailing content (handles 'Extra data' errors from models that
         add commentary or repeat output after valid JSON)
    """
    raw = call_llm(system_prompt, user_prompt, model=model, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    extracted = _extract_first_json_object(cleaned)
    return json.loads(extracted)


if __name__ == "__main__":
    out = call_llm(
        "You are a helpful assistant.",
        "Reply with exactly the word: OK",
    )
    print("Test call result:", out)