import hashlib
import json
from pathlib import Path

from . import config, llm, rag_utils

CACHE_DIR = config.PROJECT_ROOT / ".chunk_cache"


def _cache_path(source_path, file_hash):
    return CACHE_DIR / f"{source_path.stem}_{file_hash}.json"


def _validate_coverage(boundaries, n_paragraphs):
    if not boundaries:
        raise ValueError("empty boundaries list -- model returned no chunks")
    expected = 0
    for b in boundaries:
        if not isinstance(b, dict) or "start" not in b or "end" not in b:
            raise ValueError(f"malformed boundary entry (expected {{'start','end'}} object): {b!r}")
        if not isinstance(b["start"], int) or not isinstance(b["end"], int):
            raise ValueError(f"non-integer start/end in boundary entry: {b!r}")
        if b["start"] != expected:
            raise ValueError(f"gap/overlap: expected start={expected}, got {b['start']}")
        expected = b["end"] + 1
    if expected != n_paragraphs:
        raise ValueError(f"incomplete coverage: boundaries end at {expected - 1}, expected {n_paragraphs - 1}")


def get_boundaries(source_path, target_chars=1200, max_attempts=3):
    CACHE_DIR.mkdir(exist_ok=True)
    file_hash = hashlib.sha1(source_path.read_bytes()).hexdigest()[:16]
    cache_path = _cache_path(source_path, file_hash)

    pages = rag_utils.extract_pages(source_path)
    paragraphs = rag_utils.extract_paragraphs(pages)

    if cache_path.exists():
        cached = json.loads(cache_path.read_text())
        _validate_coverage(cached["boundaries"], len(paragraphs))
        return cached["boundaries"], paragraphs, cached["usage"]

    texts = [p["text"] for p in paragraphs]
    debug_path = CACHE_DIR / f"{source_path.stem}_{file_hash}.raw.txt"

    last_error = None
    for attempt in range(max_attempts):
        boundaries, usage = llm.propose_chunk_boundaries(
            texts, target_chars=target_chars, debug_path=debug_path
        )
        try:
            _validate_coverage(boundaries, len(paragraphs))
        except ValueError as e:
            last_error = e
            print(f"  attempt {attempt + 1} failed validation: {e}, retrying")
            continue
        cache_path.write_text(json.dumps({"boundaries": boundaries, "usage": usage}, indent=2))
        return boundaries, paragraphs, usage

    raise ValueError(f"failed to get valid coverage after {max_attempts} attempts: {last_error}")
