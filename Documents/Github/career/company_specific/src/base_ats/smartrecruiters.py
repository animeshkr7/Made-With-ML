import urllib.request
import json
import logging

def fetch_smartrecruiters_jobs(company_id):
    """
    Fetches jobs from SmartRecruiters API for the given company_id.
    """
    api_url = f"https://api.smartrecruiters.com/v1/companies/{company_id}/postings"
    logging.info(f"[SmartRecruiters Base] Fetching active jobs API at: {api_url}")
    
    try:
        offset = 0
        limit = 100
        jobs = []
        
        while True:
            paged_url = f"{api_url}?limit={limit}&offset={offset}"
            logging.info(f"[SmartRecruiters Base] Fetching page: {paged_url}")
            
            req = urllib.request.Request(paged_url, headers={'User-Agent': 'Mozilla/5.0'})
            json_data = urllib.request.urlopen(req).read().decode('utf-8')
            data = json.loads(json_data)
            
            raw_jobs = data.get("content", [])
            if not raw_jobs:
                break
                
            for j in raw_jobs:
                location_data = j.get("location", {})
                location_str = location_data.get("fullLocation", "N/A")
                
                jobs.append({
                    "title": j.get("name", "N/A"),
                    "location": location_str,
                    "published_at": j.get("releasedDate"),
                    "url": f"https://jobs.smartrecruiters.com/{company_id}/{j.get('id')}"
                })
                
            if len(raw_jobs) < limit:
                break
            
            offset += limit
            
        logging.info(f"[SmartRecruiters Base] Successfully extracted {len(jobs)} total jobs.")
        return jobs
    except Exception as e:
        logging.error(f"[SmartRecruiters Base] Failed to fetch active jobs API {api_url}: {e}")
        return []
