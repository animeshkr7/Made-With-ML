import os
import time
import smtplib
import imaplib
import email
from email.message import EmailMessage

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

def find_exact_company_name(page, company_name: str):
    company_search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name}"
    page.goto(company_search_url)
    time.sleep(4)
    exact_company_name = company_name
    company_url = None
    
    try:
        page.wait_for_selector('a[href*="/company/"]', timeout=10000)
        
        company_link = page.query_selector('a[href*="/company/"]')
        if company_link:
            # Extract Name
            exact_company_name = company_link.inner_text().strip().split('\n')[0].strip()
            if not exact_company_name:
                exact_company_name = company_name
            print(f"-> Found exact LinkedIn company name: '{exact_company_name}'")
            
            # Extract URL
            url = company_link.get_attribute("href")
            if url:
                if not url.startswith('http'):
                    url = "https://www.linkedin.com" + url
                if not url.endswith('/'):
                    url += '/'
                
                # Strip parameters
                if "?" in url:
                    url = url.split("?")[0]
                    
                company_url = url
                print(f"-> Found LinkedIn Company URL: {company_url}")
                
    except Exception as e:
        print(f"-> Could not find exact company, falling back to '{company_name}'")
        
    return exact_company_name, company_url

def extract_connections(page, exact_company_name: str, max_connections: int = 5, networks: list = ["F"]) -> list:
    network_str = "%2C".join([f"%22{n}%22" for n in networks])
    people_search_url = f"https://www.linkedin.com/search/results/people/?keywords={exact_company_name}&network=%5B{network_str}%5D"
    page.goto(people_search_url)
    time.sleep(5)
    
    page.keyboard.press("PageDown")
    time.sleep(3)
    
    cards = page.query_selector_all('[role="listitem"]')
    connections_info = []
    
    for card in cards:
        first_name = None
        profile_url = None
        
        try:
            img_el = card.query_selector('img[alt]')
            if img_el:
                full_name = img_el.get_attribute('alt').strip()
                if full_name and len(full_name.split()) > 0:
                    first_name = full_name.split()[0]
        except:
            pass
        
        try:
            profile_link = card.query_selector('a[href*="/in/"]')
            if profile_link:
                profile_url = profile_link.get_attribute("href")
                if profile_url and not profile_url.startswith("http"):
                    profile_url = "https://www.linkedin.com" + profile_url
                
                # Split at the ? to remove tracking params from profile url
                if profile_url and "?" in profile_url:
                    profile_url = profile_url.split("?")[0]
        except:
            pass
            
        if first_name and profile_url:
            connections_info.append({
                "first_name": first_name,
                "profile_url": profile_url,
                "is_1st_degree": ("F" in networks)
            })
            
    unique_connections = []
    seen_urls = set()
    for conn in connections_info:
        if conn["profile_url"] not in seen_urls:
            seen_urls.add(conn["profile_url"])
            unique_connections.append(conn)
            
    return unique_connections[:max_connections]

def send_connection_request(page, profile_url: str) -> bool:
    """
    Send a connection request WITHOUT a note — matches workflow_sender.py logic.
    Simple selectors: 'main button:has-text("Connect")' then 'Send without a note'.
    """
    print(f"Sending connection request to {profile_url}...")
    page.goto(profile_url)
    time.sleep(3)

    try:
        # Try finding the primary Connect button
        connect_btn = page.query_selector('main button:has-text("Connect")')

        if not connect_btn:
            # Look in the "More" dropdown
            more_btn = page.query_selector('main button:has-text("More")')
            if more_btn:
                more_btn.click()
                time.sleep(1)
                connect_btn = page.query_selector(
                    'div.artdeco-dropdown__content button:has-text("Connect"), '
                    'div.artdeco-dropdown__content div:has-text("Connect")'
                )

        if connect_btn:
            connect_btn.click()
            time.sleep(2)

            # Send without a note (per user's preference from workflow_sender.py)
            send_btn = page.query_selector(
                'button[aria-label="Send without a note"], '
                'button[aria-label="Send now"], '
                'button:has-text("Send")'
            )
            if send_btn:
                send_btn.click()
                print("-> Connection request sent successfully (without note)!")
                time.sleep(2)
                return True
            else:
                print("-> Could not find Send button after clicking Connect.")
        else:
            print("-> Connect button not found. Already connected, pending, or 3rd degree without option.")
    except Exception as e:
        print(f"-> Failed to send connection request: {e}")
    return False


def extract_connections_from_company_page(page, company_url: str, max_connections: int = 5, network: str = None, require_connect: bool = False) -> list:
    """
    Extract connections from company's People page. Returns list of dicts with
    first_name, profile_url, is_1st_degree. No URL resolution step — URLs are
    taken directly from the DOM and cleaned of query params.
    """
    url = f"{company_url}people/"
    if network:
        url += f"?facetNetwork={network}"
        
    print(f"Navigating to Company People page: {url}")
    page.goto(url)
    time.sleep(5)
    
    connections_info = []
    seen_urls = set()
    
    if require_connect:
        selector = '.org-people-profile-card__profile-card-spacing button:has-text("Connect")'
    else:
        selector = '.org-people-profile-card__profile-card-spacing button:has-text("Connect"), .org-people-profile-card__profile-card-spacing button:has-text("Message")'
        
    scroll_attempts = 0
    max_scrolls = 60
    
    while len(connections_info) < max_connections and scroll_attempts < max_scrolls:
        buttons = page.query_selector_all(selector)
        
        for btn in buttons:
            if len(connections_info) >= max_connections:
                break
                
            try:
                if btn.is_visible() and btn.is_enabled():
                    btn_text = btn.inner_text().strip()
                    is_1st_degree = ("Message" in btn_text)
                    
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
                            
                        if profile_url in seen_urls:
                            continue
                            
                        # Extract name
                        name_el = card.query_selector('.org-people-profile-card__profile-title, .artdeco-entity-lockup__title')
                        if name_el:
                            full_name = name_el.inner_text().strip()
                            if full_name and len(full_name.split()) > 0:
                                first_name = full_name.split()[0]
                                
                        if not first_name:
                            img_els = card.query_selector_all('img[alt]')
                            for img_el in img_els:
                                full_name = (img_el.get_attribute('alt') or "").strip()
                                if full_name and full_name.lower() not in ("", "linkedin member"):
                                    first_name = full_name.split()[0]
                                    break
                                    
                    if profile_url and first_name:
                        seen_urls.add(profile_url)
                        print(f"Found person: {first_name} (1st Degree: {is_1st_degree}) -> {profile_url}")
                        connections_info.append({
                            "first_name": first_name,
                            "profile_url": profile_url,
                            "is_1st_degree": is_1st_degree
                        })
            except Exception:
                pass
                
        if len(connections_info) >= max_connections:
            break
            
        # Scroll to load more cards
        page.keyboard.press("End")
        time.sleep(1.5)
        scroll_attempts += 1
            
    return connections_info
