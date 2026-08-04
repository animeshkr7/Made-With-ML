import urllib.request
import re
import logging
from src.base_ats.keka import fetch_keka_jobs_from_embed_url

def scrape():
    """
    Entry point for scraping Akaike.ai.
    """
    url = "http://akaike.ai/careers"
    logging.info(f"Fetching {url} for Akaike")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
    except Exception as e:
        logging.error(f"Failed to fetch {url}: {e}")
        return []

    # Find the Keka JS embed URL
    match = re.search(r'src="(https://.*?keka\.com/careers/api/embedjobs/js/[^"]+)"', html)
    if not match:
        logging.error("Could not find Keka embed JS URL in the Akaike page HTML.")
        return []
        
    js_url = match.group(1)
    logging.info(f"Found Keka JS embed URL for Akaike: {js_url}")
    
    return fetch_keka_jobs_from_embed_url(js_url)
