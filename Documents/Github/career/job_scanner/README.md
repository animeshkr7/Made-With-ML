# 🎯 Intelligent Adaptive Career Page Job Scanner

An intelligent, self-adapting job scraping and classification system designed to scan any corporate career portal (dynamic or static), extract individual job postings, filter out roles posted on previous days, and isolate Machine Learning Engineering opportunities using local gating and advanced Groq LLM reasoning.

---

## 🏗️ Two-Stage Intelligent Architecture

Most modern corporate career sites are built on varying structures (e.g. static pages, dynamically loaded JS pages like React/Next.js, or standard systems like Greenhouse, Lever, and Workday) and rarely print the date posted on the landing page. To address this, the system implements a **Two-Stage Scanning Architecture**:

1. **Discovery (Stage 1)**:
   - Resilient static `requests` retrieval or automatic dynamic `Selenium` headless fallback.
   - Smart DOM parser that compresses raw HTML down to an optimized link map, eliminating context limits.
   - Discovery LLM call to extract all job posting URLs, titles, and locations.
   - Python-based Keyword Gating (`config.ML_KEYWORDS`) to discard non-ML roles immediately (minimizing API cost).

2. **Deep Verification & Recency (Stage 2)**:
   - For ML candidates, retrieves the specific job description page.
   - Extracts and sanitizes description blocks.
   - Verification LLM parses the exact posting date relative to today's date (handles text like *"Posted 2 hours ago"*, *"Yesterday"*, *"May 24"*).
   - Strict classifier filters out standard backend developers, web wrappers, product managers, or old listings based on the configured date window.

---

## 🛠️ Getting Started

### 1. Requirements
The system is built on Python 3.10+ and relies on the following libraries (pre-configured in the environment):
- `requests`
- `beautifulsoup4`
- `selenium`
- `webdriver-manager`
- `groq`
- `python-dotenv`

### 2. Configuration & API Credentials
The system automatically discovers your Groq API key from your existing environmental context:
- Sibling `.env` at `../email_drafting/.env`
- Sibling `.env` in the root workspace
- Local `job_scanner/.env` file

Ensure your `.env` contains:
```env
GROQ_API_KEY=your_groq_api_key_here
```

To configure default companies or ML keyword criteria, update [job_scanner/config.py](file:///c:/Users/aks/Documents/Github/career/job_scanner/config.py).

---

## 🚀 Execution Guide

Always execute commands from the `c:\Users\aks\Documents\Github\career` root directory.

### A. Batch Scan Default Boards (OpenAI, Cohere, Anthropic)
Run a complete scan across default boards (filters for jobs posted **today** and **yesterday** by default):
```powershell
python -m job_scanner.main
```

### B. Strictly Filter Today's Postings
To scan default sites keeping **only** postings made strictly today (Reference Date):
```powershell
python -m job_scanner.main --days 0
```

### C. Scan a Custom Career Board
To scan any specific URL (adaptive to Lever, Greenhouse, Workday, or custom layouts):
```powershell
python -m job_scanner.main --url "https://jobs.lever.co/mistral" --company "Mistral AI"
```

---

## 📊 Outputs & Reports

Every run compiles detailed statistics and writes formatted outputs to [job_scanner/reports/](file:///c:/Users/aks/Documents/Github/career/job_scanner/reports/):
1. **Markdown Summary Report** (`reports/ml_jobs_YYYY-MM-DD.md`): A human-readable dossier containing a summary scoreboard, dynamic tables of verified matches, detailed LLM fit/date analyses, and complete trace lists of rejected items.
2. **Structured JSON File** (`reports/ml_jobs_YYYY-MM-DD.json`): Raw structured dataset for downstream pipeline triggers or job alerts.
