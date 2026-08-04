import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Add paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_DIR = os.path.dirname(os.path.abspath(__file__))
if WORKFLOW_DIR not in sys.path:
    sys.path.insert(0, WORKFLOW_DIR)

# Load environment variables
load_dotenv(os.path.join(BASE_DIR, '.env'))
load_dotenv(os.path.join(BASE_DIR, 'email_processor', '.env'))
load_dotenv(os.path.join(BASE_DIR, 'email_processor', 'linkedin_message_request', '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment or .env files.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

from linkedin_engine import process_job_url
from notifier import send_job_outreach_notification

def get_target_dates() -> list[str]:
    """Returns today's and yesterday's dates formatted as DD-MM-YY."""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    return [today.strftime("%d-%m-%y"), yesterday.strftime("%d-%m-%y")]

def run_outreach_workflow():
    dates = get_target_dates()
    print(f"\n==================================================")
    print(f"[START] Automated Job URL Outreach Workflow")
    print(f"[DATE] Target Dates: {dates[0]} (Today), {dates[1]} (Yesterday)")
    print(f"==================================================")

    # 1. Fetch records matching today's or yesterday's date
    all_records = []
    for d in dates:
        try:
            res = supabase.table('job_url').select('*').eq('date', d).execute()
            if res.data:
                all_records.extend(res.data)
        except Exception as e:
            print(f"[ERROR] Querying Supabase for date {d}: {e}")

    if not all_records:
        print("[INFO] No job URL records found for today or yesterday.")
        return

    # 2. Filter records where status is 'Pending'
    pending_records = [
        r for r in all_records 
        if r.get('status') and str(r.get('status')).strip().lower() == 'pending'
    ]

    print(f"[INFO] Found {len(all_records)} total records across target dates.")
    print(f"[INFO] Found {len(pending_records)} pending job URLs to process.")

    if not pending_records:
        print("[SUCCESS] No pending job URLs to process. Everything up to date!")
        return

    # 3. Process each pending record
    for idx, record in enumerate(pending_records, 1):
        rec_id = record.get('id')
        job_url = record.get('url')
        rec_date = record.get('date')

        print(f"\n--- [{idx}/{len(pending_records)}] Processing Record ID #{rec_id} (Date: {rec_date}) ---")
        print(f"URL: {job_url}")

        # Update status to In-Process
        try:
            supabase.table('job_url').update({'status': 'In-Process'}).eq('id', rec_id).execute()
            print("Status updated to: 'In-Process'")
        except Exception as e:
            print(f"[WARN] Failed to update status to In-Process: {e}")

        # Execute LinkedIn engine & draft generation
        try:
            result_data = process_job_url(job_url)
            
            company_name = result_data.get('company_name', 'Company')
            job_title = result_data.get('job_title', 'Role')
            connections = result_data.get('connections', [])

            # Send Email Notification
            sent = send_job_outreach_notification(
                job_url=job_url,
                company_name=company_name,
                job_title=job_title,
                connections_data=connections
            )

            # Update status to Completed
            final_status = 'Completed' if sent else 'Completed (No Email)'
            supabase.table('job_url').update({'status': final_status}).eq('id', rec_id).execute()
            print(f"[SUCCESS] Record #{rec_id} successfully processed and updated to '{final_status}'!")

        except Exception as e:
            print(f"[ERROR] Processing record #{rec_id}: {e}")
            try:
                supabase.table('job_url').update({'status': 'Failed'}).eq('id', rec_id).execute()
            except Exception as update_err:
                print(f"Failed to set status to Failed: {update_err}")

    print(f"\n[COMPLETE] Workflow Execution Finished! Processed {len(pending_records)} pending items.")


if __name__ == "__main__":
    run_outreach_workflow()
