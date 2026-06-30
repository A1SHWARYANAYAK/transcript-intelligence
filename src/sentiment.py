"""
sentiment.py
------------
Task 2: sentiment analysis across call types, with trend identification.

APPROACH:
  The dataset already ships with TWO levels of pre-existing sentiment:
    1. Call-level: `overallSentiment` (categorical: very-negative ...
       very-positive) and `sentimentScore` (numeric 1-5) in summary.json
    2. Sentence-level: `sentimentType` per line in transcript.json

  We treat both as a BASELINE, not ground truth, because:
    - We don't know what produced them (could be a different/older model,
      different prompt, different scale anchoring) -- "mixed-positive"
      from an unknown system isn't independently verifiable.
    - For an interview exercise, re-deriving sentiment ourselves and then
      comparing against the baseline is more defensible and demonstrates
      our own judgment, rather than just repackaging numbers that were
      handed to us.

  Our own pipeline:
    - We compute a CALL-LEVEL sentiment score (-1 to +1) using an LLM,
      explicitly distinguishing three dimensions that matter more to a
      business audience than generic positive/negative:
        a) customer_sentiment: how does the CUSTOMER/non-Aegis party feel
           (only meaningful for external/support calls; null for internal)
        b) urgency: how time-pressured/escalated does this call feel
        c) resolution_status: was the issue/topic resolved, open, or
           escalated further by the end of the call
    - This is richer than a single polarity score and maps directly to
      what a support/sales leader would actually want to triage on.

  We then aggregate by call_type and by week to surface trends, and
  explicitly compare our scores against the baseline `sentimentScore`
  for a validation check (correlation + spot-check of biggest disagreements).
"""

import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(__file__))
from llm_client import call_llm_json

SENTIMENT_SYSTEM_PROMPT = """You are analyzing a call transcript from a B2B
cybersecurity/compliance SaaS company (Aegis Cloud). Calls are one of three
types: internal (all Aegis employees), external (Aegis + customer, e.g.
sales/account management conversations), or support (customer support case).

Score the call on these dimensions:

1. customer_sentiment: how does the CUSTOMER (non-Aegis party) feel about
   Aegis/the product/the situation by the END of the call, from -1.0 (very
   negative/angry/at risk of churning) to +1.0 (very positive/delighted).
   For INTERNAL calls with no customer present, set this to null and instead
   reason about overall team sentiment in the rationale.

2. urgency: 0.0 (routine, no time pressure) to 1.0 (critical, drop-everything
   urgency -- e.g. active outage, threatened churn, escalation to leadership).

3. resolution_status: one of "resolved", "open_with_plan", "open_unresolved",
   "escalated". Did the call end with the core issue/topic settled, settled
   with a clear next step, left hanging, or pushed up/out to someone else?

4. trajectory: one of "improving", "stable", "deteriorating" -- comparing
   sentiment at the START of the call vs. the END of the call.

Return ONLY this JSON shape:
{
  "customer_sentiment": <float -1 to 1, or null>,
  "urgency": <float 0 to 1>,
  "resolution_status": "<one of the four values above>",
  "trajectory": "<one of the three values above>",
  "rationale": "<one sentence, specific to this call>"
}
"""


def score_call(row) -> dict:
    user_prompt = (
        f"Call type: {row.call_type}\n"
        f"Title: {row.title}\n\n"
        f"Transcript:\n{row.transcript_text[:6000]}"
    )
    try:
        return call_llm_json(SENTIMENT_SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        print(f"  ERROR scoring {row.call_id}: {e}")
        return {
            "customer_sentiment": None,
            "urgency": None,
            "resolution_status": "UNKNOWN",
            "trajectory": "UNKNOWN",
            "rationale": f"scoring failed: {e}",
        }


def score_all(df: pd.DataFrame) -> pd.DataFrame:
    results = []
    for i, row in enumerate(df.itertuples()):
        print(f"  scoring {i+1}/{len(df)}: {row.call_id} ({row.call_type})")
        r = score_call(row)
        r["call_id"] = row.call_id
        results.append(r)
    return pd.DataFrame(results)


def main():
    sys.path.append(os.path.dirname(__file__))
    from load_data import load_all_transcripts

    df = load_all_transcripts()
    print("Scoring sentiment for all 100 transcripts...")
    results = score_all(df)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    results.to_csv(os.path.join(out_dir, "sentiment_results.csv"), index=False)
    print(f"Saved to outputs/sentiment_results.csv")


if __name__ == "__main__":
    main()
