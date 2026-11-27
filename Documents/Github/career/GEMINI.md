# Project Steering Guidelines

## 1. Scraper Date Handling & Delta Caching Protocol (MANDATORY)

Whenever implementing, debugging, or auditing company career scrapers for the daily job monitor:

1. **Check for Hidden APIs first**:
   - Investigate if the portal has an underlying JSON API, embedded state (`__NEXT_DATA__`), internal ATS endpoint, or RSS feed that contains posting timestamps.
   - Always verify if dates can be extracted natively before assuming they don't exist.

2. **If no dates exist, use Cisco-like Delta Caching**:
   - Do **NOT** leave jobs with `posted_at = None` (which causes them to always be filtered out from the yesterday report).
   - Follow the standard protocol documented in [`knowledge/cisco_caching.md`](file:///C:/Users/aks/Documents/Github/career/knowledge/cisco_caching.md).
   - Use persistent `.cache.json` files to store seen job IDs, detect new postings (delta), and timestamp newly discovered jobs as "yesterday".
   - Ensure `ats_id` is unique and stable (e.g. from job ID or URL tail, never a loop index).

See full implementation specifications and examples in:
👉 [`knowledge/cisco_caching.md`](file:///C:/Users/aks/Documents/Github/career/knowledge/cisco_caching.md)

---

## 2. Keywords & Filtering Rules
- Maintain keyword exclusions in [`monitor/src/filter.py`](file:///C:/Users/aks/Documents/Github/career/monitor/src/filter.py) with clean syntax and regex word boundaries.
- When modifying targets, maintain synchronization across `monitor/input/targets.json` and `monitor/input/new_targets.json`.

---

## 3. Specific Portal Configurations & Gotchas
- **Priceline:** Always use the dedicated tenant `https://priceline.wd1.myworkdayjobs.com/Priceline` (never the Booking Holdings `booking.wd3` instance). See [`knowledge/priceline.md`](file:///C:/Users/aks/Documents/Github/career/knowledge/priceline.md).

---

## 4. Career URL Discovery & 7-Day Validation Protocol
- Always verify that a discovered career URL is active before adding to targets.
- **Portals with Native Dates:** Must have $\ge 1$ job posted/updated in the past 7 days.
- **Portals without Native Dates:** Follow the 7-day delta validation process (Day 0 snapshot $\rightarrow$ daily audit for new job IDs $\rightarrow$ verify if delta found within 7 days, else flag as stale).
- **Regional Preference:** Prefer India-dedicated portal if separate regional sites exist.
- **Mandatory Chat Validation Reporting:** Whenever validating or adding URLs, **always present the full validation results in the chat response**. Include:
  - Scraper execution status & API response summary.
  - Total active jobs fetched & count of jobs with valid posting dates.
  - Recency breakdown (jobs posted in the past 24 hours vs last 7 days).
  - Regional / India job count and concrete sample listings (Title, Location, Posting Date, URL).

See full validation guidelines in:
👉 [`knowledge/working_career_url.md`](file:///C:/Users/aks/Documents/Github/career/knowledge/working_career_url.md)

---

## 5. Company Discovery & Eligibility Criteria Protocol (MANDATORY)

Whenever asked to search, suggest, or discover new target companies:

1. **Target Persona & Hiring Criteria:**
   - **Experience Level:** 1–2 Years of Experience (Early-Career / SDE-1 / MLE-1 / Junior).
   - **Target Roles:** Machine Learning Engineer, Data Scientist, AI / Agentic Engineer, MLOps, Data Platform / Distributed Systems.
   - **Compensation Benchmark:** Around **₹15+ LPA** in India.

2. **Deduplication & Scope Rule:**
   - **Default Scope:** Must be **entirely new** — present in **neither** `monitor/input/new_targets.json` **nor** `monitor/input/targets.json`.
   - If ambiguous, clarify with the user whether they want *entirely new* companies or companies that exist in old `targets.json` but are missing from `new_targets.json`.

3. **Validation & Synchronization:**
   - Always verify the portal/ATS URL using the **7-Day Validation Protocol** (Section 4) before proposing or adding.
   - When adding, maintain synchronization across `monitor/input/targets.json` and `monitor/input/new_targets.json`.

---

## 6. Skill Logging & Git Isolation Protocol (MANDATORY)

Whenever running or authoring skills that track job applications, post evaluations, or outreach runs:

1. **Dedicated Local Folder per Skill:**
   - All run logs (`.md` or `.json`) must be saved in a dedicated `logs/` directory inside each respective skill folder:
     - Workday applications $\rightarrow$ `.agents/skills/workday-auto-apply/logs/workday_applied.md`
     - Instahyre applications $\rightarrow$ `.agents/skills/instahyre-auto-apply/logs/instahyre_applied.md`
     - LinkedIn applications $\rightarrow$ `.agents/skills/linkedin-job-hunt/logs/applied_jobs.md`
   - Never store application logs in the repository root or shared global directories.

2. **Strict Git Exclusion:**
   - **Logs must NEVER be committed or pushed to Git.**
   - All `logs/` and `**/logs/` directories must be ignored in `.gitignore` across both the parent repository and `.agents/skills/`.
   - Never stage (`git add`) any log files or tracking history.




