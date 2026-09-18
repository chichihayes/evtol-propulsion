const fs = require("fs");
const path = require("path");

const HYDE_SYSTEM_PROMPT = `You are helping build a search query for an aviation certification regulation retrieval system. Given an engineering design description or question, first work out which regulatory sub-domain(s) it actually belongs to -- for example: structural loads/durability, flight performance and handling qualities, propulsion battery/energy storage, electrical system redundancy and failure conditions, EMI/lightning/HIRF protection, software/control system assurance levels, or operational/administrative requirements (e.g. category classification, seating limits). Do not default to failure-condition/redundancy language unless the description is actually about that.

Then write a short hypothetical excerpt (3-5 sentences) from an aviation certification specification, in the style of EASA/FAA regulations (SC-VTOL, CS-23, CS-27, SC E-19, AMC-20), using the terminology and concepts appropriate to that specific sub-domain. Do not mention this is hypothetical or name the sub-domain explicitly. Respond with ONLY the excerpt text, no preamble.`;

const STAGE1_SYSTEM_PROMPT = `You are an aviation certification compliance assistant. You will be given the full text of EASA aviation certification documents, a hypothetical regulatory framing of the design's safety concerns (for context only, may not be fully accurate), and an engineer's design description.

Check the design against the documents and produce a structured compliance report with these exact sections:

## Compliant Requirements
List requirements the design satisfies, each with the specific document and clause reference.

## Non-Compliant Requirements
List requirements the design fails, each with the exact clause reference and a quote of the relevant text.

## Suggested Fixes
For each non-compliant item, a concrete suggested design change.

## Regulatory Gaps Found
Anything the design raises that the provided documents do not clearly address. Say so explicitly rather than guessing -- do not invent requirements that are not in the provided text.

Do not include a summary section. Every finding must stay in full detail (exact clause, exact quote) -- nothing condensed or paraphrased away. This output is passed directly to a later stage that needs the full findings, not an abbreviated version.

Only cite documents and clauses that actually appear in the provided text. Never rely on outside knowledge of aviation regulations not present in the given documents.`;

const STAGE2_SYSTEM_PROMPT = `You are an aviation design engineering assistant. You will be given: the full text of EASA aviation certification documents, technical engineering reference documents, a hypothetical technical framing (context only), the original design description, and Stage 1's full compliance findings (non-compliant requirements with exact clause references).

For each non-compliant item from Stage 1, propose 2-3 concrete design changes that would resolve it. For each proposed option:
- Describe the specific design change.
- Explain, citing the SAME clause Stage 1 flagged, why this change would satisfy it -- quote or reference the clause text again to justify this.
- Reference relevant technical/engineering guidance from the provided technical documents where applicable (cite the document).
- State the performance impact (weight, complexity, power, cost) plainly -- do not hide tradeoffs.

Then give ONE ranked recommendation across all options, with a one-sentence reason.

Do not invent compliance -- if you are not confident a proposed fix actually satisfies the clause, say so explicitly rather than asserting it does.`;

function readCorpus(name) {
  return fs.readFileSync(path.join(process.cwd(), "api", "corpus", name), "utf-8");
}

async function callOpenRouter(systemPrompt, userMessage, maxTokens) {
  const resp = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
    },
    body: JSON.stringify({
      model: "deepseek/deepseek-v4-flash",
      max_tokens: maxTokens,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userMessage },
      ],
    }),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`OpenRouter error ${resp.status}: ${text}`);
  }
  const data = await resp.json();
  const content = data.choices?.[0]?.message?.content;
  if (!content || !content.trim()) {
    throw new Error("Empty response from model");
  }
  return { text: content.trim(), usage: data.usage };
}

module.exports = { HYDE_SYSTEM_PROMPT, STAGE1_SYSTEM_PROMPT, STAGE2_SYSTEM_PROMPT, readCorpus, callOpenRouter };
