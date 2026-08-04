import urllib.request
import json
import logging

def fetch_ashby_jobs(company_id):
    """
    Fetches jobs from Ashby API for the given company_id (the board name).
    """
    api_url = f"https://api.ashbyhq.com/posting-api/job-board/{company_id}"
    logging.info(f"[Ashby Base] Fetching active jobs API at: {api_url}")
    
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        json_data = urllib.request.urlopen(req).read().decode('utf-8')
        raw_jobs = json.loads(json_data).get("jobs", [])
        
        jobs = []
        for j in raw_jobs:
            location_str = j.get("location", "N/A")
            if not location_str and j.get("secondaryLocations"):
                location_str = ", ".join([loc.get("locationName", "") for loc in j.get("secondaryLocations")])
                
            jobs.append({
                "title": j.get("title", "N/A"),
                "location": location_str,
                "published_at": j.get("publishedAt") or j.get("createdAt") or j.get("postedAt"),
                "url": j.get("jobUrl") or j.get("applyUrl")
            })
            
        logging.info(f"[Ashby Base] Successfully extracted {len(jobs)} jobs from Ashby.")
        return jobs
    except Exception as e:
        logging.error(f"[Ashby Base] Failed to fetch active jobs API {api_url}: {e}")
        return []
