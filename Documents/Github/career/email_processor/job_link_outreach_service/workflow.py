import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

base_dir = os.path.dirname(os.path.abspath(__file__))
email_processor_dir = os.path.dirname(base_dir)
if email_processor_dir not in sys.path:
    sys.path.insert(0, email_processor_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from job_link_outreach_service.modules.job_scraper import fetch_job_text_chunk
from job_link_outreach_service.modules.llm_extractor import extract_company_and_details
from company_outreach_service.workflow import run_outreach_workflow

load_dotenv()

def process_job_link_and_outreach(job_url: str):
    print("\n=======================================================")
    print("      Starting Job Link to Outreach Pipeline           ")
    print("=======================================================")
    print(f"Target Job URL: {job_url}")

    # 1. Scrape & Chunk Top Content
    text_chunk = fetch_job_text_chunk(job_url, chunk_size=3500)
    if not text_chunk:
        print("Warning: Could not extract body text from URL. Proceeding with URL analysis...")

    # 2. Extract Company Name & Job Details via LLM
    details = extract_company_and_details(job_url, text_chunk)
    company_name = details.get("company_name")

    if not company_name or len(company_name) > 100:
        print("Error: Could not extract a valid company name from job link.")
        sys.exit(1)

    print(f"\nSuccessfully identified Company: '{company_name}'")
    print("Handing off to company_outreach_service...\n")

    # 3. Handoff to company_outreach_service
    run_outreach_workflow(company_name)

    print("\n=======================================================")
    print("  Job Link Pipeline & Company Outreach Complete!        ")
    print("=======================================================")

def main():
    if len(sys.argv) < 2:
        print("Usage: python workflow.py \"<JOB_CAREERS_URL>\"")
        print("Example: python workflow.py \"https://jobs.colgate.com/job/Mumbai-Data-Scientist-MH/173498-en_GB/?feedId=430400\"")
        sys.exit(1)

    job_url = sys.argv[1]
    process_job_link_and_outreach(job_url)

if __name__ == "__main__":
    main()
