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
        
        url = 'https://www.linkedin.com/company/milliman/people/?facetNetwork=%5B%22S%22%2C%22O%22%5D'
        print(f"Testing {url}")
        page.goto(url)
        time.sleep(5)
        
        html = page.content()
        with open("company_people.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        browser.close()

if __name__ == "__main__":
    test_search()
