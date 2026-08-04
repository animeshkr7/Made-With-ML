import os
import time
from playwright.sync_api import sync_playwright

STATE_FILE = "state.json"

def setup_auth():
    print("Starting Playwright to setup LinkedIn authentication...")
    with sync_playwright() as p:
        # Launch in headed mode so the user can interact
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("Navigating to LinkedIn login page...")
        page.goto("https://www.linkedin.com/login")
        
        print("\n" + "="*50)
        print("*** ACTION REQUIRED ***")
        print("1. Look at the Chromium browser window that just opened.")
        print("2. Log in to your LinkedIn account manually.")
        print("3. Wait until you see your LinkedIn feed.")
        print("4. Return to this terminal and press ENTER.")
        print("="*50 + "\n")
        
        input("Press ENTER here ONLY AFTER you have successfully logged in...")

        # Save state (cookies, local storage, etc.)
        context.storage_state(path=STATE_FILE)
        print(f"\n✅ Success! Authentication state saved to {STATE_FILE}.")
        print("You can now run the automated scraper.")
        
        browser.close()

if __name__ == "__main__":
    setup_auth()
