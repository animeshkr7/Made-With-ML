import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from modules.scraper import scrape_job_url
from modules.llm import extract_job_details, generate_draft_message
from modules.linkedin_core import handle_login, find_exact_company_name, extract_connections, send_connection_request, extract_connections_from_company_page

load_dotenv()

def run_workflow(job_url: str):
    print("\n--- Starting Referral Draft Generation Workflow ---")
    # 1. Scrape URL
    text = scrape_job_url(job_url)
    
    # 2. Extract Details
    details = extract_job_details(job_url, text)
    company_name = details.get("company_name")
    
    if not company_name or len(company_name) > 100:
        print("Failed to extract a valid company name.")
        sys.exit(1)
        
    # 3. Open LinkedIn to find exact company name & connections
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state_file = os.path.join(base_dir, 'linkedin_monitor', 'state.json')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Can be headless since we are just scraping JSON
        
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
        
        # Go to a neutral page to check auth
        page.goto("https://www.linkedin.com/feed/")
        if page.query_selector(".login__form, .alternate-signin-container, .join-form-container, #username"):
            print("Session expired or LinkedIn is asking to log in. Attempting automatic login...")
            if not handle_login(page, state_file):
                print("Failed to authenticate. Exiting.")
                browser.close()
                return
                
        # Find exact company
        print(f"Searching native LinkedIn to find the exact company name for '{company_name}'...")
        exact_company_name, company_url = find_exact_company_name(page, company_name)
        
        connections = []
        if company_url:
            print(f"\nNavigating to company page to find 1st-degree connections...")
            first_degree = extract_connections_from_company_page(page, company_url, max_connections=5, network="F")
            
            print(f"\nSearching company page for new connections with available Connect buttons...")
            new_conns = extract_connections_from_company_page(page, company_url, max_connections=5, network=None, require_connect=True)
            
            # Combine logic: max 5 total, min 3 new connections (if available)
            final_connections = []
            
            # 1. Add up to 3 new connections to satisfy the minimum 3 requirement
            final_connections.extend(new_conns[:3])
            
            # 2. Fill remaining slots (up to 5) with 1st degree connections
            remaining_slots = 5 - len(final_connections)
            final_connections.extend(first_degree[:remaining_slots])
            
            # 3. If we STILL have slots left (not enough 1st degree), fill with any remaining new connections
            remaining_slots = 5 - len(final_connections)
            if remaining_slots > 0 and len(new_conns) > 3:
                final_connections.extend(new_conns[3:3+remaining_slots])
                
            connections = final_connections
        else:
            print(f"\nCould not find Company URL to perform search.")
            
        if not connections:
            print(f"No connections found at {exact_company_name}.")
            browser.close()
            return

        print(f"Found {len(connections)} total connections. Generating drafts...")
                
        browser.close()
    
    # 4. Generate JSON Output
    current_date = datetime.now().strftime("%d%m%y") # DDMMYY
    
    # Optional: sanitize company name for filename
    safe_company_name = "".join(c for c in exact_company_name if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_').upper()
    filename = f"{current_date}-{safe_company_name}.json"
    
    output_data = []
    
    for conn in connections:
        first_name = conn["first_name"]
        is_connected = conn["is_1st_degree"]
        
        draft_msg = generate_draft_message(
            person_name=first_name,
            company=exact_company_name,
            title=details.get("job_title", "Role"),
            job_id=details.get("job_id", "N/A"),
            job_url=job_url,
            is_connected=is_connected
        )
        
        record = {
            "job_link": job_url,
            "connection_profile_url": conn["profile_url"],
            "connected": is_connected,
            "draft_message": draft_msg,
            "date": datetime.now().isoformat()
        }
        output_data.append(record)
        
    # 5. Save JSON
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"\nWorkflow complete! Saved {len(output_data)} drafts to {filename}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python workflow_generate_drafts.py <job_url>")
        sys.exit(1)
        
    job_url = sys.argv[1]
    run_workflow(job_url)

if __name__ == "__main__":
    main()
