import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

base_dir = os.path.dirname(os.path.abspath(__file__))
email_processor_dir = os.path.dirname(base_dir)
if email_processor_dir not in sys.path:
    sys.path.insert(0, email_processor_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from company_outreach_service.modules.llm import generate_referral_draft
from company_outreach_service.modules.linkedin_core import (
    handle_login,
    resolve_company_url_and_name,
    extract_1st_degree_connections,
    send_new_connection_requests,
    send_email_notification
)

load_dotenv()

def run_outreach_workflow(target_input: str):
    print("\n=======================================================")
    print("      Starting LinkedIn Company Outreach Workflow      ")
    print("=======================================================")
    print(f"Target Input: {target_input}")

    # Determine state file location
    email_processor_dir = os.path.dirname(base_dir)
    state_file = os.path.join(email_processor_dir, 'linkedin_monitor', 'state.json')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Non-headless for visual verification and stability
        
        if os.path.exists(state_file):
            print(f"Loading saved session state from: {state_file}")
            context = browser.new_context(
                storage_state=state_file,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        else:
            print("WARNING: state.json not found! Proceeding with fresh browser session...")
            context = browser.new_context()

        page = context.new_page()

        # Check authentication
        page.goto("https://www.linkedin.com/feed/")
        time.sleep(3)
        if page.query_selector(".login__form, .alternate-signin-container, #username"):
            print("Session expired or not logged in. Attempting login...")
            if not handle_login(page, state_file):
                print("Authentication failed. Exiting workflow.")
                browser.close()
                return

        # 1. Resolve Company URL & Name
        exact_company_name, company_url = resolve_company_url_and_name(page, target_input)
        if not company_url:
            print(f"Error: Could not resolve LinkedIn Company URL for target '{target_input}'. Exiting.")
            browser.close()
            return

        print(f"\nTarget Company: '{exact_company_name}'")
        print(f"Company Page URL: {company_url}")

        # 2. Step 1: Check 1st-degree connections (Max 5 to draft)
        first_degree_conns = extract_1st_degree_connections(page, company_url, max_count=5)
        
        drafts = []
        for conn in first_degree_conns:
            draft_msg = generate_referral_draft(
                person_name=conn["first_name"],
                company=exact_company_name,
                title="Role",
                job_id="N/A",
                job_url=""
            )
            drafts.append({
                "first_name": conn["first_name"],
                "profile_url": conn["profile_url"],
                "is_1st_degree": True,
                "draft_message": draft_msg
            })

        # 3. Step 2: Connect to new people on unfiltered people page
        # Calculation formula: max(3, 5 - count_1st_degree)
        count_1st_degree = len(first_degree_conns)
        num_to_connect = max(3, 5 - count_1st_degree)

        print(f"\n--- Connection Request Formula ---")
        print(f"1st-Degree Connections Found: {count_1st_degree}")
        print(f"Calculated New Connection Target: max(3, 5 - {count_1st_degree}) = {num_to_connect}")

        new_connections_sent = send_new_connection_requests(page, company_url, num_to_connect=num_to_connect)

        browser.close()

    # 4. Save Results to JSON
    current_date = datetime.now().strftime("%d%m%y")
    safe_company_name = "".join(c for c in exact_company_name if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_').upper()
    filename = f"{current_date}-{safe_company_name}.json"
    output_path = os.path.join(base_dir, filename)

    output_payload = {
        "company_name": exact_company_name,
        "company_url": company_url,
        "execution_date": datetime.now().isoformat(),
        "1st_degree_count": count_1st_degree,
        "1st_degree_referral_drafts": drafts,
        "new_connection_requests_target": num_to_connect,
        "new_connection_requests_sent": new_connections_sent
    }

    json_output_str = json.dumps(output_payload, indent=2, ensure_ascii=False)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json_output_str)

    # 5. Build Human-Readable Email Notification
    email_body = f"""==================================================
LINKEDIN OUTREACH REPORT: {exact_company_name}
Date: {current_date}
Company Page: {company_url}
==================================================

1ST-DEGREE REFERRAL DRAFTS ({count_1st_degree} found):
--------------------------------------------------"""

    if drafts:
        for idx, d in enumerate(drafts, 1):
            msg = d.get("draft_message", "").replace("\\n", "\n")
            email_body += f"\n\n[{idx}] {d.get('first_name')} ({d.get('profile_url')})\nDraft Message:\n{msg}\n"
            email_body += "-" * 40
    else:
        email_body += "\nNo 1st-degree connections found."

    email_body += f"\n\nNEW CONNECTION REQUESTS SENT (Target: {num_to_connect}):\n--------------------------------------------------"
    if new_connections_sent:
        for idx, c in enumerate(new_connections_sent, 1):
            email_body += f"\n{idx}. {c.get('first_name')} ({c.get('profile_url')}) - Sent"
    else:
        email_body += "\nNo new connection requests sent."

    email_subject = f"LinkedIn Outreach Report - {exact_company_name} ({current_date})"
    send_email_notification(email_subject, email_body)

    print("\n=======================================================")
    print(f"  Workflow Complete! Output saved to: {filename}       ")
    print("=======================================================")

def main():
    if len(sys.argv) < 2:
        print("Usage: python workflow.py \"<COMPANY_NAME | COMPANY_URL | JOB_URL | PROFILE_URL>\"")
        print("Example: python workflow.py \"Colgate Palmolive\"")
        sys.exit(1)

    target_input = sys.argv[1]
    run_outreach_workflow(target_input)

if __name__ == "__main__":
    main()
