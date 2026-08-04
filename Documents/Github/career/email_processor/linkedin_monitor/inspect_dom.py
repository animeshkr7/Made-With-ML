import os
import time
from playwright.sync_api import sync_playwright

STATE_FILE = "state.json"

def inspect_dom():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=STATE_FILE,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        search_url = 'https://www.linkedin.com/search/results/content/?keywords=ML%20Engineer&sortBy=%22date_posted%22'
        page.goto(search_url)
        time.sleep(5)
        
        html = page.evaluate("() => document.body.innerHTML")
        with open("first_post.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved full HTML to first_post.html")
            
        browser.close()

if __name__ == "__main__":
    inspect_dom()
