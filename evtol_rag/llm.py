import json
import os
import re

import anthropic
import openai

from . import config

_client = None
_openrouter_client = None


def _load_env():
    env_path = config.PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env()


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def get_openrouter_client():
    global _openrouter_client
    if _openrouter_client is None:
        _openrouter_client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
        )
    return _openrouter_client


def chat_openrouter(system, user_message, model="deepseek/deepseek-v4-flash", max_tokens=500):
    response = get_openrouter_client().chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
    )
    return (response.choices[0].message.content or "").strip()


BOUNDARY_SYSTEM_PROMPT = """You are chunking a regulatory/technical document for a RAG system whose \
embedding model has a hard {target_chars}-character limit per chunk -- ANY chunk larger than \
{target_chars} characters will be silently truncated and lose content. This is a strict ceiling, \
not a target to aim near.

You will be given a document as a list of numbered paragraphs.
Group consecutive paragraphs into chunks, following these rules in priority order:
1. A chunk's total character count (sum of its paragraphs' lengths) must NEVER exceed {target_chars}.
   If a single coherent section is longer than that, you MUST still split it into multiple chunks
   at its most reasonable internal sub-boundaries -- staying under the limit always wins over
   keeping a section whole.
2. Within that hard limit, avoid splitting a single requirement/clause/sentence across two chunks.
3. Prefer cutting between paragraphs that are about different topics/sections.
4. Mark a chunk as "toc": true if it is pure table-of-contents / section-listing content.
5. Don't pad a chunk with unrelated paragraphs just to approach the limit -- a short, coherent
   chunk is fine.

Respond with ONLY a JSON array, no prose, no markdown fences:
[{{"start": <first paragraph index>, "end": <last paragraph index, inclusive>, "toc": <true|false>}}, ...]
Every paragraph index from 0 to {max_idx} must be covered exactly once, in order, no gaps."""


def _extract_text(response):
    for block in response.content:
        if block.type == "text":
            return block.text.strip()
    raise ValueError(f"No text block in response (types: {[b.type for b in response.content]})")


def _parse_json_array(text):
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in response")
    candidate = text[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # common LLM slip: trailing comma before a closing bracket
        fixed = re.sub(r",\s*([\]}])", r"\1", candidate)
        return json.loads(fixed)


def _propose_via_anthropic(numbered, system, model, debug_path):
    with get_client().messages.stream(
        model=model,
        max_tokens=128000,
        system=system,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": numbered}],
    ) as stream:
        response = stream.get_final_message()
    text = _extract_text(response)
    if debug_path:
        debug_path.write_text(text, encoding="utf-8")
    if response.stop_reason == "max_tokens":
        raise ValueError(f"Response hit max_tokens (truncated) -- raw text saved to {debug_path}")
    usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    return text, usage


def _propose_via_openrouter(numbered, system, debug_path, model="deepseek/deepseek-v4-flash"):
    response = get_openrouter_client().chat.completions.create(
        model=model,
        max_tokens=64000,
        extra_body={"reasoning": {"effort": "low"}},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": numbered},
        ],
    )
    choice = response.choices[0]
    text = (choice.message.content or "").strip()
    if debug_path:
        debug_path.write_text(text, encoding="utf-8")
    if choice.finish_reason == "length":
        raise ValueError(f"Response hit max_tokens (truncated) -- raw text saved to {debug_path}")
    usage = {
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
    }
    return text, usage


def propose_chunk_boundaries(
    paragraphs, target_chars=1200, model="claude-sonnet-5", provider="openrouter", debug_path=None
):
    numbered = "\n".join(f"[{i}] {p}" for i, p in enumerate(paragraphs))
    system = BOUNDARY_SYSTEM_PROMPT.format(target_chars=target_chars, max_idx=len(paragraphs) - 1)

    if provider == "openrouter":
        text, usage = _propose_via_openrouter(numbered, system, debug_path)
    else:
        text, usage = _propose_via_anthropic(numbered, system, model, debug_path)

    try:
        return _parse_json_array(text), usage
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Could not parse response as JSON ({e}) -- raw text saved to {debug_path}")
