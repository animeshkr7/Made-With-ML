import os
import json
import time
from playwright.sync_api import sync_playwright

STATE_FILE = "state.json"
OUTPUT_DIR = "scratch_responses"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

responses_data = []

def handle_response(response):
    url = response.url
    if "graphql" in url or "voyager" in url or "search" in url:
        try:
            body = response.json()
            responses_data.append({
                "url": url,
                "body": body
            })
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    if os.path.exists(STATE_FILE):
        context = browser.new_context(storage_state=STATE_FILE)
    else:
        print("No state.json found!")
        exit(1)
        
    page = context.new_page()
    page.on("response", handle_response)
    
    search_url = 'https://www.linkedin.com/search/results/content/?keywords=ML%20Engineer&sortBy=%22date_posted%22'
    print(f"Navigating to {search_url}")
    page.goto(search_url)
    
    time.sleep(5)
    
    with open("scratch_responses.json", "w", encoding="utf-8") as f:
        json.dump(responses_data, f, indent=2)
        
    print(f"Dumped {len(responses_data)} responses to scratch_responses.json")
    browser.close()
