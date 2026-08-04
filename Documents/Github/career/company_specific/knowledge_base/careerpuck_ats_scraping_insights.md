# ATS Scraping Insights: Careerpuck

This document details the methodology used to integrate the Careerpuck frontend ATS into our scraping pipeline, discovered during the integration of Avalara.

## 1. The Careerpuck Architecture

Careerpuck acts as a modern frontend wrapper around legacy ATS systems (like iCIMS). By using Careerpuck, companies expose a clean, modern UI for candidates, which in turn exposes a clean, public JSON API endpoint for us to scrape.

When a company uses Careerpuck, their job board URL typically redirects to or loads data from:
`https://app.careerpuck.com/job-board/{company_id}`

## 2. Discovering the API

By inspecting the Network tab when visiting `careers.avalara.com`, we observed that the page queries a public Careerpuck API endpoint to populate the UI.

**The Endpoint:**
`https://api.careerpuck.com/v1/public/job-boards/{company_id}`

This API is not paginated by default for Avalara (it returns all jobs in a single massive array).

## 3. The Extraction Logic

The API returns a JSON object where the jobs are contained in the `jobs` array.

**Schema Mapping for Standardization:**
*   `title` -> Maps to `job["title"]`.
*   `location` -> Maps to `job["location"]` (which is a simple string, e.g., "Remote, United States").
*   `published_at` -> Maps to `job["postedAt"]`.
*   `url` -> Maps to `job["publicUrl"]` or `job["applyUrl"]`.

## 4. Implementation Example

```python
import urllib.request
import json

def fetch_careerpuck_jobs(company_id):
    api_url = f"https://api.careerpuck.com/v1/public/job-boards/{company_id}"
    
    req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    json_data = urllib.request.urlopen(req).read().decode('utf-8')
    data = json.loads(json_data)
    raw_jobs = data.get("jobs", [])
    
    return raw_jobs
```

## 5. Adding Future Careerpuck Companies
1. Extract their `{company_id}` from the careers URL.
2. Create a minimal wrapper in `src/companies/` calling `fetch_careerpuck_jobs("{company_id}")`.
3. Register them in `registry.json` using `"base_ats": "careerpuck"`.
