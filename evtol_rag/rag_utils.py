import re

import fitz

from . import config

SECTION_PATTERN = re.compile(
    r"\b(?:CS|AMC|SC[- ]?E|SC-VTOL|ED|DO|ARP|CM)[\s-]?\d[\d.\-A-Za-z]*\b"
)
PARA_PATTERN = re.compile(r"\S.*?(?=\n\s*\n|\Z)", re.S)


def extract_pages(path):
    if path.suffix.lower() == ".pdf":
        doc = fitz.open(path)
        pages = [page.get_text() for page in doc]
        doc.close()
        return pages
    return [path.read_text(encoding="utf-8")]


def _page_offsets(pages):
    offsets = []
    pos = 0
    for page in pages:
        offsets.append(pos)
        pos += len(page) + 1
    return offsets


def _page_for_offset(offsets, offset):
    page_num = 1
    for i, start in enumerate(offsets):
        if offset >= start:
            page_num = i + 1
        else:
            break
    return page_num


def extract_paragraphs(pages):
    """Return each paragraph's text plus its page range and nearest section_ref,
    for LLM-guided chunking (llm.propose_chunk_boundaries)."""
    full_text = "\n".join(pages)
    offsets = _page_offsets(pages)
    section_matches = [(m.start(), m.group(0)) for m in SECTION_PATTERN.finditer(full_text)]

    results = []
    for m in PARA_PATTERN.finditer(full_text):
        start, end = m.start(), m.end()
        section_ref = None
        for m_start, m_text in section_matches:
            if m_start <= start:
                section_ref = m_text
            else:
                break
        results.append(
            {
                "text": m.group(0),
                "page_start": _page_for_offset(offsets, start),
                "page_end": _page_for_offset(offsets, end),
                "section_ref": section_ref,
            }
        )
    return results


def chunk_document(pages, size=None, overlap=None):
    size = size or config.CHUNK_SIZE_CHARS
    overlap = overlap or config.CHUNK_OVERLAP_CHARS
    full_text = "\n".join(pages)
    if not full_text.strip():
        return []

    offsets = _page_offsets(pages)
    section_matches = [(m.start(), m.group(0)) for m in SECTION_PATTERN.finditer(full_text)]
    paragraphs = [(m.start(), m.end()) for m in PARA_PATTERN.finditer(full_text)]

    raw_spans = []
    buf_start = buf_end = None
    for para_start, para_end in paragraphs:
        if buf_start is None:
            buf_start, buf_end = para_start, para_end
            continue
        if (para_end - buf_start) > size:
            raw_spans.append((buf_start, buf_end))
            buf_start = max(buf_end - overlap, buf_start)
            buf_end = para_end
        else:
            buf_end = para_end
    if buf_start is not None:
        raw_spans.append((buf_start, buf_end))

    final_spans = []
    for start, end in raw_spans:
        if end - start <= size:
            final_spans.append((start, end))
            continue
        pos = start
        while pos < end:
            seg_end = min(pos + size, end)
            final_spans.append((pos, seg_end))
            if seg_end >= end:
                break
            pos = seg_end - overlap

    results = []
    for start, end in final_spans:
        text = full_text[start:end].strip()
        if not text:
            continue
        section_ref = None
        for m_start, m_text in section_matches:
            if m_start <= start:
                section_ref = m_text
            else:
                break
        results.append(
            {
                "text": text,
                "page_start": _page_for_offset(offsets, start),
                "page_end": _page_for_offset(offsets, end),
                "section_ref": section_ref,
            }
        )
    return results
