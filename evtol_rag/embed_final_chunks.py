import json
import time

from . import config, db, voyage_embed

AUDIT_DIR = config.PROJECT_ROOT / "chunking_audit"
EMBEDDED_DIR = config.PROJECT_ROOT / "embedded_chunks"


def embed_and_store(source_path, doc_type):
    stem = source_path.stem
    after_path = AUDIT_DIR / f"{stem}_after.json"
    chunks = json.loads(after_path.read_text(encoding="utf-8"))

    texts = [c["text"] for c in chunks]
    t0 = time.time()

    def on_batch(done, total):
        print(f"    {done}/{total} embedded ({time.time() - t0:.0f}s elapsed)", flush=True)

    vectors = voyage_embed.embed_texts(texts, on_batch=on_batch)
    elapsed = time.time() - t0

    conn = db.get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM document_chunks WHERE source_document = %s", (source_path.name,))
        for i, (c, vec) in enumerate(zip(chunks, vectors)):
            cur.execute(
                """
                INSERT INTO document_chunks
                    (chunk_key, doc_type, source_document, page_start, page_end,
                     section_ref, chunk_index, text, char_count, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    f"{stem}::{i}",
                    doc_type,
                    source_path.name,
                    c["page_start"],
                    c["page_end"],
                    c["section_ref"],
                    i,
                    c["text"],
                    len(c["text"]),
                    json.dumps(vec),
                ),
            )
    conn.close()

    EMBEDDED_DIR.mkdir(exist_ok=True)
    local_records = [
        {
            "chunk_key": f"{stem}::{i}",
            "doc_type": doc_type,
            "source_document": source_path.name,
            "page_start": c["page_start"],
            "page_end": c["page_end"],
            "section_ref": c["section_ref"],
            "chunk_index": i,
            "text": c["text"],
            "embedding": vec,
        }
        for i, (c, vec) in enumerate(zip(chunks, vectors))
    ]
    (EMBEDDED_DIR / f"{stem}.json").write_text(
        json.dumps(local_records, ensure_ascii=False), encoding="utf-8"
    )

    return len(chunks), elapsed


if __name__ == "__main__":
    db.init_db()
    total_chunks = 0
    total_time = 0.0
    for stage, raw_dir in config.STAGE_RAW_DIRS.items():
        for path in sorted(raw_dir.glob("*")):
            if path.suffix.lower() not in (".pdf", ".txt", ".md"):
                continue
            print(f"embedding: {path.name}")
            try:
                n, elapsed = embed_and_store(path, stage)
            except Exception as e:
                print(f"  FAILED: {e}")
                continue
            total_chunks += n
            total_time += elapsed
            print(f"  {n} chunks embedded in {elapsed:.1f}s")

    print(f"\nTOTAL: {total_chunks} chunks in {total_time:.1f}s")
