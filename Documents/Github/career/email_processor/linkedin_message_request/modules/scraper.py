import time
from playwright.sync_api import sync_playwright

def scrape_job_url(url: str) -> str:
    print(f"Scraping job URL: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=30000)
            time.sleep(2)
            text = page.locator("body").inner_text()
            browser.close()
            return text[:4000]
        except Exception as e:
            browser.close()
            print(f"Failed to scrape URL (may be dead link): {e}")
            return ""
