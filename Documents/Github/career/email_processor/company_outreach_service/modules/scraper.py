import time
import urllib.request
import re

def scrape_job_url(url: str, page=None) -> str:
    print(f"Scraping job URL: {url}")
    # Try using existing Playwright page if provided
    if page:
        try:
            page.goto(url, timeout=20000)
            time.sleep(2)
            text = page.locator("body").inner_text()
            return text[:4000]
        except Exception as e:
            print(f"Playwright page navigation failed: {e}")

    # Fallback to urllib standard HTTP request
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:4000]
    except Exception as e:
        print(f"Failed to scrape URL: {e}")
        return ""
