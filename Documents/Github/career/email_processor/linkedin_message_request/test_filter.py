import time
from playwright.sync_api import sync_playwright

def test_search():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state="../linkedin_monitor/state.json",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        url1 = 'https://www.linkedin.com/company/milliman/people/?facetNetwork=%5B%22F%22%5D'
        print(f"Testing {url1}")
        page.goto(url1)
        time.sleep(5)
        
        cards = page.query_selector_all('[role="listitem"]') # people grid items are sometimes li, wait let's just get HTML
        print(f"URL 1 has {len(cards)} cards")
        page.screenshot(path="debug_url1.png")
        
        url2 = 'https://www.linkedin.com/company/milliman/people/?facetNetwork=F'
        print(f"Testing {url2}")
        page.goto(url2)
        time.sleep(5)
        
        cards2 = page.query_selector_all('[role="listitem"]')
        print(f"URL 2 has {len(cards2)} cards")
        page.screenshot(path="debug_url2.png")
        
        browser.close()

if __name__ == "__main__":
    test_search()
