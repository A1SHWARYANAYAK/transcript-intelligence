"""
categorize.py
-------------
Task 1: categorize all 100 transcripts by topic/theme.

APPROACH (hybrid, bottom-up then converged):
  Step 1 (open-ended discovery): show the LLM a sample of ~20 transcripts
          (summaries, not full text, to keep tokens reasonable) and ask it
          to propose a topic taxonomy bottom-up, rather than us guessing
          categories top-down. This avoids forcing the data into categories
          that don't actually fit a B2B SaaS call dataset.
  Step 2 (human-in-the-loop convergence): we review the proposed taxonomy,
          collapse near-duplicates, and lock a final fixed set of ~8-10
          categories. This step is manual/printed -- a human (you) reviews
          the LLM's proposal before it becomes "official."
  Step 3 (classification): classify all 100 transcripts against the FIXED
          taxonomy using a structured prompt (JSON output: category,
          confidence, 1-line rationale). Each transcript gets exactly one
          PRIMARY category (for clean aggregate stats) plus optional
          secondary tags, since real calls are rarely about one thing.

WHY HYBRID OVER PURE CLUSTERING OR PURE RULES:
  - Pure embedding clustering (e.g. k-means on sentence embeddings) finds
    structure but the clusters need labeling anyway, and with only 100
    docs, clusters are noisy and don't reliably align with concepts a
    product/eng leader actually cares about (e.g. "churn risk" or "outage
    response" are business concepts, not necessarily the tightest semantic
    clusters in embedding space).
  - Pure rules (keyword matching) are fast and auditable but brittle: this
    dataset's titles and content are varied enough (e.g. "URGENT:
    Blackridge Investments - Complete Loss of Threat Visibility" vs.
    "Detect Outage - Post-Incident Review") that hand-written regexes
    would need constant patching and miss nuance.
  - LLM-based classification with a small, fixed, human-reviewed taxonomy
    gets us business-relevant categories, transparent rationale per call
    (auditable -- you can see WHY a call was tagged a certain way), and
    is fast enough to run on 100 transcripts in a couple minutes.

VALIDATION: the dataset ships with a pre-existing `topics` field per call
(see load_data.py docstring). We do NOT use this as ground truth (it's
free-text, many-per-call, no fixed taxonomy) but we DO compare our final
categories against it qualitatively as a sanity check -- see
notebooks/01_categorization.ipynb for that comparison.
"""

import json
import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(__file__))
from llm_client import call_llm, call_llm_json

DISCOVERY_SAMPLE_SIZE = 20

DISCOVERY_SYSTEM_PROMPT = """You are a B2B SaaS operations analyst. You will be
shown summaries of customer/internal call transcripts from a cybersecurity
and compliance SaaS company. Your job is to propose a topic/theme taxonomy
that would help product, support, sales, and engineering leaders quickly
understand what's happening across hundreds of calls.

Propose 8-12 distinct categories. Each category should be:
- Mutually exclusive enough to be useful as a PRIMARY label
- Meaningful to a business stakeholder (not overly technical or overly broad)
- Backed by at least 2-3 examples from what you were shown

Return ONLY a JSON object: {"categories": [{"name": "...", "description": "...", "example_call_ids": ["...", "..."]}]}
"""

CLASSIFY_SYSTEM_PROMPT = """You are classifying a single call transcript from
a B2B cybersecurity/compliance SaaS company into ONE primary category from a
FIXED taxonomy, plus optional secondary categories if genuinely relevant.

Fixed taxonomy:
{taxonomy_block}

Return ONLY a JSON object with this exact shape:
{{
  "primary_category": "<one of the category names above, exactly>",
  "secondary_categories": ["<zero or more other category names>"],
  "confidence": <float 0-1>,
  "rationale": "<one sentence explaining why this category fits, referencing something specific from the call>"
}}
"""


def run_discovery(df: pd.DataFrame) -> dict:
    """Step 1: ask the LLM to propose a taxonomy from a sample, stratified
    across call types so the proposal isn't skewed toward one type."""
    sample = (
        df.groupby("call_type", group_keys=False)
        .apply(lambda g: g.sample(min(len(g), max(1, DISCOVERY_SAMPLE_SIZE // 3)), random_state=42))
        .reset_index(drop=True)
    )

    blob = "\n\n".join(
        f"[{row.call_id}] ({row.call_type}) {row.title}\nSummary: {row.baseline_summary}"
        for row in sample.itertuples()
    )

    result = call_llm_json(
        DISCOVERY_SYSTEM_PROMPT,
        f"Here are {len(sample)} call summaries:\n\n{blob}\n\nPropose the taxonomy now.",
    )
    return result


def classify_all(df: pd.DataFrame, taxonomy: list[dict]) -> pd.DataFrame:
    """Step 3: classify every transcript against the fixed taxonomy."""
    taxonomy_block = "\n".join(f"- {c['name']}: {c['description']}" for c in taxonomy)
    system_prompt = CLASSIFY_SYSTEM_PROMPT.format(taxonomy_block=taxonomy_block)

    results = []
    for i, row in enumerate(df.itertuples()):
        print(f"  classifying {i+1}/{len(df)}: {row.call_id} ({row.title[:50]})")
        user_prompt = (
            f"Title: {row.title}\n"
            f"Call type: {row.call_type}\n"
            f"Summary: {row.baseline_summary}\n\n"
            f"Full transcript (for context if summary is ambiguous):\n{row.transcript_text[:4000]}"
        )
        r = None
        last_err = None
        for attempt in range(2):  # one retry on top of the initial attempt
            try:
                r = call_llm_json(system_prompt, user_prompt)
                break
            except Exception as e:
                last_err = e
                if attempt == 0:
                    print(f"    retrying {row.call_id} after parse/call error: {e}")
        if r is None:
            print(f"    ERROR on {row.call_id} after retry: {last_err}")
            r = {
                "primary_category": "UNCLASSIFIED",
                "secondary_categories": [],
                "confidence": 0.0,
                "rationale": f"classification failed after retry: {last_err}",
            }
        r["call_id"] = row.call_id
        results.append(r)

    return pd.DataFrame(results)


def main():
    sys.path.append(os.path.join(os.path.dirname(__file__)))
    from load_data import load_all_transcripts

    df = load_all_transcripts()

    print("Step 1: running open-ended taxonomy discovery on a sample...")
    discovery = run_discovery(df)
    print(json.dumps(discovery, indent=2))

    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "discovered_taxonomy_RAW.json"), "w") as f:
        json.dump(discovery, f, indent=2)

    print(
        "\n>>> Review outputs/discovered_taxonomy_RAW.json, edit/collapse as "
        "needed, save the final version as outputs/taxonomy_FINAL.json, "
        "then re-run with --classify to classify all 100 transcripts."
    )

    if "--classify" in sys.argv:
        final_path = os.path.join(out_dir, "taxonomy_FINAL.json")
        if not os.path.exists(final_path):
            print(f"No {final_path} found -- using raw discovery output as-is.")
            taxonomy = discovery["categories"]
        else:
            with open(final_path) as f:
                taxonomy = json.load(f)["categories"]

        print("\nStep 3: classifying all 100 transcripts...")
        results = classify_all(df, taxonomy)
        results.to_csv(os.path.join(out_dir, "categorization_results.csv"), index=False)
        print(f"Saved {len(results)} classifications to outputs/categorization_results.csv")


if __name__ == "__main__":
    main()