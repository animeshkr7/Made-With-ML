import time
import re
from playwright.sync_api import sync_playwright

def is_older_than_3_hours(text):
    lines = text.split('\n')
    for line in lines[:15]:
        line = line.strip()
        # The character is often \u2022 or \u00b7. Let's just match any non-word character if it starts the line.
        match = re.match(r'^(now|\d+[mhdwy])\s*[\u2022\u00B7]', line)
        if match:
            time_str = match.group(1)
            print(f"Found time: {time_str}")
            if time_str == 'now':
                return False
            if time_str.endswith('m'):
                return False
            if time_str.endswith('h'):
                val = int(time_str[:-1])
                return val >= 3
            return True
    return False

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state='state.json')
    page = context.new_page()
    page.goto('https://www.linkedin.com/search/results/content/?keywords=ML%20Engineer&sortBy=%22date_posted%22')
    time.sleep(5)
    
    posts = page.query_selector_all("li.reusable-search__result-container, div.feed-shared-update-v2, div.search-result__wrapper, [role='listitem']")
    if posts:
        for idx, post in enumerate(posts[:5]):
            text = post.inner_text()
            older = is_older_than_3_hours(text)
            print(f"Post {idx} older than 3h? {older}")
            
    browser.close()
