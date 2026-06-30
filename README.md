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
  01_categorization.ipynb      Task 1 walkthrough + charts + reasoning
  02_sentiment.ipynb           Task 2 walkthrough + trend charts + reasoning
  03_bonus_insights.ipynb      Bonus insight walkthrough + 2 more ideas (described, not built)
outputs/                       Generated CSVs, charts, and the taxonomy
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
  sample, human-reviewed/locked, then applied as a fixed taxonomy to all
  100 transcripts with structured JSON output + rationale per call.
- **Sentiment** is re-derived independently (not just reusing the
  dataset's pre-existing `sentimentScore`), scored on customer sentiment,
  urgency, and resolution status — then compared against the baseline as
  a validation check.
- **Bonus insight** (fully built): an Incident Blast Radius Timeline
  tracing one real outage across internal/external/support calls,
  showing cross-functional cost that's invisible in any single team's
  view of the data.
