import json

from . import config, propose_chunks, rag_utils

AUDIT_DIR = config.PROJECT_ROOT / "chunking_audit"


def _section_ref_for_span(paragraphs, start, end):
    for i in range(start, end + 1):
        if paragraphs[i]["section_ref"]:
            return paragraphs[i]["section_ref"]
    return None


def build_final_chunks(source_path, doc_type):
    boundaries, paragraphs, usage = propose_chunks.get_boundaries(source_path)

    final_chunks = []
    for b in boundaries:
        span_paras = paragraphs[b["start"] : b["end"] + 1]
        text = "\n\n".join(p["text"] for p in span_paras).strip()
        if not text:
            continue
        final_chunks.append(
            {
                "text": text,
                "page_start": span_paras[0]["page_start"],
                "page_end": span_paras[-1]["page_end"],
                "section_ref": _section_ref_for_span(paragraphs, b["start"], b["end"]),
                "toc": bool(b.get("toc")),
            }
        )

    # "before" -- what the plain algorithmic chunker would have produced
    pages = rag_utils.extract_pages(source_path)
    before_chunks = rag_utils.chunk_document(pages)

    AUDIT_DIR.mkdir(exist_ok=True)
    stem = source_path.stem
    (AUDIT_DIR / f"{stem}_before.json").write_text(
        json.dumps(before_chunks, indent=2), encoding="utf-8"
    )
    (AUDIT_DIR / f"{stem}_after.json").write_text(
        json.dumps(final_chunks, indent=2), encoding="utf-8"
    )

    return final_chunks, before_chunks, usage


if __name__ == "__main__":
    total_before = 0
    total_after = 0
    for stage, raw_dir in config.STAGE_RAW_DIRS.items():
        for path in sorted(raw_dir.glob("*")):
            if path.suffix.lower() not in (".pdf", ".txt", ".md"):
                continue

            before_path = AUDIT_DIR / f"{path.stem}_before.json"
            after_path = AUDIT_DIR / f"{path.stem}_after.json"
            if before_path.exists() and after_path.exists():
                n_before = len(json.loads(before_path.read_text(encoding="utf-8")))
                n_after = len(json.loads(after_path.read_text(encoding="utf-8")))
                print(f"skip (already done): {path.name}  before: {n_before} -> after: {n_after}")
                total_before += n_before
                total_after += n_after
                continue

            print(f"processing: {path.name}")
            try:
                final_chunks, before_chunks, usage = build_final_chunks(path, stage)
            except Exception as e:
                print(f"  FAILED: {e}")
                continue
            total_before += len(before_chunks)
            total_after += len(final_chunks)
            print(f"  before: {len(before_chunks)} chunks -> after: {len(final_chunks)} chunks  usage={usage}")

    print(f"\nTOTAL before: {total_before}  after: {total_after}")
