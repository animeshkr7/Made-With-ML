import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state='state.json')
    page = context.new_page()
    page.goto('https://www.linkedin.com/search/results/content/?keywords=ML%20Engineer&sortBy=%22date_posted%22')
    time.sleep(5)
    
    post = page.query_selector('div.update-components-actor, div.feed-shared-update-v2, li.reusable-search__result-container, [role=\'listitem\']')
    if post:
        html_content = post.evaluate('el => el.innerHTML')
        with open('one_post.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print('Saved one_post.html')
        
        # also print all links inside it
        links = post.query_selector_all('a')
        print("Links found:")
        for link in links:
            href = link.get_attribute('href')
            if href:
                print(href)
    else:
        print('No post found')
    browser.close()
