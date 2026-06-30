# Transcript Intelligence 

Pipeline for categorizing, sentiment-scoring, and extracting cross-functional
insights from 100 B2B SaaS call transcripts (support, external, internal)
from a fictional cybersecurity/compliance company, "Aegis Cloud."

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your API key
cp .env.example .env
# edit .env and paste your OpenRouter key:
#   OPENROUTER_API_KEY=sk-or-v1-...
# (get one at https://openrouter.ai/keys -- works with any underlying
#  model; this project defaults to anthropic/claude-sonnet-4.5 via
#  OpenRouter, see src/llm_client.py to swap models)
```

## Project structure

```
data/raw_transcripts/        100 transcript folders (untouched, as provided)
src/
  load_data.py                loads + flattens all 100 transcripts into one DataFrame,
                               derives call_type (support/external/internal)
  llm_client.py                OpenRouter API wrapper (reads key from .env)
  categorize.py                Task 1: topic/theme categorization pipeline
  sentiment.py                 Task 2: sentiment analysis pipeline
  outage_blast_radius.py       Bonus insight: cross-functional incident timeline
notebooks/
  00_data_exploration.ipynb    Initial data profiling -- call type derivation, date range, customer mix
  01_categorization.ipynb      Task 1 walkthrough + charts + reasoning
  02_sentiment.ipynb           Task 2 walkthrough + trend charts + reasoning
  03_bonus_insights.ipynb      Bonus insight walkthrough + 2 more ideas (described, not built)
outputs/                       Generated CSVs, charts, and the final locked taxonomy
```

## Running the pipeline end to end

```bash
cd src

# Task 1: categorization (run discovery first, review/edit the taxonomy,
# then classify all 100)
python categorize.py                 # step 1: proposes taxonomy -> outputs/discovered_taxonomy_RAW.json
# review/edit, save final version as outputs/taxonomy_FINAL.json
python categorize.py --classify      # step 3: classifies all 100 transcripts

# Task 2: sentiment
python sentiment.py

# Bonus: incident blast-radius timeline
python outage_blast_radius.py
```

Or just open and run the notebooks in `notebooks/` in order — they call
the same `src/` modules and include the reasoning, validation against the
dataset's pre-existing baseline fields, and all charts.

## Key design decisions (see module docstrings for full reasoning)

- **Call type** isn't in the raw data — derived via a transparent
  title/domain heuristic (43 external / 30 internal / 27 support).
- **Categorization** is hybrid: LLM-proposed taxonomy from a stratified
  sample, then human-reviewed and locked down to 10 final categories
  (`outputs/taxonomy_FINAL.json`) before classifying all 100 transcripts
  against it with structured JSON output + per-call rationale. Two of the
  originally-proposed 12 categories were merged during review for being
  thin/overlapping (see the taxonomy file's `description` fields for the
  reasoning behind each merge).
- **Sentiment** is re-derived independently (not just reusing the
  dataset's pre-existing `sentimentScore`), scored on customer sentiment,
  urgency, resolution status, and trajectory — then compared against the
  baseline as a validation check (0.95 correlation; see
  `02_sentiment.ipynb` for an honest discussion of what that number does
  and doesn't prove).
- **Bonus insight** (fully built): an Incident Blast Radius Timeline
  tracing one real outage (a "Detect" pipeline failure, March 10-18 2026)
  across internal/external/support calls and 7 affected customer accounts,
  showing cross-functional cost that's invisible in any single team's
  view of the data.

## Notable findings

- "Platform Reliability & Outages" is the only category that shows up
  meaningfully across all three call types (25 of 100 calls), while every
  other category lives almost entirely within one call type -- reliability
  problems are the one thing that ripples through the whole organization.
- External and support calls almost never resolve on the call itself
  (2.3% and 7.4% respectively, vs. 33% for internal calls) -- ticket/call
  volume alone says nothing about whether issues actually get closed out.
- Call sentiment trajectory rarely worsens mid-call (67% improving, 31%
  stable, only 2% deteriorating) -- and both deteriorating calls were
  internal, technical-team calls discovering bad news in real time during
  the outage, not customer-facing calls.

## A bug worth mentioning

During the categorization run, one call failed classification with a JSON
parsing error ("Extra data") caused by the model occasionally appending
content after a complete JSON object. Fixed in `src/llm_client.py` by
scanning for the first balanced `{...}` block instead of naively parsing
the whole response, plus a retry before falling back to an `UNCLASSIFIED`
label. Left as a visible example of debugging a real pipeline failure
rather than only showing the clean final run.