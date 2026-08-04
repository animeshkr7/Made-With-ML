import os
import sys
import glob
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

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from connection_monitor.modules.checker import check_profile_connection_status
from connection_monitor.modules.drafter import generate_accepted_referral_message
from connection_monitor.modules.notifier import send_connection_accepted_email

load_dotenv()

def run_connection_monitor():
    print("\n=======================================================")
    print("      Starting Connection Acceptance Monitor Workflow   ")
    print("=======================================================")

    # Locate session state
    state_file = os.path.join(email_processor_dir, 'linkedin_monitor', 'state.json')

    # Gather target JSON files
    search_paths = [
        os.path.join(email_processor_dir, 'company_outreach_service', '*.json'),
        os.path.join(email_processor_dir, 'job_link_outreach_service', '*.json'),
        os.path.join(os.path.dirname(email_processor_dir), 'monitor', 'input', '*.json')
    ]

    target_json_files = []
    for path_pattern in search_paths:
        target_json_files.extend(glob.glob(path_pattern))

    # Exclude system JSONs
    target_json_files = [f for f in target_json_files if not os.path.basename(f).startswith("targets") and not os.path.basename(f).startswith("removed")]

    print(f"Found {len(target_json_files)} target report file(s) to monitor.\n")

    if not target_json_files:
        print("No report files found to monitor. Exiting.")
        return

    notifications_sent_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        if os.path.exists(state_file):
            print(f"Loading saved LinkedIn session from: {state_file}")
            context = browser.new_context(
                storage_state=state_file,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        else:
            print("WARNING: state.json not found! Running in fresh context...")
            context = browser.new_context()

        page = context.new_page()

        # Check authentication
        page.goto("https://www.linkedin.com/feed/")
        time.sleep(3)

        for filepath in target_json_files:
            filename = os.path.basename(filepath)
            print(f"\n--- Checking Report File: {filename} ---")

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Error reading JSON file {filename}: {e}")
                continue

            if isinstance(data, dict):
                company_name = data.get("company_name", "Target Company")
                requests_sent = data.get("new_connection_requests_sent", [])
            elif isinstance(data, list):
                clean_name = filename.split('.')[0]
                company_name = clean_name.split("-")[1].capitalize() if "-" in clean_name else clean_name
                requests_sent = data
            else:
                continue

            if not requests_sent:
                print(f"No pending connection requests found in {filename}.")
                continue

            file_modified = False

            for item in requests_sent:
                profile_url = item.get("profile_url") or item.get("connection_profile_url")
                first_name = item.get("first_name")
                if not first_name and profile_url:
                    first_name = profile_url.rstrip("/").split("/")[-1].split("-")[0].capitalize()
                if not first_name:
                    first_name = "Connection"

                already_notified = item.get("notification_sent", False)

                # Skip if already notified
                if already_notified:
                    print(f" -> [SKIP] {first_name} ({profile_url}): Notification already sent.")
                    continue

                # Check current profile status on LinkedIn
                current_status = check_profile_connection_status(page, profile_url)

                if current_status == "Accepted":
                    print(f" -> [ACCEPTED] Connection ACCEPTED by {first_name}!")
                    
                    # Generate customized draft message
                    draft_msg = generate_accepted_referral_message(
                        first_name=first_name,
                        company=company_name
                    )

                    # Send email alert
                    email_success = send_connection_accepted_email(
                        person_name=first_name,
                        profile_url=profile_url,
                        company_name=company_name,
                        draft_message=draft_msg
                    )

                    # Update item record with flags
                    item["status"] = "Accepted"
                    item["notification_sent"] = True
                    item["notification_date"] = datetime.now().isoformat()
                    item["draft_message"] = draft_msg
                    file_modified = True
                    notifications_sent_count += 1

                elif current_status == "Not Connected":
                    item["status"] = "Not Connected"
                    file_modified = True

            # Save updated report back to disk immediately
            if file_modified:
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f" -> Saved updated status & flags back to {filename}.")
                except Exception as e:
                    print(f" -> Error saving updated JSON to {filename}: {e}")

        browser.close()

    print("\n=======================================================")
    print(f" Monitor Complete! Total New Alerts Sent: {notifications_sent_count}")
    print("=======================================================")

def main():
    run_connection_monitor()

if __name__ == "__main__":
    main()
