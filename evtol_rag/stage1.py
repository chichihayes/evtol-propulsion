from . import config, llm, query_transform, rag_utils

STAGE1_SYSTEM_PROMPT = """You are an aviation certification compliance assistant. You will be given the \
full text of EASA aviation certification documents, a hypothetical regulatory framing of the design's \
safety concerns (for context only, may not be fully accurate), and an engineer's design description.

Check the design against the documents and produce a structured compliance report with these exact \
sections:

## Compliant Requirements
List requirements the design satisfies, each with the specific document and clause reference.

## Non-Compliant Requirements
List requirements the design fails, each with the exact clause reference and a quote of the relevant text.

## Suggested Fixes
For each non-compliant item, a concrete suggested design change.

## Regulatory Gaps Found
Anything the design raises that the provided documents do not clearly address. Say so explicitly rather \
than guessing -- do not invent requirements that are not in the provided text.

Do not include a summary section. Every finding must stay in full detail (exact clause, exact quote) --\
 nothing condensed or paraphrased away. This output is passed directly to a later stage that needs the \
full findings, not an abbreviated version.

Only cite documents and clauses that actually appear in the provided text. Never rely on outside \
knowledge of aviation regulations not present in the given documents."""


def build_corpus():
    """Extracts the full text of every stage1 regulatory PDF fresh from data/stage1_regulatory/raw/."""
    parts = []
    for path in sorted(config.STAGE_RAW_DIRS["stage1_regulatory"].glob("*")):
        if path.suffix.lower() not in (".pdf", ".txt", ".md"):
            continue
        pages = rag_utils.extract_pages(path)
        text = "\n".join(pages)
        parts.append(f"\n\n===== DOCUMENT: {path.name} =====\n\n{text}")
    return "".join(parts)


def run_stage1(design_description, model="deepseek/deepseek-v4-flash"):
    hyde_doc = query_transform.generate_hyde(design_description)

    corpus = build_corpus()
    user_message = (
        f"{corpus}\n\n"
        f"===== HYPOTHETICAL REGULATORY FRAMING (context only) =====\n\n{hyde_doc}\n\n"
        f"===== ENGINEER'S DESIGN DESCRIPTION =====\n\n{design_description}"
    )

    response = llm.get_openrouter_client().chat.completions.create(
        model=model,
        max_tokens=16000,
        messages=[
            {"role": "system", "content": STAGE1_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    choice = response.choices[0]
    return {
        "hyde_doc": hyde_doc,
        "report": choice.message.content,
        "usage": {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        },
    }


if __name__ == "__main__":
    q = (
        "Our aircraft uses 8 electric motors in a distributed lift configuration, each independently "
        "powered by its own battery pack and motor controller, no shared power bus between motor groups. "
        "The flight control computer has triple redundancy, but all three units draw power from a single "
        "28V DC bus. Motors are liquid-cooled with one shared coolant loop across all 8 units."
    )
    result = run_stage1(q)
    print(f"usage: {result['usage']}")
    with open("stage1_output.txt", "w", encoding="utf-8") as f:
        f.write("=== HyDE doc ===\n" + result["hyde_doc"] + "\n\n=== Stage 1 Report ===\n" + result["report"])
    print("saved to stage1_output.txt")
