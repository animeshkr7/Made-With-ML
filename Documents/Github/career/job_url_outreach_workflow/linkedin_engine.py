import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Add path to email_processor/linkedin_message_request for module imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINKEDIN_MODULE_DIR = os.path.join(BASE_DIR, 'email_processor', 'linkedin_message_request')
if LINKEDIN_MODULE_DIR not in sys.path:
    sys.path.insert(0, LINKEDIN_MODULE_DIR)

load_dotenv(os.path.join(BASE_DIR, '.env'))
load_dotenv(os.path.join(LINKEDIN_MODULE_DIR, '.env'))

from modules.scraper import scrape_job_url
from modules.llm import extract_job_details, generate_draft_message
from modules.linkedin_core import handle_login, find_exact_company_name, extract_connections_from_company_page, send_connection_request


def process_job_url(job_url: str) -> dict:
    """
    Follows the same flow as workflow_generate_drafts.py:
    1. Scrape job page
    2. Extract company/title/id via LLM
    3. Find company on LinkedIn
    4. Get 1st degree connections FIRST, then 2nd/3rd degree with Connect buttons
    5. Combine: 1st degree first, fill remaining slots with new connections
    6. Generate drafts for all, send connection requests (without note) for non-1st degree
    """
    print(f"\n--- Processing Job URL: {job_url} ---")
    
    # 1. Scrape Job Page Text
    job_text = scrape_job_url(job_url)
    
    # 2. Extract Details via LLM
    details = extract_job_details(job_url, job_text)
    company_name = details.get("company_name", "Company")
    job_title = details.get("job_title", "Role")
    job_id = details.get("job_id", "N/A")
    
    if not company_name or len(company_name) > 100:
        company_name = "Target Company"

    # 3. Locate LinkedIn Session & Open Browser
    state_file = os.path.join(BASE_DIR, 'email_processor', 'linkedin_monitor', 'state.json')
    connections = []
    exact_company_name = company_name

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        if os.path.exists(state_file):
            print("Loading saved LinkedIn session state...")
            context = browser.new_context(
                storage_state=state_file,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        else:
            print("[WARN] State.json not found! Browser authentication may be required.")
            context = browser.new_context()

        page = context.new_page()

        try:
            page.goto("https://www.linkedin.com/feed/", timeout=25000)
            if page.query_selector(".login__form, .alternate-signin-container, .join-form-container, #username"):
                print("Session expired. Attempting automated login...")
                if not handle_login(page, state_file):
                    print("[ERROR] Failed to authenticate with LinkedIn.")
                    browser.close()
                    return {
                        "job_url": job_url,
                        "company_name": company_name,
                        "job_title": job_title,
                        "connections": [],
                        "error": "LinkedIn Authentication Failed"
                    }

            # Search native LinkedIn for company page
            print(f"Searching LinkedIn for company: '{company_name}'...")
            found_company, company_url = find_exact_company_name(page, company_name)
            if found_company:
                exact_company_name = found_company

            raw_connections = []
            if company_url:
                print(f"Navigating to company page: {company_url}")
                
                # === MATCH workflow_generate_drafts.py LOGIC (lines 60-83) ===
                # Step 1: Get 1st degree connections from company people page
                first_degree = extract_connections_from_company_page(
                    page, company_url, max_connections=5, network="F"
                )
                
                # Step 2: Get new connections with Connect buttons
                new_conns = extract_connections_from_company_page(
                    page, company_url, max_connections=5, network=None, require_connect=True
                )
                
                # Step 3: Combine — 1ST DEGREE FIRST, then fill with new connections
                final_connections = []
                seen_urls = set()
                
                # Add 1st degree first (up to 3)
                for conn in first_degree[:3]:
                    p_url = conn.get("profile_url")
                    if p_url and p_url not in seen_urls:
                        seen_urls.add(p_url)
                        final_connections.append(conn)
                
                # Fill remaining slots with new connections (up to total of 5)
                for conn in new_conns:
                    if len(final_connections) >= 5:
                        break
                    p_url = conn.get("profile_url")
                    if p_url and p_url not in seen_urls:
                        seen_urls.add(p_url)
                        final_connections.append(conn)
                
                # If still have room, add more 1st degree
                for conn in first_degree[3:]:
                    if len(final_connections) >= 5:
                        break
                    p_url = conn.get("profile_url")
                    if p_url and p_url not in seen_urls:
                        seen_urls.add(p_url)
                        final_connections.append(conn)
                
                raw_connections = final_connections
            else:
                print(f"[WARN] Company page URL not found for {company_name}")

            # 4. Generate drafts and send connection requests (without note) while browser is open
            for conn in raw_connections:
                first_name = conn.get("first_name", "")
                is_1st = conn.get("is_1st_degree", False)
                p_url = conn.get("profile_url", "")

                draft_msg = generate_draft_message(
                    person_name=first_name,
                    company=exact_company_name,
                    title=job_title,
                    job_id=job_id,
                    job_url=job_url,
                    is_connected=is_1st
                )

                request_sent = False
                if not is_1st and p_url:
                    print(f"--> Non 1st-degree connection ({first_name}). Sending connection request (no note)...")
                    request_sent = send_connection_request(page, p_url)

                connections.append({
                    "name": first_name or "Contact",
                    "profile_url": p_url,
                    "is_1st_degree": is_1st,
                    "request_sent": request_sent,
                    "draft_message": draft_msg
                })

        except Exception as e:
            print(f"[WARN] Playwright LinkedIn lookup encountered error: {e}")
        finally:
            browser.close()

    if not connections:
        print("No connections retrieved. Generating default draft message...")
        default_draft = generate_draft_message(
            person_name="",
            company=exact_company_name,
            title=job_title,
            job_id=job_id,
            job_url=job_url,
            is_connected=False
        )
        connections.append({
            "name": "General Contact",
            "profile_url": f"https://www.linkedin.com/company/{exact_company_name.lower().replace(' ', '-')}",
            "is_1st_degree": False,
            "request_sent": False,
            "draft_message": default_draft
        })

    return {
        "job_url": job_url,
        "company_name": exact_company_name,
        "job_title": job_title,
        "connections": connections
    }

if __name__ == "__main__":
    test_url = "https://jobs.ashbyhq.com/supabase/test"
    res = process_job_url(test_url)
    print("Process Result:", json.dumps(res, indent=2))
