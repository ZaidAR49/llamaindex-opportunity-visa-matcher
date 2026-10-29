# Opportunity & Visa Matcher

An intelligent decision-support system that evaluates candidate profiles against international opportunity specifications and cross-references live immigration regulations to assess eligibility and fit.

---

## Overview

Applying for international roles requires evaluating both skill alignment and legal work authorization. The **Opportunity & Visa Matcher** automates this by:

1. **Ingesting Candidate & Opportunity Documents**: Parses local CV and opportunity specification PDFs.
2. **Retrieving Live Immigration Policies**: Fetches up-to-date visa regulations and entry requirements directly from target web URLs.
3. **Semantic Indexing & Retrieval**: Combines all document sources into a unified vector index using **LlamaIndex** to extract relevant policy clauses.
4. **Structured Multi-Dimensional Evaluation**: Delivers an actionable evaluation report featuring requirement matching tables, risk flags, pros & cons, immigration legal analysis, and an overall hiring verdict.

---

## Key Features

* **Multi-Source RAG Pipeline**: Integrates unstructured local PDF documents with live web scraping into a unified vector store.
* **Deep Requirement Auditing**: Generates a 4-column markdown matrix matching each job requirement against the candidate's background, highlighting critical blockers (`🚩`).
* **Immigration & Visa Verification**: Cross-references legal regulations from official portals or embassy resources to verify work authorization feasibility.
* **Bilingual Experience (English / العربية)**: Complete UI and report generation support in English and Arabic, featuring dynamic Right-to-Left (RTL) rendering.
* **Interactive Web Dashboard**: Streamlit interface with card-based section rendering, executive KPI summary ribbon, 1-click clipboard copy, and Markdown export.
* **CLI Automation**: Command-line interface for headless evaluation and rapid testing.

---

## Quickstart

### Prerequisites

* Python 3.10+ (Python 3.11 recommended)
* [`uv`](https://github.com/astral-sh/uv) package manager
* An API key for **OpenRouter** (e.g. DeepSeek) or **Google Gemini**

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/opportunity-visa-matcher.git
   cd opportunity-visa-matcher
   ```

2. **Configure environment variables:**
   Copy `.env.example` to `.env` and supply your API key:
   ```env
   # Choose OpenRouter or Google Gemini:
   OPENROUTER_API_KEY=your_openrouter_api_key
   OPENROUTER_MODEL=deepseek/deepseek-chat

   # Optional fallback or direct Gemini provider:
   GEMINI_API_KEY=your_gemini_api_key

   # Target immigration policy URL:
   VISA_RULES_URL=https://en.wikipedia.org/wiki/Visa_policy_of_the_Schengen_Area
   ```

3. **Install dependencies:**
   ```bash
   uv sync
   ```

---

## Usage

### 1. Web Application (Streamlit)

Launch the dashboard:
```bash
uv run python -m llamaindex.main
```
*(Or directly: `uv run streamlit run src/llamaindex/app.py`)*

Open your browser at `http://localhost:8501`:
* Upload a Candidate CV (PDF) and an Opportunity Specification (PDF), or check **"✨ Use built-in sample files"** for an instant test.
* Toggle the UI language or select the desired report output language (English or Arabic) from the sidebar.
* Click **"🚀 Analyze Match & Check Visa"** to generate the report.
* Toggle between **"🃏 Colorful Cards"** and **"📄 Full Text"**, copy the output to your clipboard, or download the Markdown report.

### 2. Command Line Interface (CLI)

Run automated evaluations directly from the terminal:

* **English Report:**
  ```bash
  uv run python -m llamaindex.main --cli
  ```

* **Arabic Report (تقرير باللغة العربية):**
  ```bash
  uv run python -m llamaindex.main --cli --lang ar
  ```

---

## Project Structure

```
LlamaIndex/
├── .env                       # Environment configuration (API keys, URLs)
├── .env.example               # Template for environment configuration
├── pyproject.toml             # Project metadata and dependencies (managed by uv)
├── sample_data/               # Sample evaluation documents
│   ├── sample_cv.pdf          # Sample candidate CV
│   └── sample_opportunity.pdf # Sample international opportunity specification
└── src/
    └── llamaindex/
        ├── __init__.py        # Package initialization
        ├── matcher.py         # Core LlamaIndex engine (PDF parsing, web scraper, RAG pipeline)
        ├── app.py             # Streamlit web application & visualization
        └── main.py            # Entry point dispatcher (Web and CLI)
```
