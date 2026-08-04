import os
import time
import smtplib
import imaplib
import email
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "animeshkr7@gmail.com")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
APP_PASSWORD = os.getenv("APP_PASSWORD")

def send_otp_request():
    print("LinkedIn requested an OTP. Sending notification email...")
    load_dotenv()
    email_to = os.getenv("LINKEDIN_EMAIL", "animeshkr7@gmail.com")
    app_pwd = os.getenv("APP_PASSWORD")
    msg = EmailMessage()
    msg['Subject'] = "ACTION REQUIRED: LinkedIn OTP Pin"
    msg['From'] = email_to
    msg['To'] = email_to
    body = "LinkedIn requires a PIN/OTP for login. Please reply to this email with ONLY the digits of the OTP."
    msg.set_content(body)
    try:
        if not app_pwd:
            print("Error: APP_PASSWORD is not set. Cannot send OTP request.")
            return False
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_to, app_pwd)
            server.send_message(msg)
        print("OTP request email sent. Waiting up to 60 seconds for a reply...")
        return True
    except Exception as e:
        print(f"Failed to send OTP email: {e}")
        return False

def send_email_notification(subject: str, json_content: str) -> bool:
    """
    Sends an email to LINKEDIN_EMAIL with the formatted JSON body as content.
    """
    load_dotenv()
    email_to = os.getenv("LINKEDIN_EMAIL", "animeshkr7@gmail.com")
    app_pwd = os.getenv("APP_PASSWORD")

    print(f"Sending email notification to {email_to}...")
    if not app_pwd:
        print("Warning: APP_PASSWORD is not set in .env. Skipping email notification.")
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = email_to
    msg['To'] = email_to
    msg.set_content(json_content)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_to, app_pwd)
            server.send_message(msg)
        print("-> Email notification sent successfully!")
        return True
    except Exception as e:
        print(f"-> Failed to send email notification: {e}")
        return False

def check_for_otp_reply():
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

def resolve_company_url_and_name(page, input_str: str):
    """
    Parses input_str which can be:
    1. LinkedIn Company URL (e.g. https://www.linkedin.com/company/colgate-palmolive/)
    2. LinkedIn Profile URL (e.g. https://www.linkedin.com/in/username/)
    3. Company Name (e.g. "Colgate Palmolive")
    4. Careers/Job Posting URL (e.g. https://jobs.lever.co/...)
    Returns (exact_company_name, company_url)
    """
    input_str = input_str.strip()
    print(f"Resolving company details for input: '{input_str}'...")

    # Case 1: Already a LinkedIn Company URL
    if "linkedin.com/company/" in input_str:
        company_url = input_str.split("?")[0]
        if not company_url.endswith("/"):
            company_url += "/"
        # Extract slug for fallback name
        slug = company_url.split("/company/")[1].strip("/").replace("-", " ").title()
        return slug, company_url

    # Case 2: LinkedIn Profile URL
    if "linkedin.com/in/" in input_str:
        print("Input is a LinkedIn Profile URL. Opening profile to find current company...")
        page.goto(input_str)
        time.sleep(4)
        comp_link = page.query_selector('a[href*="/company/"]')
        if comp_link:
            company_url = comp_link.get_attribute("href")
            if not company_url.startswith("http"):
                company_url = "https://www.linkedin.com" + company_url
            company_url = company_url.split("?")[0]
            if not company_url.endswith("/"):
                company_url += "/"
            name = comp_link.inner_text().strip().split('\n')[0]
            return name if name else "Company", company_url
        print("Could not find company link on profile page. Falling back to search.")

    # Case 3: Careers / Job Posting URL
    if input_str.startswith("http://") or input_str.startswith("https://"):
        print("Input is a web URL. Fetching content to extract company name...")
        try:
            from modules.scraper import scrape_job_url
            from modules.llm import extract_job_details
            text = scrape_job_url(input_str, page=page)
            details = extract_job_details(input_str, text)
            company_name = details.get("company_name", "").strip()
            if company_name:
                input_str = company_name
        except Exception as e:
            print(f"Error scraping URL: {e}")

    # Case 4: Search LinkedIn by Company Name
    company_search_url = f"https://www.linkedin.com/search/results/companies/?keywords={input_str}"
    print(f"Searching native LinkedIn for company '{input_str}'...")
    page.goto(company_search_url)
    time.sleep(4)
    
    exact_company_name = input_str
    company_url = None
    
    try:
        page.wait_for_selector('a[href*="/company/"]', timeout=10000)
        company_link = page.query_selector('a[href*="/company/"]')
        if company_link:
            exact_company_name = company_link.inner_text().strip().split('\n')[0].strip()
            if not exact_company_name:
                exact_company_name = input_str
            
            url = company_link.get_attribute("href")
            if url:
                if not url.startswith('http'):
                    url = "https://www.linkedin.com" + url
                url = url.split("?")[0]
                if not url.endswith('/'):
                    url += '/'
                company_url = url
                print(f"-> Found LinkedIn Company: '{exact_company_name}' at {company_url}")
    except Exception as e:
        print(f"-> Could not find exact company, fallback to '{input_str}'")
        
    return exact_company_name, company_url

def extract_1st_degree_connections(page, company_url: str, max_count: int = 5) -> list:
    """
    Navigates to company people page with 1st-degree filter (facetNetwork=F).
    Extracts at most `max_count` (default 5) 1st-degree connection profiles.
    """
    url = f"{company_url}people/?facetNetwork=F"
    print(f"\n[Step 1] Checking 1st-degree connections: {url}")
    page.goto(url)
    time.sleep(4)
    
    connections = []
    seen_urls = set()
    scroll_attempts = 0
    max_scrolls = 15
    
    while len(connections) < max_count and scroll_attempts < max_scrolls:
        # Find cards with Message buttons (1st degree) or profile links
        cards = page.query_selector_all('li.grid, .org-people-profile-card__profile-card-spacing, [role="listitem"]')
        
        for card in cards:
            if len(connections) >= max_count:
                break
                
            try:
                # Check for Message button to confirm 1st degree
                msg_btn = card.query_selector('button:has-text("Message"), a:has-text("Message")')
                if not msg_btn:
                    continue
                    
                profile_link = card.query_selector('a[href*="/in/"]')
                if not profile_link:
                    continue
                    
                profile_url = profile_link.get_attribute("href")
                if profile_url and not profile_url.startswith("http"):
                    profile_url = "https://www.linkedin.com" + profile_url
                if profile_url and "?" in profile_url:
                    profile_url = profile_url.split("?")[0]
                    
                if not profile_url or profile_url in seen_urls:
                    continue
                    
                # Extract Name
                first_name = ""
                name_el = card.query_selector('.org-people-profile-card__profile-title, .artdeco-entity-lockup__title, span[aria-hidden="true"]')
                if name_el:
                    full_name = name_el.inner_text().strip().split('\n')[0].strip()
                    if full_name and len(full_name.split()) > 0:
                        first_name = full_name.split()[0]
                        
                if not first_name:
                    img_els = card.query_selector_all('img[alt]')
                    for img in img_els:
                        alt = img.get_attribute('alt').strip()
                        if alt:
                            first_name = alt.split()[0]
                            break
                            
                seen_urls.add(profile_url)
                print(f" -> Found 1st-degree connection ({len(connections)+1}/{max_count}): {first_name} ({profile_url})")
                connections.append({
                    "first_name": first_name,
                    "profile_url": profile_url,
                    "is_1st_degree": True
                })
            except Exception as e:
                pass
                
        if len(connections) >= max_count:
            break
            
        page.keyboard.press("PageDown")
        time.sleep(1.5)
        
        try:
            show_more_btn = page.query_selector('button:has-text("Show more results"), .scaffold-finite-scroll__load-button, button.artdeco-button--muted:has-text("Show more")')
            if show_more_btn and show_more_btn.is_visible():
                show_more_btn.click()
                time.sleep(2)
        except Exception:
            pass

        scroll_attempts += 1
        
    print(f"Total 1st-degree connections extracted (max 5): {len(connections)}")
    return connections

def send_new_connection_requests(page, company_url: str, num_to_connect: int) -> list:
    """
    Navigates to unfiltered company people page (company_url + 'people/').
    Locates profile cards with 'Connect' buttons (excluding 'Message' or 'Pending').
    Sends connection requests to `num_to_connect` people.
    """
    if num_to_connect <= 0:
        print("\n[Step 2] Connection target count is 0. Skipping connection requests.")
        return []
        
    url = f"{company_url}people/"
    print(f"\n[Step 2] Navigating to unfiltered People page: {url}")
    print(f"Target count to connect: {num_to_connect}")
    page.goto(url)
    time.sleep(4)
    
    connected_list = []
    seen_urls = set()
    scroll_attempts = 0
    max_scrolls = 30
    
    while len(connected_list) < num_to_connect and scroll_attempts < max_scrolls:
        # Find buttons with Connect text
        buttons = page.query_selector_all('.org-people-profile-card__profile-card-spacing button:has-text("Connect"), button[aria-label*="Connect"]')
        
        for btn in buttons:
            if len(connected_list) >= num_to_connect:
                break
                
            try:
                if not btn.is_visible() or not btn.is_enabled():
                    continue
                    
                btn_text = btn.inner_text().strip()
                if "Message" in btn_text or "Pending" in btn_text or "Withdraw" in btn_text:
                    continue
                    
                card = btn.evaluate_handle('node => node.closest("li")')
                if not card:
                    continue
                    
                profile_link = card.query_selector('a[href*="/in/"]')
                profile_url = None
                first_name = ""
                
                if profile_link:
                    profile_url = profile_link.get_attribute("href")
                    if profile_url and not profile_url.startswith("http"):
                        profile_url = "https://www.linkedin.com" + profile_url
                    if profile_url and "?" in profile_url:
                        profile_url = profile_url.split("?")[0]
                        
                if profile_url and profile_url in seen_urls:
                    continue
                    
                # Get name
                name_el = card.query_selector('.org-people-profile-card__profile-title, .artdeco-entity-lockup__title')
                if name_el:
                    full_name = name_el.inner_text().strip().split('\n')[0].strip()
                    if full_name and len(full_name.split()) > 0:
                        first_name = full_name.split()[0]
                        
                if not first_name:
                    img_els = card.query_selector_all('img[alt]')
                    for img in img_els:
                        alt = img.get_attribute('alt').strip()
                        if alt:
                            first_name = alt.split()[0]
                            break
                            
                # Click Connect button
                print(f" -> Clicking Connect for: {first_name} ({profile_url or 'N/A'})...")
                btn.click()
                time.sleep(2)
                
                # Check for "Send without a note" or "Send now" modal button
                modal_send = page.query_selector('button[aria-label="Send without a note"], button[aria-label="Send now"], button:has-text("Send without a note"), button:has-text("Send")')
                if modal_send and modal_send.is_visible():
                    modal_send.click()
                    time.sleep(2)
                    print(f"    Connection request sent successfully to {first_name}!")
                else:
                    print(f"    Connect clicked (no modal prompt required).")
                    
                if profile_url:
                    seen_urls.add(profile_url)
                    
                connected_list.append({
                    "first_name": first_name,
                    "profile_url": profile_url,
                    "status": "Connection Request Sent"
                })
            except Exception as e:
                print(f"    Could not process connection button: {e}")
                
        if len(connected_list) >= num_to_connect:
            break
            
        page.keyboard.press("End")
        time.sleep(1.5)
        
        # Check and click "Show more results" button if present
        try:
            show_more_btn = page.query_selector('button:has-text("Show more results"), .scaffold-finite-scroll__load-button, button.artdeco-button--muted:has-text("Show more")')
            if show_more_btn and show_more_btn.is_visible():
                print(" -> Clicking 'Show more results' to load additional profiles...")
                show_more_btn.click()
                time.sleep(2)
        except Exception:
            pass

        scroll_attempts += 1
        
    print(f"Successfully sent {len(connected_list)} connection request(s).")
    return connected_list
