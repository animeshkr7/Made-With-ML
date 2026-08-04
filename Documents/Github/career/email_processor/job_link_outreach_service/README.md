# Job Link Outreach Service

A wrapper service that accepts a **Careers Page / Job Posting URL**, scrapes and chunks the page content, uses Groq LLM (`llama-3.1-8b-instant`) to extract the target company name, and automatically hands off the company name to `company_outreach_service`.

## Architecture

1. `modules/job_scraper.py`: Fetches job posting HTML via HTTP/Playwright fallback and extracts the top text chunk (~3,500 chars).
2. `modules/llm_extractor.py`: Sends the text chunk to Groq LLM to extract structured JSON (`company_name`, `job_title`, `job_id`).
3. `workflow.py`: CLI entry point that orchestrates the scraping, extraction, and handoff to `company_outreach_service`.

## Usage

Run with `python.exe` (to avoid Windows `pyenv-win` batch shim issues with `?` URL parameters):

```powershell
cd C:\Users\aks\Documents\Github\career\email_processor\job_link_outreach_service
& "C:\Users\aks\.pyenv\pyenv-win\versions\3.10.10\python.exe" workflow.py "https://jobs.colgate.com/job/Mumbai-Data-Scientist-MH/173498-en_GB/?feedId=430400"
```
