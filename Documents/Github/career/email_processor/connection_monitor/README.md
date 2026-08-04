# LinkedIn Connection Acceptance Monitor Service

A dedicated monitoring service inside `email_processor/connection_monitor` that tracks sent LinkedIn connection requests, detects accepted connections, drafts custom referral messages, sends email alerts, and flags profiles to prevent duplicate notifications.

## Features

1. **Automatic Status Inspection**:
   - Inspects profile URLs from all outreach JSON reports (`company_outreach_service/*.json`, `job_link_outreach_service/*.json`, `monitor/input/*.json`).
   - Checks if the action button has changed to **`Message`** (1st-degree connection accepted).

2. **Deduplication & Flagging**:
   - Updates each profile entry in the JSON file with `"status": "Accepted"` and `"notification_sent": true`.
   - Ensures that profiles already notified are **never** re-alerted on future runs.

3. **Rich Email Notification**:
   - Emails `animeshkr7@gmail.com` with:
     - Person's Name & LinkedIn Profile URL
     - Company Name
     - Customized, ready-to-send Referral Draft Message

## Usage

Run with `python.exe` directly from the repository root:

```powershell
cd C:\Users\aks\Documents\Github\career
& "C:\Users\aks\.pyenv\pyenv-win\versions\3.10.10\python.exe" email_processor/connection_monitor/workflow.py
```
