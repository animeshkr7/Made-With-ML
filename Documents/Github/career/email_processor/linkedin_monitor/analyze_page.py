import os
import time
from playwright.sync_api import sync_playwright

STATE_FILE = "state.json"

def analyze_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            storage_state=STATE_FILE,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        search_url = 'https://www.linkedin.com/search/results/content/?keywords=ML%20Engineer&sortBy=%22date_posted%22'
        page.goto(search_url)
        time.sleep(10)
        
        # Take a screenshot to confirm it loaded
        page.screenshot(path="analyze_screenshot.png")
        
        # Find all li elements and their classes
        classes_script = """
            () => {
                let els = document.querySelectorAll('li, div, ul');
                let classCounts = {};
                els.forEach(el => {
                    if (el.className && typeof el.className === 'string') {
                        let cName = el.className.trim();
                        classCounts[cName] = (classCounts[cName] || 0) + 1;
                    }
                });
                return classCounts;
            }
        """
        counts = page.evaluate(classes_script)
        
        # Sort and print most common classes
        sorted_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        print("Most common classes:")
        for k, v in sorted_counts[:20]:
            print(f"{v}: {k}")
            
        print("\nChecking common linkedin selectors:")
        selectors = [
            "div.feed-shared-update-v2",
            "li.reusable-search__result-container",
            "div.update-components-actor",
            "div[data-urn]",
            "div.search-results-container",
            "ul.reusable-search__entity-result-list"
        ]
        
        for sel in selectors:
            count = len(page.query_selector_all(sel))
            print(f"Selector '{sel}': {count} found")

        browser.close()

if __name__ == "__main__":
    analyze_page()
