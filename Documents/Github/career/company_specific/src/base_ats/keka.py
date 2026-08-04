import urllib.request
import json
import logging

def fetch_keka_jobs_from_embed_url(js_url):
    """
    Takes a Keka JS embed URL (e.g. https://company.keka.com/careers/api/embedjobs/js/UUID)
    and fetches the active jobs directly from the JSON API.
    """
    api_url = js_url.replace('/js/', '/default/active/')
    logging.info(f"[Keka Base] Fetching active jobs API at: {api_url}")
    
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        json_data = urllib.request.urlopen(req).read().decode('utf-8')
        raw_jobs = json.loads(json_data)
        
        jobs = []
        for j in raw_jobs:
            location_names = []
            if "jobLocations" in j and isinstance(j["jobLocations"], list):
                location_names = [loc.get("name", "N/A") for loc in j["jobLocations"] if "name" in loc]
            location_str = ", ".join(location_names) if location_names else "N/A"
            
            jobs.append({
                "title": j.get("title", "N/A"),
                "location": location_str,
                "published_at": j.get("publishedOn"),
                "url": None # Keka jobs pop up in a modal, URL is usually just the career site
            })
            
        logging.info(f"[Keka Base] Successfully extracted {len(jobs)} jobs from Keka.")
        return jobs
    except Exception as e:
        logging.error(f"[Keka Base] Failed to fetch active jobs API {api_url}: {e}")
        return []
