import logging
import urllib.request
import json
import re
from datetime import datetime, timedelta, timezone

def scrape():
    """
    Scraper for Cisco (ThousandEyes).
    Uses the internal JSON API at careers.cisco.com/widgets.
    """
    logging.info("Starting Cisco (jobs.cisco.com) custom scraper...")
    
    # 1. Fetch CSRF token from the main search page
    search_url = "https://jobs.cisco.com/jobs/SearchJobs"
    try:
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
    except Exception as e:
        logging.error(f"Failed to fetch Cisco main page: {e}")
        return []

    csrf_match = re.search(r'<meta\s+name="csrf-token"\s+content="([^"]+)"', html)
    if not csrf_match:
        csrf_match = re.search(r'csrfToken\s*:\s*["\']([^"\']+)["\']', html)
        
    if not csrf_match:
        logging.error("Could not find CSRF token on Cisco jobs page (blocked by WAF or format changed).")
        return []
    
    csrf_token = csrf_match.group(1)
    
    # 2. Fetch jobs using the API
    api_url = "https://careers.cisco.com/widgets"
    
    # We want yesterday's jobs, but we'll fetch the first 100 recent jobs and let filter_and_save_jobs handle it
    payload = {
        "sortBy": "posted_date_desc", # usually sorting helps, or just leave empty
        "from": 0,
        "size": 50,
        "jobs": True,
        "counts": False,
        "pageName": "search-results",
        "jdsource": "facets",
        "isSliderEnable": False,
        "pageId": "page4",
        "siteType": "external",
        "global": True,
        "lang": "en_global",
        "deviceType": "desktop",
        "country": "global",
        "ddoKey": "refineSearch"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json',
        'X-CSRF-TOKEN': csrf_token
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(api_url, data=data, headers=headers, method='POST')
        response = urllib.request.urlopen(req).read().decode('utf-8')
        resp_json = json.loads(response)
    except Exception as e:
        logging.error(f"Failed to fetch Cisco jobs API: {e}")
        return []
        
    jobs_data = resp_json.get("refineSearch", {}).get("data", {}).get("jobs", [])
    
    formatted_jobs = []
    for job in jobs_data:
        # Expected format from subagent:
        # title, location, postedDate, applyUrl
        
        # company_specific filter expects 'published_at' instead of 'posted_at' for raw dates
        # Wait, filter_and_save_jobs uses job.get("published_at")
        
        formatted_jobs.append({
            "title": job.get("title", "Unknown Title"),
            "location": job.get("location", "Unknown Location"),
            "url": job.get("applyUrl", "https://jobs.cisco.com"),
            "published_at": job.get("postedDate")
        })
        
    logging.info(f"Cisco API returned {len(formatted_jobs)} jobs.")
    return formatted_jobs
