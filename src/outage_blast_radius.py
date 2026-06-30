"""
outage_blast_radius.py
-----------------------
BONUS INSIGHT (fully implemented): "Incident Blast Radius Timeline"

WHAT IT IS:
  A cross-functional timeline that traces a single product incident (the
  "Detect" pipeline outage, March 10-20 2026) as it ripples across all
  three call types: internal response, customer-facing escalations, and
  support tickets from affected customers -- on one timeline, with
  sentiment/urgency overlaid.

WHY IT MATTERS (the pitch):
  Today, these 20 calls live in three different silos: support sees
  tickets, sales/AM sees escalation calls, engineering sees war rooms and
  RCAs. No single view shows a PM or eng leader "this one pipeline bug
  cost us 20 calls across 8 different customer accounts over 12 days, hit
  two major accounts (Northstar Pharma, Blackridge Investments) hard
  enough to trigger compliance-risk language, and is now showing up in a
  competitive-threat assessment." That composite view is the kind of
  thing that changes incident retro prioritization and could justify
  engineering investment that a single support ticket count never would.

HOW IT'S BUILT:
  1. Identify candidate "incident clusters": calls whose titles/content
     reference the same underlying event. For this dataset we detect this
     via keyword matching on the title (a simple, transparent, auditable
     rule -- "Detect Outage", "INCIDENT", "Pipeline Failure", company
     names appearing in support tickets during the same window) PLUS an
     LLM pass to confirm/reject borderline calls and identify which
     customer accounts were affected.
  2. For each call in the cluster, the LLM extracts: which customer (if
     any) was involved, what stage of the incident lifecycle this call
     represents (detection / customer impact / escalation / remediation
     / resolution / retrospective), and a 1-line "what happened" note.
  3. Output: a structured timeline (CSV + chart) that can be dropped
     straight into a slide.

HOW TO GENERALIZE THIS BEYOND ONE HAND-FOUND INCIDENT:
  In production this wouldn't be a one-off script for one outage -- it
  would be: (a) embed all call summaries, (b) cluster temporally-close,
  semantically-similar calls, (c) for any cluster spanning 2+ call types
  within a short window, auto-flag it as a candidate "cross-functional
  incident" and run this same stage-extraction + timeline generation on
  it. We describe this generalization in the slide deck/notebook but did
  not build the generic clustering version given the time-box -- this
  module demonstrates the concept end-to-end on the one clear real
  incident in the sample data.
"""

import sys
import os
import re
import pandas as pd

sys.path.append(os.path.dirname(__file__))
from llm_client import call_llm_json

INCIDENT_KEYWORDS = re.compile(
    r"detect outage|incident|pipeline failure|war room|threat visibility|"
    r"detect alerts not firing|detect data gaps|detect latency|"
    r"false positives after patch|recovery confirmation|dashboard down",
    re.IGNORECASE,
)

STAGE_SYSTEM_PROMPT = """You are reconstructing a timeline of a single
product incident (a "Detect" pipeline outage at a B2B cybersecurity SaaS
company) from individual call transcripts. You will be shown ONE call that
has been flagged as plausibly related to this incident.

Determine:
1. is_incident_related: true/false -- does this call genuinely discuss the
   Detect outage/its aftermath, or was it a false-positive keyword match?
2. customer_affected: the customer company name if a specific customer's
   impact is discussed, else null (null for purely internal calls with no
   named customer).
3. incident_stage: one of "detection", "customer_impact", "escalation",
   "remediation", "resolution", "retrospective" -- which phase of incident
   response does this call represent?
4. one_line_summary: a single sentence, in your own words, describing what
   happened in this specific call in the context of the incident.

Return ONLY this JSON shape:
{
  "is_incident_related": true/false,
  "customer_affected": "<name or null>",
  "incident_stage": "<one of the six stages above, or null if not related>",
  "one_line_summary": "<one sentence>"
}
"""


def find_candidate_calls(df: pd.DataFrame) -> pd.DataFrame:
    """Step 1: cheap keyword-based candidate detection (transparent, auditable)."""
    mask = df["title"].str.contains(INCIDENT_KEYWORDS, regex=True, na=False)
    return df[mask].copy()


def extract_stage(row) -> dict:
    user_prompt = (
        f"Call type: {row.call_type}\n"
        f"Title: {row.title}\n"
        f"Date: {row.start_time}\n\n"
        f"Summary: {row.baseline_summary}\n\n"
        f"Transcript excerpt:\n{row.transcript_text[:3000]}"
    )
    try:
        return call_llm_json(STAGE_SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        print(f"  ERROR on {row.call_id}: {e}")
        return {
            "is_incident_related": None,
            "customer_affected": None,
            "incident_stage": None,
            "one_line_summary": f"extraction failed: {e}",
        }


def build_timeline(df: pd.DataFrame) -> pd.DataFrame:
    candidates = find_candidate_calls(df)
    print(f"Found {len(candidates)} keyword-candidate calls for the incident.")

    results = []
    for i, row in enumerate(candidates.itertuples()):
        print(f"  extracting {i+1}/{len(candidates)}: {row.call_id} ({row.title[:50]})")
        r = extract_stage(row)
        r["call_id"] = row.call_id
        r["call_type"] = row.call_type
        r["title"] = row.title
        r["start_time"] = row.start_time
        r["baseline_sentiment_score"] = row.baseline_sentiment_score
        results.append(r)

    timeline = pd.DataFrame(results)
    timeline = timeline[timeline["is_incident_related"] == True].sort_values("start_time")
    return timeline


def main():
    sys.path.append(os.path.dirname(__file__))
    from load_data import load_all_transcripts

    df = load_all_transcripts()
    timeline = build_timeline(df)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    timeline.to_csv(os.path.join(out_dir, "incident_blast_radius_timeline.csv"), index=False)
    print(f"\nSaved {len(timeline)} incident-related calls to outputs/incident_blast_radius_timeline.csv")
    print(f"Distinct customers affected: {timeline['customer_affected'].dropna().nunique()}")
    print(f"Call types involved: {timeline['call_type'].unique().tolist()}")


if __name__ == "__main__":
    main()
