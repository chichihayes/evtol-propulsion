import json

import numpy as np

from . import db, voyage_embed

STAGE_DOC_TYPES = {
    "stage1": ["stage1_regulatory"],
    "stage2": ["stage1_regulatory", "stage2_technical"],
    "stage3": ["stage3_feasibility"],
}


def retrieve(query, stage, top_k=20):
    doc_types = STAGE_DOC_TYPES[stage]
    query_vec = np.array(voyage_embed.embed_query(query))

    conn = db.get_connection()
    with conn.cursor() as cur:
        placeholders = ",".join(["%s"] * len(doc_types))
        cur.execute(
            f"""
            SELECT chunk_key, source_document, page_start, page_end, section_ref, text, embedding
            FROM document_chunks
            WHERE doc_type IN ({placeholders}) AND is_toc = FALSE
            """,
            doc_types,
        )
        rows = cur.fetchall()
    conn.close()

    scored = []
    for chunk_key, source_document, page_start, page_end, section_ref, text, embedding_json in rows:
        vec = np.array(json.loads(embedding_json))
        score = float(np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec)))
        scored.append(
            {
                "chunk_key": chunk_key,
                "source_document": source_document,
                "page_start": page_start,
                "page_end": page_end,
                "section_ref": section_ref,
                "text": text,
                "score": score,
            }
        )

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_k]
