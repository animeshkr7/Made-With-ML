import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state='state.json')
    context.grant_permissions(["clipboard-read", "clipboard-write"])
    page = context.new_page()
    page.goto('https://www.linkedin.com/search/results/content/?keywords=ML%20Engineer&sortBy=%22date_posted%22')
    time.sleep(5)
    
    post = page.query_selector('div.update-components-actor, div.feed-shared-update-v2, li.reusable-search__result-container, [role=\'listitem\']')
    if post:
        with open("post_html.html", "w", encoding="utf-8") as f:
            f.write(post.evaluate('el => el.innerHTML'))
        
        menu_btn = post.query_selector('[aria-label^="Open control menu"]')
        if menu_btn:
            menu_btn.click()
            time.sleep(1)
            copy_btn = page.query_selector('div[role="button"]:has-text("Copy link to post"), div[role="menuitem"]:has-text("Copy link to post")')
            if not copy_btn:
                copy_btn = page.query_selector('text="Copy link to post"')
            if copy_btn:
                copy_btn.click()
                time.sleep(1)
                clip_text = page.evaluate("navigator.clipboard.readText()")
                print("Clipboard URL:", clip_text)
            else:
                print("No copy button")
        else:
            print("No menu button")
    else:
        print('No post found')
    browser.close()
