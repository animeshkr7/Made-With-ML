import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import smtplib
from email.message import EmailMessage
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

STATE_FILE = "state.json"
OUTPUT_DIR = "output"

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "animeshkr7@gmail.com")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
APP_PASSWORD = os.getenv("APP_PASSWORD")

def send_otp_request():
    print("LinkedIn requested an OTP. Sending notification email...")
    msg = EmailMessage()
    msg['Subject'] = "ACTION REQUIRED: LinkedIn OTP Pin"
    msg['From'] = LINKEDIN_EMAIL
    msg['To'] = LINKEDIN_EMAIL
    
    body = "LinkedIn requires a PIN/OTP for login. Please reply to this email with ONLY the digits of the OTP."
    msg.set_content(body)

    try:
        if not APP_PASSWORD:
            print("Error: APP_PASSWORD is not set. Cannot send OTP request.")
            return False
            
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(LINKEDIN_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        print("OTP request email sent. Waiting up to 60 seconds for a reply...")
        return True
    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        return False

def check_for_otp_reply():
    print("Checking for OTP reply...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(LINKEDIN_EMAIL, APP_PASSWORD)
        mail.select("inbox")
        
        # Search for unread emails with the subject
        status, messages = mail.search(None, '(UNSEEN SUBJECT "Re: ACTION REQUIRED: LinkedIn OTP Pin")')
        
        if status == "OK" and messages[0]:
            latest_email_id = messages[0].split()[-1]
            status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                # Clean up and extract numbers
                                otp = ''.join(filter(str.isdigit, body.split('\n')[0].strip()))
                                return otp
                    else:
                        body = msg.get_payload(decode=True).decode()
                        otp = ''.join(filter(str.isdigit, body.split('\n')[0].strip()))
                        return otp
    except Exception as e:
        print(f"Error checking email: {e}")
    finally:
        try:
            mail.close()
            mail.logout()
        except:
            pass
    return None

def wait_for_otp(timeout_seconds=60):
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        otp = check_for_otp_reply()
        if otp:
            print(f"Received OTP: {otp}")
            return otp
        time.sleep(5)
    print("Timed out waiting for OTP.")
    return None

def handle_login(page):
    print("Navigating to login page...")
    page.goto('https://www.linkedin.com/login')
    
    try:
        # Wait for the password field instead, as the email field might be hidden on the 'Welcome Back' screen
        page.wait_for_selector('input[type="password"]:visible', timeout=10000)
    except Exception as e:
        print(f"Failed to find login fields: {e}")
        page.screenshot(path="login_page_failed.png")
        print("Saved screenshot of what the login page looks like to login_page_failed.png")
        return False
    
    if not LINKEDIN_PASSWORD:
        print("Error: LINKEDIN_PASSWORD not found in environment.")
        return False
        
    # Try filling username if it exists (it won't exist on the 'Welcome back' screen)
    email_input = page.query_selector('input[type="text"]:visible, input[type="email"]:visible, #username:visible, #session_key:visible')
    if email_input:
        try:
            email_input.fill(LINKEDIN_EMAIL)
        except Exception:
            pass # ignore errors if it's not interactable

    # Try filling password
    if page.query_selector('#password:visible'):
        page.fill('#password:visible', LINKEDIN_PASSWORD)
    elif page.query_selector('#session_password:visible'):
        page.fill('#session_password:visible', LINKEDIN_PASSWORD)
    else:
        page.locator('input[type="password"]:visible').first.fill(LINKEDIN_PASSWORD)

    # Press Enter to submit the form, which is more robust
    page.keyboard.press('Enter')
    
    # Fallback click if it didn't submit
    try:
        page.click('button[type="submit"], button[aria-label="Sign in"], button.btn__primary--large', timeout=5000)
    except Exception:
        pass
        
    page.wait_for_timeout(5000)
    
    # Check for OTP challenge
    if page.query_selector('input[name="pin"]'):
        print("OTP Challenge detected.")
        if send_otp_request():
            otp = wait_for_otp()
            if otp:
                page.fill('input[name="pin"]', otp)
                page.click('button[type="submit"]')
                page.wait_for_timeout(5000)
            else:
                return False
        else:
            return False
            
    # Check if login was successful
    if page.query_selector('.global-nav__me') or "feed" in page.url or "search" in page.url:
        print("Login successful! Saving state.")
        page.context.storage_state(path=STATE_FILE)
        return True
    else:
        print("Login failed or encountered unexpected challenge.")
        page.screenshot(path="login_failed.png")
        with open("login_failed.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        return False

def run_scraper(headless=True):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print("Starting LinkedIn scraper...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        
        if os.path.exists(STATE_FILE):
            context = browser.new_context(
                storage_state=STATE_FILE,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                permissions=['clipboard-read', 'clipboard-write']
            )
        else:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                permissions=['clipboard-read', 'clipboard-write']
            )
            
        page = context.new_page()

        # Simple keyword searches — LinkedIn handles short queries much better
        # than complex boolean expressions which often return "No results found"
        search_keywords = [
            "hiring AI ML engineer",
            "hiring machine learning",
            "recruiting AI team",
            "looking for ML engineers",
        ]
        
        import re
        def is_older_than_3_hours(text):
            lines = text.split('\n')
            for line in lines[:15]:
                line = line.strip()
                match = re.match(r'^(now|\d+[mhdwy])\s*[\u2022\u00B7]', line)
                if match:
                    time_str = match.group(1)
                    if time_str == 'now' or time_str.endswith('m'):
                        return False
                    if time_str.endswith('h'):
                        val = int(time_str[:-1])
                        return val > 3
                    return True
            return False

        extracted_data = []
        seen_urls = set()
        login_handled = False

        for keyword_idx, keyword in enumerate(search_keywords):
            from urllib.parse import quote
            search_url = f'https://www.linkedin.com/search/results/content/?keywords={quote(keyword)}&sortBy=%22date_posted%22'
            
            print(f"\n--- Search {keyword_idx+1}/{len(search_keywords)}: \"{keyword}\" ---")
            
            search_success = False
            for attempt in range(3):
                print(f"Navigating to LinkedIn Search (Attempt {attempt+1})")
                page.goto(search_url)
                time.sleep(5)
                
                # Handle login redirect (only needed once)
                if not login_handled and page.query_selector(".login__form, .alternate-signin-container, .join-form-container, #username"):
                    print("Session expired or LinkedIn is asking to log in. Attempting automatic login...")
                    if not handle_login(page):
                        browser.close()
                        return
                    login_handled = True
                    # Navigate back to search URL after login
                    page.goto(search_url)
                    time.sleep(5)
                
                # Handle random LinkedIn "Something went wrong" error
                try:
                    body_text = page.inner_text("body")
                except:
                    body_text = ""
                    
                try_btn = page.query_selector('button:has-text("Try again")')
                
                if "Something went wrong" in body_text or try_btn:
                    print("LinkedIn threw an error page. Retrying in 5 seconds...")
                    if try_btn:
                        try_btn.click()
                    else:
                        page.reload()
                    time.sleep(5)
                    continue
                
                if "No results found" in body_text:
                    print(f"No results for \"{keyword}\", skipping to next query.")
                    break
                    
                search_success = True
                break
            
            if not search_success:
                continue
            
            # Scroll to load posts from the last 3 hours
            print(f"Scrolling to load posts for \"{keyword}\"...")
            last_count = 0
            stuck_count = 0
            while True:
                posts = page.query_selector_all("li.reusable-search__result-container, div.feed-shared-update-v2, div.search-result__wrapper, [role='listitem']")
                if not posts:
                    break
                    
                try:
                    posts[-1].scroll_into_view_if_needed()
                except:
                    pass
                page.keyboard.press("PageDown")
                time.sleep(2)
                
                if len(posts) > 0:
                    try:
                        text = posts[-1].inner_text()
                        if is_older_than_3_hours(text):
                            print("Found post older than 3 hours, stopping scroll.")
                            break
                    except:
                        pass
                        
                if len(posts) == last_count:
                    stuck_count += 1
                    if stuck_count > 3:
                        print("No more posts loading.")
                        break
                else:
                    last_count = len(posts)
                    stuck_count = 0

            # Extract posts from this search
            print(f"Extracting posts for \"{keyword}\"...")
            post_elements = page.query_selector_all("li.reusable-search__result-container, div.feed-shared-update-v2, div.search-result__wrapper, [role='listitem']")
            if not post_elements:
                post_elements = page.query_selector_all("div.update-components-actor")
                post_elements = [el.evaluate_handle("el => el.closest('div[data-urn]') || el.closest('li') || el.closest('[role=\"listitem\"]') || el").as_element() for el in post_elements if el]

            posts_from_this_search = 0
            for idx, post in enumerate(post_elements):
                try:
                    author = "Unknown Author"
                    author_el = post.query_selector(".entity-result__title-text, .update-components-actor__title, .update-components-actor__name, .feed-shared-actor__name, span[dir='ltr']")
                    if author_el:
                        author = author_el.inner_text().strip().split('\n')[0].strip()
                    else:
                        # Fallback for new UI
                        profile_el = post.query_selector('[aria-label*="profile"]')
                        if profile_el:
                            label = profile_el.get_attribute("aria-label")
                            if label:
                                author = label.replace("View ", "").replace("'s profile", "").replace("\u2019s profile", "").strip()

                    text_el = post.query_selector(".entity-result__summary, .update-components-text, .feed-shared-update-v2__description-wrapper, .feed-shared-text, .break-words, [data-testid='expandable-text-box']")
                    text = text_el.inner_text().strip() if text_el else "No Text"

                    url = "Unknown URL"
                    try:
                        page.evaluate("navigator.clipboard.writeText('')")
                        menu_btn = post.query_selector('[aria-label^="Open control menu"]')
                        if menu_btn:
                            menu_btn.scroll_into_view_if_needed()
                            menu_btn.click()
                            time.sleep(1)
                            copy_btn = page.query_selector('text="Copy link to post"')
                            if copy_btn:
                                copy_btn.click()
                                time.sleep(1)
                                clip_text = page.evaluate("navigator.clipboard.readText()")
                                if clip_text and clip_text.startswith("http"):
                                    url = clip_text
                            else:
                                page.keyboard.press("Escape")
                    except Exception as ex:
                        print(f"Error extracting url: {ex}")
                        page.keyboard.press("Escape")

                    if url not in seen_urls:
                        seen_urls.add(url)
                        extracted_data.append({
                            "id": len(extracted_data) + 1,
                            "author": author,
                            "url": url,
                            "text": text,
                            "search_keyword": keyword,
                            "scraped_at": datetime.now().isoformat()
                        })
                        posts_from_this_search += 1
                except Exception as e:
                    print(f"Failed to extract a post: {e}")
            
            print(f"Extracted {posts_from_this_search} new posts from \"{keyword}\" (total so far: {len(extracted_data)})")

        if not extracted_data:
            print("No posts were extracted from any search. Dumping HTML to debug_html.html")
            with open("debug_html.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            page.screenshot(path="debug_screenshot.png")
            print("Saved debug_screenshot.png and debug_html.html")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(OUTPUT_DIR, f"linkedin_ml_posts_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=4)

        print(f"\n[SUCCESS] Scraper finished successfully!")
        print(f"Extracted {len(extracted_data)} posts.")
        print(f"Data saved to: {output_file}")

        browser.close()
        return output_file

if __name__ == "__main__":
    run_scraper(headless=False)
