# ATS Scraping Insights: SmartRecruiters

This document details the methodology used to integrate the SmartRecruiters ATS into our scraping pipeline, discovered during the integration of Arista Networks.

## 1. The SmartRecruiters Architecture

SmartRecruiters, similar to Ashby, exposes a structured JSON API endpoint to fetch active jobs dynamically for career sites.

When a company uses SmartRecruiters, their job board URL is typically:
`https://careers.smartrecruiters.com/{company_id}`

## 2. Discovering the API

By inspecting the Network tab when visiting `careers.smartrecruiters.com/AristaNetworks`, we observed that the page queries a highly reliable public API endpoint.

**The Endpoint:**
`https://api.smartrecruiters.com/v1/companies/{company_id}/postings`

This API is strictly paginated.

## 3. The Extraction Logic and Pagination

The API returns a JSON object where the jobs are contained in the `content` array.

**CRITICAL DISCOVERY - Pagination:**
SmartRecruiters enforces a hard limit per request (default max 100). If a company has more than 100 jobs (like Arista which had 254), a single request will silently truncate the data.

To fetch all jobs, you **must** use the `limit` and `offset` query parameters in a loop:
`?limit=100&offset={offset}`

**Schema Mapping for Standardization:**
*   `title` -> Maps to `job["name"]`.
*   `location` -> Maps to `job["location"]["fullLocation"]`.
*   `published_at` -> Maps to `job["releasedDate"]`.
*   `url` -> SmartRecruiters does not return the public URL in the JSON payload. You must construct it manually using the schema: `https://jobs.smartrecruiters.com/{company_id}/{job["id"]}`.

## 4. Implementation Example

```python
import urllib.request
import json

def fetch_smartrecruiters_jobs(company_id):
    api_url = f"https://api.smartrecruiters.com/v1/companies/{company_id}/postings"
    
    offset = 0
    limit = 100
    jobs = []
    
    while True:
        paged_url = f"{api_url}?limit={limit}&offset={offset}"
        req = urllib.request.Request(paged_url, headers={'User-Agent': 'Mozilla/5.0'})
        json_data = urllib.request.urlopen(req).read().decode('utf-8')
        raw_jobs = json.loads(json_data).get("content", [])
        
        if not raw_jobs:
            break
            
        jobs.extend(raw_jobs)
        
        if len(raw_jobs) < limit:
            break
        offset += limit
        
    return jobs
```

## 5. Adding Future SmartRecruiters Companies
1. Extract their `{company_id}` from the careers URL.
2. Create a minimal wrapper in `src/companies/` calling `fetch_smartrecruiters_jobs("{company_id}")`.
3. Register them in `registry.json` using `"base_ats": "smartrecruiters"`.
