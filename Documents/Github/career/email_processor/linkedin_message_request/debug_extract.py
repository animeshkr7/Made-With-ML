import time
import os
from playwright.sync_api import sync_playwright

project_dir = os.path.dirname(os.path.abspath(__file__)) # linkedin_message_request

state_path = os.path.join(project_dir, "state.json")
if not os.path.exists(state_path):
    state_path = os.path.join(os.path.dirname(project_dir), "linkedin_monitor", "state.json")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state=state_path)
    page = context.new_page()
    page.goto("https://www.linkedin.com/company/milliman/people/")
    time.sleep(5)
    
    # Scroll a bit
    for _ in range(3):
        page.keyboard.press("PageDown")
        time.sleep(1)
        
    buttons = page.query_selector_all('.org-people-profile-card__profile-card-spacing button')
    print(f"Found {len(buttons)} total buttons in profile cards")
    for b in buttons:
        try:
            print(f"Text: '{b.inner_text().strip()}', Aria-Label: '{b.get_attribute('aria-label')}'")
        except:
            pass
            
    browser.close()
