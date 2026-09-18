import os
import time

import voyageai

from . import config

# Free-tier limits (no payment method on file): 3 requests/min, 10K tokens/min.
MIN_SECONDS_BETWEEN_REQUESTS = 21  # 60s / 3 requests, plus a small safety margin

_client = None
_last_request_time = None


def _wait_for_rate_limit():
    global _last_request_time
    if _last_request_time is not None:
        wait = MIN_SECONDS_BETWEEN_REQUESTS - (time.time() - _last_request_time)
        if wait > 0:
            time.sleep(wait)


def _mark_request():
    global _last_request_time
    _last_request_time = time.time()


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
        _client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
    return _client


CHARS_PER_TOKEN_ESTIMATE = 3  # conservative for dense regulatory/technical text
MAX_TOKENS_PER_BATCH = 2800  # headroom under 10K TPM / 3 requests-per-min
MAX_CHARS_PER_BATCH = MAX_TOKENS_PER_BATCH * CHARS_PER_TOKEN_ESTIMATE


def _make_batches(texts, max_batch_chars=MAX_CHARS_PER_BATCH):
    batches = []
    current = []
    current_chars = 0
    for t in texts:
        if current and current_chars + len(t) > max_batch_chars:
            batches.append(current)
            current = []
            current_chars = 0
        current.append(t)
        current_chars += len(t)
    if current:
        batches.append(current)
    return batches


def embed_texts(texts, model="voyage-4-lite", on_batch=None):
    all_embeddings = []
    for batch in _make_batches(texts):
        _wait_for_rate_limit()

        for attempt in range(5):
            try:
                result = get_client().embed(batch, model=model, input_type="document")
                break
            except voyageai.error.RateLimitError:
                backoff = 30 * (attempt + 1)
                print(f"    rate limited, waiting {backoff}s")
                time.sleep(backoff)
        else:
            raise RuntimeError("rate limited after 5 retries")

        _mark_request()
        all_embeddings.extend(result.embeddings)
        if on_batch:
            on_batch(len(all_embeddings), len(texts))
    return all_embeddings


def embed_query(text, model="voyage-4-lite"):
    _wait_for_rate_limit()
    for attempt in range(5):
        try:
            result = get_client().embed([text], model=model, input_type="query")
            break
        except voyageai.error.RateLimitError:
            backoff = 30 * (attempt + 1)
            print(f"    rate limited, waiting {backoff}s")
            time.sleep(backoff)
    else:
        raise RuntimeError("rate limited after 5 retries")
    _mark_request()
    return result.embeddings[0]
