# Transcript Intelligence

> AI-powered enterprise transcript analytics platform that automatically categorizes conversations, analyzes sentiment, and extracts cross-functional business insights using Large Language Models (LLMs).

Built as an Applied AI Engineering project demonstrating LLM orchestration, structured outputs, enterprise analytics, and product-focused insight generation.

---

## 🚀 Highlights

- Hybrid **LLM + Human-Reviewed Taxonomy** topic classification
- Multi-dimensional sentiment analysis beyond simple positive/negative labels
- Cross-functional incident timeline reconstruction
- Executive-ready visualizations and business insights
- Modular, reproducible AI pipeline with clean project structure

---

# Business Problem

Enterprise organizations generate thousands of meeting transcripts every month across Customer Support, Sales, Product, and Engineering teams.

While these conversations contain valuable business intelligence, manually reviewing them is:

- Time-consuming
- Expensive
- Difficult to scale
- Inconsistent across reviewers

This project demonstrates how an AI-powered transcript intelligence platform can automatically transform unstructured conversations into actionable insights for business leaders.

---

# Architecture

> **Replace the image below with your architecture diagram (assets/architecture.png).**

<p align="center">
<img src="assets/architecture.png" width="900">
</p>

The pipeline follows a modular architecture:

```
Raw Transcripts
        │
        ▼
Data Loading & Cleaning
        │
        ▼
Call Type Detection
        │
        ▼
Hybrid Topic Categorization
        │
        ▼
Sentiment Analysis
        │
        ▼
Business Insight Generation
        │
        ▼
Visualizations & Reports
```

---

# Repository Structure

```
.
├── assets/
│   └── architecture.png
│
├── data/
│   └── raw_transcripts/
│
├── notebooks/
│   ├── 00_data_exploration.ipynb
│   ├── 01_categorization.ipynb
│   ├── 02_sentiment.ipynb
│   └── 03_bonus_insights.ipynb
│
├── outputs/
│   ├── figures/
│   ├── categorization_results.csv
│   ├── sentiment_results.csv
│   ├── incident_blast_radius_timeline.csv
│   └── taxonomy_FINAL.json
│
├── src/
│   ├── load_data.py
│   ├── llm_client.py
│   ├── categorize.py
│   ├── sentiment.py
│   └── outage_blast_radius.py
│
├── requirements.txt
├── .env.example
└── README.md
```

---

# Dataset

The project uses approximately **100 enterprise SaaS call transcripts** provided as part of the interview assignment.

The dataset contains conversations across:

- Customer Support
- External Customer Calls
- Internal Engineering & Product Meetings

The original dataset is preserved unchanged under:

```
data/raw_transcripts/
```

---

# Installation

Clone the repository

```bash
git clone <repository-url>

cd transcript-intelligence
```

Install dependencies

```bash
pip install -r requirements.txt
```

Configure environment variables

```bash
cp .env.example .env
```

Add your OpenRouter API key

```
OPENROUTER_API_KEY=YOUR_API_KEY
```

---

# Running the Project

## Topic Discovery

Generate an initial taxonomy using a representative transcript sample.

```bash
python src/categorize.py
```

---

## Review Taxonomy

Review

```
outputs/discovered_taxonomy_RAW.json
```

Finalize it as

```
outputs/taxonomy_FINAL.json
```

---

## Classify All Transcripts

```bash
python src/categorize.py --classify
```

Outputs

- Category
- Confidence
- Structured reasoning
- Supporting evidence

---

## Run Sentiment Analysis

```bash
python src/sentiment.py
```

Outputs

- Customer sentiment
- Urgency
- Resolution status
- Sentiment trajectory

---

## Generate Cross-functional Incident Timeline

```bash
python src/outage_blast_radius.py
```

---

# Methodology

## 1. Call Type Detection

Since call types were not explicitly available in the raw dataset, they were derived using a transparent heuristic based on:

- Meeting titles
- Participants
- Domains
- Metadata

Final distribution:

| Call Type | Count |
|-----------|------:|
| External | 43 |
| Internal | 30 |
| Support | 27 |

---

## 2. Hybrid Topic Categorization

A hybrid approach was chosen to balance flexibility and consistency.

### Phase 1

An LLM discovers candidate business topics from a stratified sample.

### Phase 2

The taxonomy is manually reviewed to merge overlapping categories and improve consistency.

### Phase 3

Every transcript is classified against the locked taxonomy using structured JSON outputs.

This approach avoids inconsistent labels while preserving the flexibility of LLM-based discovery.

---

## 3. Multi-dimensional Sentiment Analysis

Rather than relying on the provided sentiment field, sentiment is independently re-derived.

Each transcript is evaluated across:

- Overall sentiment
- Customer emotion
- Business urgency
- Resolution status
- Conversation trajectory

The resulting scores are compared against the original dataset as a validation exercise.

---

## 4. Cross-functional Incident Analysis

The pipeline reconstructs an enterprise outage by connecting conversations across multiple teams.

Instead of viewing meetings independently, the analysis demonstrates how a single production incident propagates across:

- Engineering
- Customer Support
- Customer Success
- Account Management

This provides organization-wide visibility into operational impact.

---

# Engineering Decisions

| Problem | Decision | Why |
|----------|----------|-----|
| Topic Classification | Hybrid LLM + Locked Taxonomy | Flexible yet reproducible |
| Sentiment | Independent re-scoring | Validate against provided baseline |
| Pipeline | Modular Python scripts | Maintainability & testing |
| Outputs | CSV + Figures | Easy inspection |
| Analysis | Jupyter notebooks | Reproducible experimentation |

---

# Key Findings

## Platform Reliability Impacts Every Team

Platform Reliability & Outages was the only category consistently observed across all three call types, highlighting that infrastructure incidents create organization-wide operational impact.

---

## Resolution Rates Differ Significantly

| Call Type | Resolved During Call |
|-----------|--------------------:|
| Internal | 33% |
| Support | 7.4% |
| External | 2.3% |

Conversation volume alone is therefore not a reliable indicator of operational effectiveness.

---

## Most Conversations Improve

Conversation trajectory:

- Improving → 67%
- Stable → 31%
- Deteriorating → 2%

Interestingly, the only deteriorating conversations occurred during internal engineering discussions while investigating an active production outage.

---

# Visualizations

## Category Distribution

<img src="outputs/figures/category_distribution.png" width="700">

---

## Categories by Call Type

<img src="outputs/figures/category_by_call_type.png" width="700">

---

## Sentiment Trends

<img src="outputs/figures/sentiment_over_time.png" width="700">

---

## Resolution Status

<img src="outputs/figures/resolution_status_by_calltype.png" width="700">

---

## Incident Blast Radius Timeline

<img src="outputs/figures/incident_blast_radius_timeline.png" width="700">

---

# Business Impact

This pipeline demonstrates how AI can transform enterprise conversations into actionable intelligence.

Potential applications include:

- Automated transcript categorization
- Customer pain-point discovery
- Feature request mining
- Engineering incident tracking
- Customer churn detection
- Executive dashboards
- Product adoption analytics
- Sales opportunity discovery

---

# Limitations

- Taxonomy still benefits from periodic human review.
- LLM inference introduces latency and API costs.
- Call type detection depends on metadata quality.
- Classification accuracy depends on transcript completeness.

---

# Future Enhancements

Potential next steps include:

- LangGraph-powered multi-agent workflow
- MCP tool integrations
- Retrieval-Augmented Generation (RAG)
- Human-in-the-loop taxonomy approval
- Streaming transcript ingestion
- Continuous evaluation pipelines
- Cost-aware model routing
- Interactive dashboard

---

# Technologies Used

### Languages

- Python

### AI

- Claude Sonnet 4.5
- OpenRouter API
- Structured JSON Outputs

### Data

- Pandas
- NumPy

### Visualization

- Matplotlib

### Development

- Jupyter Notebook
- python-dotenv

---

# Deliverables

This repository contains:

- AI processing pipeline
- Jupyter notebooks
- Source code
- Generated outputs
- Business insights
- Executive-ready visualizations

---

# Acknowledgements

This project was developed as part of an Applied AI Engineering assignment and is intended solely for evaluation and portfolio purposes.
