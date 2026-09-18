from . import config, llm, query_transform, rag_utils
from .stage1 import build_corpus as build_stage1_corpus

# Scoped to the docs most relevant to power/thermal redundancy questions, skipping the
# much larger general-purpose NASA Systems Engineering Handbook (see chunking_audit/
# for the full technical doc set used during evaluation).
STAGE2_TECHNICAL_DOCS = [
    "NASA_Power_System_Redundancy_Design_Trends_AllElectric.pdf",
    "NASA_X-57_Power_and_Command_System_Design.pdf",
    "NASA_X-57_SCEPTOR_Thermal_Analysis.pdf",
]

STAGE2_SYSTEM_PROMPT = """You are an aviation design engineering assistant. You will be given: the full \
text of EASA aviation certification documents, technical engineering reference documents, a hypothetical \
technical framing (context only), the original design description, and Stage 1's full compliance \
findings (non-compliant requirements with exact clause references).

For each non-compliant item from Stage 1, propose 2-3 concrete design changes that would resolve it. For \
each proposed option:
- Describe the specific design change.
- Explain, citing the SAME clause Stage 1 flagged, why this change would satisfy it -- quote or reference \
  the clause text again to justify this.
- Reference relevant technical/engineering guidance from the provided technical documents where \
  applicable (cite the document).
- State the performance impact (weight, complexity, power, cost) plainly -- do not hide tradeoffs.

Then give ONE ranked recommendation across all options, with a one-sentence reason.

Do not invent compliance -- if you are not confident a proposed fix actually satisfies the clause, say so \
explicitly rather than asserting it does."""


def build_stage2_corpus():
    parts = [build_stage1_corpus()]
    for name in STAGE2_TECHNICAL_DOCS:
        path = config.STAGE_RAW_DIRS["stage2_technical"] / name
        pages = rag_utils.extract_pages(path)
        text = "\n".join(pages)
        parts.append(f"\n\n===== TECHNICAL REFERENCE: {name} =====\n\n{text}")
    return "".join(parts)


def run_stage2(design_description, stage1_report, model="deepseek/deepseek-v4-flash"):
    hyde_doc = query_transform.generate_hyde(stage1_report)

    corpus = build_stage2_corpus()
    user_message = (
        f"{corpus}\n\n"
        f"===== HYPOTHETICAL TECHNICAL FRAMING (context only) =====\n\n{hyde_doc}\n\n"
        f"===== ORIGINAL DESIGN DESCRIPTION =====\n\n{design_description}\n\n"
        f"===== STAGE 1 FINDINGS =====\n\n{stage1_report}"
    )

    response = llm.get_openrouter_client().chat.completions.create(
        model=model,
        max_tokens=16000,
        messages=[
            {"role": "system", "content": STAGE2_SYSTEM_PROMPT},
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
    from .stage1 import run_stage1

    q = (
        "Our aircraft uses 8 electric motors in a distributed lift configuration, each independently "
        "powered by its own battery pack and motor controller, no shared power bus between motor groups. "
        "The flight control computer has triple redundancy, but all three units draw power from a single "
        "28V DC bus. Motors are liquid-cooled with one shared coolant loop across all 8 units."
    )
    stage1_result = run_stage1(q)
    result = run_stage2(q, stage1_result["report"])
    print(f"usage: {result['usage']}")
    with open("stage2_output.txt", "w", encoding="utf-8") as f:
        f.write("=== HyDE doc ===\n" + result["hyde_doc"] + "\n\n=== Stage 2 Report ===\n" + result["report"])
    print("saved to stage2_output.txt")
