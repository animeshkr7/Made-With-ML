import time
import urllib.request
import re

def fetch_job_text_chunk(url: str, chunk_size: int = 3500) -> str:
    """
    Fetches raw text content from a job posting URL and returns a cleaned top text chunk.
    """
    print(f"Fetching webpage content from: {url}")
    html_content = ""

    # Method 1: Standard HTTP request
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"HTTP fetch warning: {e}. Trying Playwright scraper...")
        
    # Method 2: Playwright fallback if HTTP request fails or yields little text
    if not html_content or len(html_content) < 300:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=25000)
                time.sleep(2)
                html_content = page.content()
                browser.close()
        except Exception as pe:
            print(f"Playwright fetch failed: {pe}")

    if not html_content:
        return ""

    # Clean HTML tags and consolidate whitespace
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # Return top content chunk
    chunked_text = text[:chunk_size]
    print(f"-> Extracted top content chunk ({len(chunked_text)} chars)")
    return chunked_text
