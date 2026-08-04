import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state='state.json')
    page = context.new_page()
    page.goto('https://www.linkedin.com/search/results/content/?keywords=ML%20Engineer&sortBy=%22date_posted%22')
    time.sleep(5)
    
    posts = page.query_selector_all("li.reusable-search__result-container, div.feed-shared-update-v2, div.search-result__wrapper, [role='listitem']")
    for idx, post in enumerate(posts[:5]):
        # Look for the time text. Often inside a span that also contains a dot or globe icon.
        # It's usually the second or third span after the author's name. 
        # For a robust approach, we can grab all text from the post and print it to debug.
        # Alternatively, find the element that matches regex \d+[mhdwy] • or similar.
        text = post.inner_text()
        lines = text.split('\n')
        print(f"--- Post {idx} ---")
        for i, line in enumerate(lines[:10]):
            print(f"Line {i}: {line}")
            
    browser.close()
