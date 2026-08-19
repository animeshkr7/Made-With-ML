import os
import sys
import time
import json
import smtplib
import imaplib
import email
from email.message import EmailMessage
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from groq import Groq

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "animeshkr7@gmail.com")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
APP_PASSWORD = os.getenv("APP_PASSWORD")

if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY in .env file")
    
client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# OTP Handling Logic
# ==========================================
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
        status, messages = mail.search(None, '(UNSEEN SUBJECT "Re: ACTION REQUIRED: LinkedIn OTP Pin")')
        if status == "OK" and messages[0]:
            latest_email_id = messages[0].split()[-1]
            status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                return ''.join(filter(str.isdigit, body.split('\n')[0].strip()))
                    else:
                        body = msg.get_payload(decode=True).decode()
                        return ''.join(filter(str.isdigit, body.split('\n')[0].strip()))
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

def handle_login(page, state_file):
    print("Navigating to login page...")
    page.goto('https://www.linkedin.com/login')
    try:
        page.wait_for_selector('input[type="password"]:visible', timeout=10000)
    except:
        return False
    if not LINKEDIN_PASSWORD:
        return False
    email_input = page.query_selector('input[type="text"]:visible, input[type="email"]:visible, #username:visible, #session_key:visible')
    if email_input:
        try:
            email_input.fill(LINKEDIN_EMAIL)
        except:
            pass
    if page.query_selector('#password:visible'):
        page.fill('#password:visible', LINKEDIN_PASSWORD)
    elif page.query_selector('#session_password:visible'):
        page.fill('#session_password:visible', LINKEDIN_PASSWORD)
    else:
        page.locator('input[type="password"]:visible').first.fill(LINKEDIN_PASSWORD)

    page.keyboard.press('Enter')
    try:
        page.click('button[type="submit"], button[aria-label="Sign in"], button.btn__primary--large', timeout=5000)
    except:
        pass
    page.wait_for_timeout(5000)
    
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
            
    if page.query_selector('.global-nav__me') or "feed" in page.url or "search" in page.url or "company" in page.url:
        print("Login successful! Saving state.")
        page.context.storage_state(path=state_file)
        return True
    return False

# ==========================================
# Main Workflow
# ==========================================

def scrape_job_url(url: str) -> str:
    print(f"Scraping job URL: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=30000)
            time.sleep(2)
            text = page.locator("body").inner_text()
            browser.close()
            return text[:4000]
        except Exception as e:
            browser.close()
            print(f"Failed to scrape URL (may be dead link): {e}")
            return ""

def extract_job_details(url: str, text: str) -> dict:
    print("Extracting job details using LLM (llama-3.1-8b-instant)...")
    prompt = f"""You are a precise data extractor. Extract the company name, job ID, and job title from the following job posting.
Hint: Company name is often in the URL path (e.g. greenhouse.io/COMPANY_NAME). If Job ID is missing, output "N/A". If Job Title is missing, guess from the URL or output "Role".

Job URL: {url}
Job Text:
{text[:3000]}

Respond ONLY with a valid JSON object matching this schema:
{{
  "company_name": "String",
  "job_id": "String",
  "job_title": "String"
}}
"""
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-20b",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        content = chat_completion.choices[0].message.content.strip()
        data = json.loads(content)
        
        # Fallbacks if LLM misses company
        if not data.get("company_name") or data["company_name"].lower() in ["none", "n/a", "null"]:
            if "greenhouse.io" in url or "lever.co" in url:
                data["company_name"] = url.split("/")[3]
                
        print(f"-> Extracted Data: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        print(f"LLM extraction failed: {e}")
        # Manual fallback
        comp = ""
        if "greenhouse.io" in url or "lever.co" in url:
            comp = url.split("/")[3]
        return {"company_name": comp, "job_id": "N/A", "job_title": "Role"}

def generate_draft_message(person_name: str, company: str, title: str, job_id: str) -> str:
    print(f"Generating tailored message for {person_name}...")
    prompt = f"""Draft a very short, professional LinkedIn message to a 1st-degree connection exactly matching this format:

Hi [Name],

I found [Company] is hiring and profile matches my expertise.

If you can look into it and guide me for this :
Job Id:[Job ID] - [Job Title]

Attached my resume for reference.

Use these exact details:
Name: {person_name}
Company: {company}
Job ID: {job_id}
Job Title: {title}

Output ONLY the final message. Do not include any extra text, pleasantries, or quotes.
"""
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-20b",
            temperature=0.0,
        )
        msg = res.choices[0].message.content.strip()
        return msg
    except Exception as e:
        print(f"Message generation failed: {e}")
        return f"Hi {person_name},\n\nI found {company} is hiring and profile matches my expertise.\n\nIf you can look into it and guide me for this :\nJob Id:{job_id} - {title}\n\nAttached my resume for reference."

def draft_messages_to_connections(page, company_name: str, job_title: str, job_id: str):
    print(f"Looking for 1st-degree connections from the search results...")
    print(f"Current URL: {page.url}")
    search_url = page.url  # Save search URL for later
    
    # Scroll down to ensure cards render
    page.keyboard.press("PageDown")
    time.sleep(3)
    
    # LinkedIn 2026 UI: Cards have componentkey, names in div.e31d23d7, Message links are <a> tags
    cards = page.query_selector_all('div[componentkey]')
    
    # Step 1: Collect all connection info (name + profile URL) upfront
    connections_info = []
    
    for card in cards:
        msg_link = card.query_selector('a:has-text("Message")')
        if not msg_link:
            continue
        link_text = msg_link.inner_text().strip()
        if "Message" not in link_text:
            continue
            
        first_name = None
        profile_url = None
        
        # Extract name
        try:
            name_el = card.query_selector('div.e31d23d7')
            if name_el:
                first_name = name_el.inner_text().strip().split()[0]
        except:
            pass
        
        # Extract profile URL from the card's profile link
        try:
            profile_link = card.query_selector('a[href*="/in/"]')
            if profile_link:
                profile_url = profile_link.get_attribute("href")
                if profile_url and not profile_url.startswith("http"):
                    profile_url = "https://www.linkedin.com" + profile_url
        except:
            pass
            
        if first_name and profile_url:
            connections_info.append({
                "first_name": first_name,
                "profile_url": profile_url
            })
            
    # Deduplicate connections based on profile_url
    unique_connections = []
    seen_urls = set()
    for conn in connections_info:
        if conn["profile_url"] not in seen_urls:
            seen_urls.add(conn["profile_url"])
            unique_connections.append(conn)
            
    if not unique_connections:
        print(f"No person is connected at {company_name}.")
        return
        
    print(f"Found {len(unique_connections)} unique connections! Drafting messages to max 3...")
    
    drafted_count = 0
    all_drafts = []
    
    for conn in unique_connections[:3]:
        first_name = conn["first_name"]
        profile_url = conn["profile_url"]
        
        # Generate the message
        draft_msg = generate_draft_message(first_name, company_name, job_title, job_id)
        
        # Save draft to local backup immediately
        all_drafts.append({
            "person": first_name,
            "company": company_name,
            "profile_url": profile_url,
            "message": draft_msg
        })
        
        print(f"\nDrafting message for {first_name}...")
        print(f"  Visiting profile: {profile_url}")
        
        try:
            # Visit the person's profile page
            page.goto(profile_url)
            time.sleep(3)
            
            # Find and click the Message button on their profile page
            msg_btn = page.query_selector('a:has-text("Message"), button:has-text("Message")')
            if not msg_btn:
                print(f"  Could not find Message button on {first_name}'s profile. Skipping.")
                continue
                
            msg_btn.evaluate("el => el.click()")
            time.sleep(3)
            
            # Wait for the chat textbox to appear
            chat_box = None
            for attempt in range(5):
                chat_box = page.query_selector('div.msg-form__contenteditable[role="textbox"], div[role="textbox"][contenteditable="true"]')
                if chat_box:
                    break
                time.sleep(1)
                
            if not chat_box:
                print(f"  Could not find the chat textbox for {first_name}. Skipping.")
                continue
                
            # Type the message
            chat_box.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            time.sleep(0.3)
            page.keyboard.type(draft_msg, delay=10)
            print(f"  Typed draft for {first_name} successfully.")
            time.sleep(1)
            
            # To properly trigger LinkedIn's auto-save API, we must close the chat normally.
            # Abruptly navigating away kills the page before the save request fires.
            page.keyboard.press("Escape")
            time.sleep(1)
            page.keyboard.press("Escape")
            time.sleep(2) # Give LinkedIn time to send the save request
            
            # Fallback close if Escape didn't work (which is safer on the profile page)
            close_btn = page.query_selector('button[aria-label*="close" i]:visible, button.msg-overlay-bubble-header__control--close-btn:visible')
            if close_btn:
                close_btn.evaluate("el => el.click()")
                time.sleep(2)
            
            print(f"  Draft for {first_name} saved successfully.")
            drafted_count += 1
            
        except Exception as e:
            print(f"  Failed to draft for {first_name}: {e}")
            
    # Save all drafts to a local JSON file as backup
    drafts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'drafted_messages.json')
    with open(drafts_path, 'w', encoding='utf-8') as f:
        json.dump(all_drafts, f, indent=2, ensure_ascii=False)
    print(f"\nAll {len(all_drafts)} draft messages saved to: {drafts_path}")
    print(f"Successfully drafted {drafted_count} messages in LinkedIn.")

def run_workflow(job_url: str):
    # 1. Scrape URL
    text = scrape_job_url(job_url)
    
    # 2. Extract Details
    details = extract_job_details(job_url, text)
    company_name = details.get("company_name")
    
    if not company_name or len(company_name) > 100:
        print("Failed to extract a valid company name.")
        sys.exit(1)
        
    # 3. Find exact company name on LinkedIn
    print(f"Searching native LinkedIn to find the exact company name for '{company_name}'...")
    company_search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name}"
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state_file = os.path.join(base_dir, 'linkedin_monitor', 'state.json')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        if os.path.exists(state_file):
            print("Loading saved LinkedIn session...")
            context = browser.new_context(
                storage_state=state_file,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        else:
            print("WARNING: state.json not found! You might not be logged in.")
            context = browser.new_context()
            
        page = context.new_page()
        page.goto(company_search_url)
        time.sleep(4)
        
        # Check if we got redirected to login
        if page.query_selector(".login__form, .alternate-signin-container, .join-form-container, #username"):
            print("Session expired or LinkedIn is asking to log in. Attempting automatic login...")
            if not handle_login(page, state_file):
                print("Failed to authenticate. Exiting.")
                browser.close()
                return
            page.goto(company_search_url)
            time.sleep(4)
            
        # DEBUG: Dump the company search page HTML
        debug_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug_company_search.html')
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(page.content())
        print(f"DEBUG: Saved company search HTML to {debug_path}")
        page.screenshot(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug_company_search.png'))
        print(f"DEBUG: Current URL after company search: {page.url}")
        
        # Extract exact name from the first company result
        # LinkedIn 2026 uses div.e31d23d7 for entity names inside cards with componentkey
        exact_company_name = company_name
        try:
            page.wait_for_selector('div.e31d23d7, .entity-result__title-text', timeout=10000)
            first_result = page.query_selector('div.e31d23d7, .entity-result__title-text')
            if first_result:
                exact_company_name = first_result.inner_text().strip().split('\n')[0].strip()
                print(f"-> Found exact LinkedIn company name: '{exact_company_name}'")
        except Exception as e:
            print(f"-> Could not find exact company name, falling back to '{company_name}'")
            
        # 4. Direct Native Search for 1st degree connections using EXACT name
        print(f"\nSearching for 1st-degree connections related to '{exact_company_name}'...")
        # %5B%22F%22%5D is URL-encoded ["F"]
        people_search_url = f"https://www.linkedin.com/search/results/people/?keywords={exact_company_name}&network=%5B%22F%22%5D"
        page.goto(people_search_url)
        time.sleep(5) # wait an extra second for results to render
            
        # We are on the People search page filtered by 1st degree connections!
        draft_messages_to_connections(page, exact_company_name, details.get("job_title", "Role"), details.get("job_id", "N/A"))
            
        print("\nWorkflow complete! Browser is left open.")
        input("Press Enter in this console to close the browser and exit...")
        browser.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python job_to_company_linkedin.py <job_url>")
        sys.exit(1)
        
    job_url = sys.argv[1]
    run_workflow(job_url)

if __name__ == "__main__":
    main()
