# LinkedIn Message Request & Referral Workflows

This folder contains modular tools to help you track job applications and automate LinkedIn outreach for referrals.

## Architecture

The codebase is modularized for reusability:
- `modules/llm.py`: Handles interactions with Groq (Llama-3.1-8b) to parse job descriptions and draft custom referral messages.
- `modules/scraper.py`: A generic Playwright utility to fetch the raw text of a job posting URL.
- `modules/linkedin_core.py`: Contains core LinkedIn automation functions (login with session states, OTP handling via email, searching for exact companies, and finding 1st-degree connections).

## Main Workflows

### 1. Generate Referral Drafts to JSON
**Script:** `workflow_generate_drafts.py`

This workflow takes a job URL, uses LLMs to extract the company and job title, searches LinkedIn for up to 5 of your 1st-degree connections at that company, and drafts a custom referral message for each. It saves the output locally in a JSON file without actually opening LinkedIn chats.

**Usage:**
```powershell
python workflow_generate_drafts.py "https://jobs.lever.co/example/12345"
```
**Output:** Creates a file named like `200726-EXAMPLE_COMPANY.json` containing:
- `job_link`
- `connection_profile_url`
- `draft_message`
- `date`

### 2. Job URL Tracker API (Legacy/Alternative)
**Script:** `main.py`

A FastAPI application that connects to Supabase to store and track job URLs you've applied to or are interested in.
- Start the server: `uvicorn main:app --reload --port 8001`
- The UI is served statically on the root URL.

### 3. Automated LinkedIn Chat Drafter (Legacy)
**Script:** `job_to_company_linkedin.py`

An older workflow that not only generates the drafts but physically opens your LinkedIn connection's chat box and types the message in for you.

## Setup Requirements

1. Ensure `.env` is configured at the root of `email_processor` with:
   - `GROQ_API_KEY`
   - `LINKEDIN_EMAIL`
   - `LINKEDIN_PASSWORD`
   - `APP_PASSWORD` (For OTP handling via Gmail)
   - `SUPABASE_URL` & `SUPABASE_KEY` (if using the tracker API)
2. Ensure Playwright is installed (`pip install playwright` and `playwright install chromium`).
3. If running the LinkedIn automations for the first time, you may need to run the `linkedin_monitor/setup_auth.py` script to generate a `state.json` file.
