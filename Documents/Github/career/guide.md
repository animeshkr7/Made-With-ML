# LinkedIn Outreach & Monitoring Services Guide

This guide explains how to run all three LinkedIn outreach and monitoring services directly from the root `career` repository folder (`C:\Users\aks\Documents\Github\career`).

---

## 🛠️ Requirements & Setup

- Ensure `.env` is configured in `email_processor/.env` (and repository root) with your `GROQ_API_KEY`, `LINKEDIN_EMAIL`, and `APP_PASSWORD`.
- Active session state is automatically loaded from `email_processor/linkedin_monitor/state.json`.

---

## 1️⃣ Service 1: Company Outreach Service

Use this service when you have a **Company Name** or **LinkedIn Company URL**.

```powershell
# By Company Name
& "C:\Users\aks\.pyenv\pyenv-win\versions\3.10.10\python.exe" email_processor/company_outreach_service/workflow.py "Colgate Palmolive"

# By LinkedIn Company URL
& "C:\Users\aks\.pyenv\pyenv-win\versions\3.10.10\python.exe" email_processor/company_outreach_service/workflow.py "https://www.linkedin.com/company/colgate-palmolive/"
```

---

## 2️⃣ Service 2: Job Link Outreach Service

Use this service when you have a **Careers Page / Job Posting URL**.

```powershell
& "C:\Users\aks\.pyenv\pyenv-win\versions\3.10.10\python.exe" email_processor/job_link_outreach_service/workflow.py "https://jobs.colgate.com/job/Mumbai-Data-Scientist-MH/173498-en_GB/?feedId=430400"
```

---

## 3️⃣ Service 3: Connection Acceptance Monitor Service

Use this service to check if pending connection requests have been accepted on LinkedIn.

### Features:
- Scans all outreach JSON reports (`company_outreach_service/*.json`, `job_link_outreach_service/*.json`, `monitor/input/*.json`).
- Checks if the connection request has been accepted (button changed to **`Message`**).
- Generates a custom referral draft message for accepted connections.
- Emails you (`animeshkr7@gmail.com`) with the **Profile URL, Person Name, Company**, and **Ready-to-Send Draft Message**.
- Sets `"notification_sent": true` in the JSON report so duplicate emails are **never** sent on future runs.

### Command (Run from `career/` root):

```powershell
& "C:\Users\aks\.pyenv\pyenv-win\versions\3.10.10\python.exe" email_processor/connection_monitor/workflow.py
```
