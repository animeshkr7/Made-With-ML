import time
import re
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state='state.json')
    page = context.new_page()
    page.goto('https://www.linkedin.com/search/results/content/?keywords=ML%20Engineer&sortBy=%22date_posted%22')
    time.sleep(5)
    
    post = page.query_selector('div.update-components-actor, div.feed-shared-update-v2, li.reusable-search__result-container, [role=\'listitem\']')
    if post:
        html_content = post.evaluate('el => el.outerHTML')
        urns = re.findall(r'urn:li:activity:\d+', html_content)
        print("Found URNs:", set(urns))
        
        # Look for data-id or data-urn
        print("data-id:", post.get_attribute('data-id'))
        print("data-urn:", post.get_attribute('data-urn'))
    else:
        print('No post found')
    browser.close()
