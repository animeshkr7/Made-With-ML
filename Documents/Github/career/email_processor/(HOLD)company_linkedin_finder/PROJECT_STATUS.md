# Company LinkedIn Connection Automation - Project Status

## What Are We Pursuing?
The goal of this sub-project is to fully automate targeted networking on LinkedIn. Given a company name, the script aims to navigate to that company's LinkedIn page, navigate to their "People" section, and autonomously send connection requests to employees based on a strict priority list and hard quotas.

Our target limits per run are:
- **Overall Maximum:** 7 total connection requests.
- **Priority 1:** AI (Max 3)
- **Priority 2:** Lead (Max 2)
- **Priority 3:** Python (Max 2)
- **Priority 4:** Manager (Max 3)
- **Priority 5:** HR (Max 2)
- **Priority 6:** Random (Sweeps up any remaining balance to hit 7)

## Where Are We Currently?
- **Authentication Solved:** We successfully linked this script to your `linkedin_monitor`'s `state.json` file. It launches completely logged into your active LinkedIn session.
- **Bot Detection Bypassed:** We avoided Google's strict CAPTCHAs by using LinkedIn's internal search engine directly via a dynamically generated URL.
- **Core Logic Complete:** The `find_company_linkedin.py` script is fully operational. It can parse through the priority list, handle dynamic page loading, locate the correct "Connect" buttons, skip profiles requiring email verification, and execute the connection request modal while perfectly tracking the quota limits. 

## What's Left & Why Is It On Hold?
- **Reason for Hold:** During our live testing, you hit the hard **"You've reached the weekly invitation limit"** restriction enforced by LinkedIn. Continuing to send requests (or failing to bypass this warning repeatedly) can flag your account as a bot or lead to a temporary ban. Thus, the project is paused for your account's safety until the limit resets.
- **What's Left for the Future:**
  1. **Limit Detection:** We need to add explicit code to read the "weekly limit reached" modal and immediately halt the script gracefully to prevent endless errors or account flags.
  2. **Batch Processing:** We currently pass one company (like "cisco") to the script. Later, we can hook this up to read a list of target companies from a file.
  3. **Task Integration:** Once safe to resume, we can add this workflow to your `.bat` files or Task Scheduler so it runs completely hands-off.
