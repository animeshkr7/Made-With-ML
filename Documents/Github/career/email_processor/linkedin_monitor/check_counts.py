import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state='state.json')
    page = context.new_page()
    page.goto('https://www.linkedin.com/search/results/content/?keywords=ML%20Engineer&sortBy=%22date_posted%22')
    time.sleep(5)
    for _ in range(5):
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(2)
    
    posts = page.query_selector_all("li.reusable-search__result-container, div.feed-shared-update-v2, div.search-result__wrapper, [role='listitem']")
    print('Found posts via primary selectors:', len(posts))
    
    actors = page.query_selector_all('div.update-components-actor')
    print('Found posts via actor selector:', len(actors))
    
    # Try finding pagination 'Next' button if less than 15
    next_btn = page.query_selector('button[aria-label="Next"]')
    print('Found Next button:', next_btn is not None)
    
    page.screenshot(path='scroll_test.png')
    browser.close()
