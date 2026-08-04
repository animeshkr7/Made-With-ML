import urllib.request
import json
import logging

def fetch_careerpuck_jobs(company_id):
    """
    Fetches jobs from Careerpuck API for the given company_id.
    """
    api_url = f"https://api.careerpuck.com/v1/public/job-boards/{company_id}"
    logging.info(f"[Careerpuck Base] Fetching active jobs API at: {api_url}")
    
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        json_data = urllib.request.urlopen(req).read().decode('utf-8')
        data = json.loads(json_data)
        raw_jobs = data.get("jobs", [])
        
        jobs = []
        for j in raw_jobs:
            jobs.append({
                "title": j.get("title", "N/A"),
                "location": j.get("location", "N/A"),
                "published_at": j.get("postedAt"),
                "url": j.get("publicUrl") or j.get("applyUrl")
            })
            
        logging.info(f"[Careerpuck Base] Successfully extracted {len(jobs)} jobs.")
        return jobs
    except Exception as e:
        logging.error(f"[Careerpuck Base] Failed to fetch active jobs API {api_url}: {e}")
        return []
