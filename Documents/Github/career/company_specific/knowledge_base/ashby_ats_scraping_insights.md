# ATS Scraping Insights: Ashby

This document details the methodology used to integrate the Ashby ATS into our scraping pipeline, discovered during the integration of Aplazo.

## 1. The Ashby Architecture

Unlike Keka, which embeds a complex Javascript payload into the career site that then fetches jobs, Ashby provides a very clean, standardized, and public REST API for all companies that use their platform. 

When a company (like Aplazo) uses Ashby, their job board is typically hosted at or redirects to:
`https://jobs.ashbyhq.com/{company_id}`

## 2. Discovering the API

By inspecting the Network tab when visiting `jobs.ashbyhq.com/aplazo`, we found that Ashby makes a direct `GET` request to a public API endpoint to populate the UI.

**The Endpoint:**
`https://api.ashbyhq.com/posting-api/job-board/{company_id}`

This endpoint does not require authentication, CSRF tokens, or complex session cookies. However, it **does** require a standard `User-Agent` header (e.g., `Mozilla/5.0`). If you attempt to hit it with `urllib`'s default Python user-agent, it will return a `403 Forbidden` error.

## 3. The Extraction Logic

The API returns a JSON object with a `jobs` array.

**Schema Mapping for Standardization:**
To feed this into `main.py`, we map Ashby's schema to our unified schema:
*   `title` -> Maps directly to `job["title"]`.
*   `location` -> Ashby provides a primary `location` string. If it's missing, it often provides an array under `secondaryLocations`. We join `locationName` from this array.
*   `published_at` -> Ashby doesn't have a single consistent date field. It can appear as `publishedAt`, `createdAt`, or `postedAt`. We fall back through these three to ensure we always extract a valid timestamp.
*   `url` -> Maps to `jobUrl` or `applyUrl`.

## 4. Implementation Example

```python
import urllib.request
import json

def fetch_ashby_jobs(company_id):
    api_url = f"https://api.ashbyhq.com/posting-api/job-board/{company_id}"
    
    # User-Agent is CRITICAL for Ashby to prevent 403 Forbidden
    req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    json_data = urllib.request.urlopen(req).read().decode('utf-8')
    raw_jobs = json.loads(json_data).get("jobs", [])
    
    return raw_jobs
```

## 5. Adding Future Ashby Companies
If a new company uses Ashby, you **do not** need to write a new parser. 
1. Simply extract their `{company_id}` from their URL (e.g., `jobs.ashbyhq.com/ramp` -> `ramp`).
2. Create a minimal wrapper in `src/companies/` that calls `fetch_ashby_jobs("{company_id}")`.
3. Register them in `registry.json` using `"base_ats": "ashby"`.
