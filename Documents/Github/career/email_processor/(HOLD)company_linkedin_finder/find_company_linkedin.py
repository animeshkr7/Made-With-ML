import sys
import os
import time
from playwright.sync_api import sync_playwright

def find_company_linkedin(company_name):
    print(f"Starting workflow for company: {company_name}")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state_file = os.path.join(base_dir, 'linkedin_monitor', 'state.json')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        if os.path.exists(state_file):
            print("Found saved LinkedIn session! Loading it to stay logged in...")
            context = browser.new_context(
                storage_state=state_file,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        else:
            print("WARNING: state.json not found! You might not be logged in.")
            context = browser.new_context()
            
        page = context.new_page()

        search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name}"
        print(f"Searching LinkedIn directly: {search_url}")
        page.goto(search_url)
        
        print("Looking for the first company result...")
        try:
            page.wait_for_selector('a[href*="/company/"]', timeout=15000)
        except Exception as e:
            print("Timeout waiting for company link! Saving screenshot to debug...")
            page.screenshot(path="debug_search.png")
            browser.close()
            raise e
        
        company_link = page.query_selector('a[href*="/company/"]')
        
        if company_link:
            url = company_link.get_attribute("href")
            if not url.startswith('http'):
                url = "https://www.linkedin.com" + url
            print(f"Found LinkedIn Company URL: {url}")
            
            if not url.endswith('/'):
                url += '/'
                
            print("Opening the LinkedIn company page...")
            page.goto(url)
            
            try:
                page.wait_for_selector('h1', timeout=15000)
            except:
                pass
                
            print("\nStarting Connection Workflow!")
            
            searches = [
                {"kw": "AI", "limit": 3},
                {"kw": "Lead", "limit": 2},
                {"kw": "Python", "limit": 2},
                {"kw": "Manager", "limit": 3},
                {"kw": "HR", "limit": 2},
                {"kw": "", "limit": 7}
            ]
            
            total_sent = 0
            MAX_TOTAL = 7
            
            for s in searches:
                if total_sent >= MAX_TOTAL:
                    break
                    
                kw = s["kw"]
                kw_limit = s["limit"]
                kw_sent = 0
                
                people_url = f"{url}people/?keywords={kw}"
                print(f"Navigating to People search for keyword: '{kw}'...")
                page.goto(people_url)
                
                # Wait for the people container to load with more resilient selectors
                try:
                    page.wait_for_selector('input[placeholder*="search"], .org-people, h2:has-text("people")', timeout=10000)
                except:
                    pass # Fallback if specific classes changed
                time.sleep(3)
                    
                # Scroll down a few times to load profiles
                for _ in range(3):
                    page.keyboard.press("PageDown")
                    time.sleep(1)
                    
                print(f"Scanning for 'Connect' buttons for keyword '{kw}'...")
                
                while total_sent < MAX_TOTAL and kw_sent < kw_limit:
                    # Look for buttons that contain the word "Connect" but haven't been ignored
                    # In newer LinkedIn UIs, the word "Connect" is often inside a span inside the button
                    connect_buttons = page.locator('button:has-text("Connect"):not(.ignore-connect)').all()
                    
                    if len(connect_buttons) == 0:
                        # Scroll a bit more to see if new ones load
                        page.keyboard.press("PageDown")
                        time.sleep(1)
                        page.keyboard.press("PageDown")
                        time.sleep(1)
                        new_buttons = page.locator('button:has-text("Connect"):not(.ignore-connect)').all()
                        if len(new_buttons) == 0:
                            print(f"No more 'Connect' buttons found for keyword '{kw}'. Moving to next keyword.")
                            break
                        connect_buttons = new_buttons
                        
                    clicked_one = False
                    
                    for btn in connect_buttons:
                        if btn.is_visible() and btn.is_enabled():
                            btn.scroll_into_view_if_needed()
                            time.sleep(0.5)
                            print("Clicking a 'Connect' button...")
                            try:
                                btn.click()
                                time.sleep(1.5)
                                
                                # Modal should pop up. Look for send without note or just send.
                                send_btn = page.locator('button[aria-label="Send without a note"], button[aria-label="Send now"]')
                                if send_btn.count() == 0:
                                    send_btn = page.locator('button:has-text("Send")')
                                    
                                if send_btn.count() > 0 and send_btn.first.is_visible():
                                    send_btn.first.click()
                                    time.sleep(2)
                                    total_sent += 1
                                    kw_sent += 1
                                    print(f"Sent connection! (Total: {total_sent}/7, Keyword '{kw}': {kw_sent}/{kw_limit})")
                                    clicked_one = True
                                    break
                                else:
                                    print("Could not find 'Send' button in modal. Might require email/premium. Dismissing...")
                                    dismiss_btn = page.locator('button[aria-label="Dismiss"]')
                                    if dismiss_btn.count() > 0:
                                        dismiss_btn.first.click()
                                    time.sleep(1)
                                    # Mark this button as ignored so we don't try it again
                                    btn.evaluate('node => node.classList.add("ignore-connect")')
                            except Exception as e:
                                print(f"Error clicking button: {e}")
                                # Mark as ignored
                                btn.evaluate('node => node.classList.add("ignore-connect")')
                                
                    if not clicked_one:
                        # If we looped through all current buttons and couldn't click any (or all failed)
                        break
                        
            print(f"\nWorkflow complete! Sent {total_sent} total requests.")
            print("The browser is left open so you can review.")
            input("Press Enter in this console to close the browser and exit...")
        else:
            print("Could not find any company results for that search on LinkedIn.")
            input("Press Enter in this console to close the browser and exit...")
            
        browser.close()

if __name__ == "__main__":
    company = "cisco"
    if len(sys.argv) > 1:
        company = " ".join(sys.argv[1:])
        
    find_company_linkedin(company)
