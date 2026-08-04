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
        # Find the "..." button. In HTML: aria-label="Open control menu..."
        menu_btn = post.query_selector('[aria-label^="Open control menu"]')
        if menu_btn:
            menu_btn.click()
            time.sleep(2)
            # Find the dropdown menu that appears
            menu = page.query_selector('.artdeco-dropdown__content, [role="menu"]')
            if menu:
                with open("menu.html", "w", encoding="utf-8") as f:
                    f.write(menu.evaluate("el => el.innerHTML"))
                print("Saved menu.html")
                
                # Check for "Copy link to post"
                copy_btn = page.query_selector('text="Copy link to post"')
                if copy_btn:
                    print("Found Copy link button")
            else:
                print("Menu didn't open")
        else:
            print("No menu button found")
    else:
        print('No post found')
    browser.close()
