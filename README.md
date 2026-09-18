# eVTOL Propulsion Compliance Assistant

A 3-stage AI system for early-design certification review of eVTOL electric propulsion
systems, grounded entirely in real EASA aviation certification documents (SC-VTOL,
SC E-19, CS-23, CS-27, AMC-20, and related Means of Compliance publications).

Given an engineer's design description, the system:

1. **Stage 1 — Regulatory Compliance Check**: checks the design against the source
   documents and produces a structured report (compliant requirements, non-compliant
   requirements with exact clause references and quotes, suggested fixes, regulatory
   gaps).
2. **Stage 2 — Design Adjustment**: proposes concrete design changes for each
   non-compliant item, justified against the same clauses Stage 1 flagged, with
   engineering tradeoffs (weight, complexity, power, cost) drawn from real technical
   references (NASA systems-engineering and electric-propulsion publications).
3. **Stage 3 — Feasibility/Readiness Check**: not yet built.

Real example output from a full run: [`examples/stage1_example_output.txt`](examples/stage1_example_output.txt),
[`examples/stage2_example_output.txt`](examples/stage2_example_output.txt).

## The core finding this project is built around

Plain embedding-based retrieval (a standard RAG approach: chunk documents, embed them,
find the closest match to a query) reliably finds *topically similar* content, but
misses regulation text that's only relevant through multi-step inference. Concrete,
measured example: a design description mentioning a shared power bus and shared
coolant loop across redundant systems never uses the words "single failure" or
"catastrophic" — but the actual applicable rule (`VTOL.2510(a)(1)`) does. That rule
ranked **957th of 1,876 chunks** under plain cosine similarity — effectively
unreachable at any practical retrieval depth.

This is a documented limitation of single-vector ("bi-encoder") retrieval models,
studied under the term **reasoning-intensive retrieval** (see the BRIGHT benchmark and
the ReasonIR paper). The fix implemented here — HyDE (generating a hypothetical
regulation-style passage from the query before embedding) plus query rewriting — moved
that same chunk from rank 957 to rank 117, and was validated across 6 test queries
spanning different regulatory sub-domains (structural, battery, EMI/lightning,
redundancy, software assurance, operational), not just the one case it was built on.

Given how cheap large-context models have become, the current architecture goes
further: Stage 1 and Stage 2 read the **entire relevant document set directly**
(a cheap model, `deepseek/deepseek-v4-flash`, reading ~900K tokens costs about
$0.03–0.05 per run) rather than relying on retrieval alone. Retrieval remains in the
codebase (`evtol_rag/retrieve.py`) as a cheaper fallback path for larger corpora where
full-context reading isn't practical.

## What's in this repo

```
evtol_rag/              Python package: the actual pipeline
  config.py              paths and settings
  rag_utils.py           PDF text extraction + paragraph-aware chunking
  propose_chunks.py       LLM-reviewed chunk boundary proposal (with validation/retry)
  build_chunks.py         ties chunking together, writes before/after audit trail
  voyage_embed.py         Voyage AI embeddings, with free-tier rate limiting
  db.py                   MySQL storage
  retrieve.py              cosine-similarity retrieval (the fallback path)
  llm.py                  Anthropic + OpenRouter API clients
  query_transform.py       HyDE + query rewriting
  stage1.py               Stage 1: regulatory compliance check
  stage2.py               Stage 2: design adjustment

data/                   Source documents (real, public EASA/NASA publications)
  stage1_regulatory/raw/  9 EASA certification documents
  stage2_technical/raw/   5 NASA technical references
  stage3_feasibility/raw/ TRL guidance, incident data, case study

chunking_audit/         Before/after evidence for the chunking approach
  *_before.json           what a plain character-count chunker produced
  *_after.json             what LLM-reviewed chunk boundaries produced (6,452 → 2,376
                           chunks across the corpus, TOC/boilerplate flagged)
  chunking_before_after_comparison.html   self-contained visual comparison, open
                           directly in a browser

examples/                Real output from an actual run (not fabricated/edited)

site/                    Static pages (see below)
```

## Running it

```bash
pip install -r requirements.txt
cp .env.example .env      # fill in ANTHROPIC_API_KEY / VOYAGE_API_KEY / OPENROUTER_API_KEY
python -m evtol_rag.stage1
python -m evtol_rag.stage2
```

Stage 1 and Stage 2 extract text directly from the PDFs in `data/` at run time —
no pre-processing step required to get a first result. `evtol_rag/build_chunks.py` +
`evtol_rag/embed_final_chunks.py` are what produced the `chunking_audit/` evidence and
would populate a MySQL-backed retrieval fallback; they need `DB_*` and `VOYAGE_API_KEY`
configured.

## Site

Static, self-contained visual pages (no backend needed) — deployed from `site/`:

- **Chunking before/after** — real character-count chunking vs. LLM-reviewed chunk
  boundaries, per document, across all 17 source files.
- **Pipeline Inspector** — every real input and output at each step of an actual
  Stage 1 → Stage 2 run, including the HyDE transformation, not summarized.
