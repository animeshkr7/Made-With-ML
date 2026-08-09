# Repository Mapping

This document maps every local directory inside `c:\Users\aks\Documents\Github\career\` to its GitHub remote.

> **Root Repo:** `c:\Users\aks\Documents\Github\career` → **https://github.com/animeshkr7/Made-With-ML.git** (branch: `dev`)

---

## Directories with their OWN separate GitHub Repo

These are **independent git repos** nested inside the root folder (like submodules, but without `.gitmodules`):

| Local Directory | GitHub Remote | Owner |
|---|---|---|
| `ats-scrapers/` | https://github.com/kalil0321/ats-scrapers | kalil0321 (external/forked) |
| `email_ceator/` | https://github.com/animeshkr7/email-creator-api | animeshkr7 |
| `monitor/` | https://github.com/animeshkr7/monitor | animeshkr7 |

> **Warning:** `ats-scrapers` points to an **external user's repo** (kalil0321). Any changes you push there will go to their fork. Consider forking it to your own GitHub account.

---

## Directories that are part of the Root Repo (Made-With-ML)

These directories **do NOT have their own remote** — they are tracked inside `animeshkr7/Made-With-ML`:

| Local Directory | Part of Root Repo |
|---|---|
| `email_processor/` | Yes |
| `supabase_sync/` | Yes |
| `job_application_tracker/` | Yes |
| `job_url_outreach_workflow/` | Yes |
| `job_scanner/` | Yes |
| `email_drafting/` | Yes |
| `company_specific/` | Yes |
| `supabase_api_demo/` | Yes |
| `research/` | Yes |
| `sysDesign/` | Yes |

---

## Filter Logic Files (What We Just Built)

| File | Repo | Push Destination |
|---|---|---|
| `email_processor/linkedin_monitor/filter_config.json` | Made-With-ML | animeshkr7/Made-With-ML |
| `email_processor/linkedin_monitor/filter_utils.py` | Made-With-ML | animeshkr7/Made-With-ML |
| `email_processor/post_processor/send_notification.py` | Made-With-ML | animeshkr7/Made-With-ML |
| `email_processor/post_processor/llm_post_filter.py` | Made-With-ML | animeshkr7/Made-With-ML |
| `email_ceator/main.py` (DATA toggle) | email-creator-api | animeshkr7/email-creator-api |
