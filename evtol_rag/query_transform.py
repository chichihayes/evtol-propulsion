import json

from . import llm

HYDE_SYSTEM_PROMPT = """You are helping build a search query for an aviation certification regulation \
retrieval system. Given an engineering design description or question, first work out which regulatory \
sub-domain(s) it actually belongs to -- for example: structural loads/durability, flight performance and \
handling qualities, propulsion battery/energy storage, electrical system redundancy and failure conditions, \
EMI/lightning/HIRF protection, software/control system assurance levels, or operational/administrative \
requirements (e.g. category classification, seating limits). Do not default to failure-condition/redundancy \
language unless the description is actually about that.

Then write a short hypothetical excerpt (3-5 sentences) from an aviation certification specification, in \
the style of EASA/FAA regulations (SC-VTOL, CS-23, CS-27, SC E-19, AMC-20), using the terminology and \
concepts appropriate to that specific sub-domain. Do not mention this is hypothetical or name the sub-domain \
explicitly. Respond with ONLY the excerpt text, no preamble."""

REWRITE_SYSTEM_PROMPT = """Given an engineering design description or question, first work out which \
regulatory sub-domain(s) it belongs to (structural loads, flight performance, battery/energy storage, \
electrical redundancy/failure conditions, EMI/lightning/HIRF, software assurance, operational/ \
administrative requirements, etc.) -- do not assume it's about failure conditions/redundancy unless it \
actually is. Generate 3 alternative search queries that rephrase the underlying concern using the formal \
regulatory terminology appropriate to that sub-domain, so they would match how an aviation certification \
specification actually discusses it. Respond with ONLY a JSON array of 3 strings, no prose."""


def generate_hyde(design_description, max_attempts=3):
    last_error = None
    for _ in range(max_attempts):
        text = llm.chat_openrouter(HYDE_SYSTEM_PROMPT, design_description, max_tokens=4000)
        if text and text.strip():
            return text.strip()
        last_error = "empty response"
    raise ValueError(f"failed to get non-empty HyDE response after {max_attempts} attempts: {last_error}")


def generate_rewrites(design_description, max_attempts=3):
    last_error = None
    for _ in range(max_attempts):
        text = llm.chat_openrouter(REWRITE_SYSTEM_PROMPT, design_description)
        try:
            return llm._parse_json_array(text)
        except ValueError as e:
            last_error = e
    raise ValueError(f"failed to get valid rewrites JSON after {max_attempts} attempts: {last_error}")
