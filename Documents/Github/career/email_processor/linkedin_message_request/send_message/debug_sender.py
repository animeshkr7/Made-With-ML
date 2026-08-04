import time
import os
from playwright.sync_api import sync_playwright

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # linkedin_message_request
email_processor_dir = os.path.dirname(project_dir) # email_processor

state_path = os.path.join(email_processor_dir, "linkedin_monitor", "state.json")
if not os.path.exists(state_path):
    state_path = os.path.join(project_dir, "state.json")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state=state_path)
    page = context.new_page()
    page.goto("https://www.linkedin.com/in/agarg144")
    time.sleep(5)
    
    # Try finding Message
    msg_btn = page.query_selector('main button:has-text("Message"), main a:has-text("Message")')
    if msg_btn:
        print("Found Message button!")
        print(f"Class: {msg_btn.get_attribute('class')}")
    else:
        print("Message button not found.")
        buttons = page.query_selector_all('main button, main a')
        for b in buttons:
            try:
                text = b.inner_text().strip()
                if text:
                    print(f"Button/Link text: '{text}'")
            except:
                pass
            
    browser.close()
