import os
import sys

# Add the subdirectories to sys.path so we can import them
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_dir, 'linkedin_monitor'))
sys.path.append(os.path.join(base_dir, 'post_processor'))

from linkedin_monitor.linkedin_scraper import run_scraper
from post_processor.filter_emails import process_posts
from post_processor.send_notification import send_notification
from post_processor.llm_post_filter import process_posts_llm
from post_processor.send_llm_job_notification import send_llm_job_notification

sys.path.append(os.path.join(base_dir, '..', 'supabase_sync'))
from sync_to_supabase import sync_to_supabase

def run_pipeline():
    print("\n--- Starting LinkedIn Monitoring Pipeline ---")
    
    # 1. Scrape posts from the last 3 hours
    original_cwd = os.getcwd()
    os.chdir(os.path.join(base_dir, 'linkedin_monitor'))
    
    try:
        output_file = run_scraper(headless=True)
        if output_file:
            output_file = os.path.abspath(output_file)
    finally:
        os.chdir(original_cwd)
        
    if not output_file or not os.path.exists(output_file):
        print("Pipeline aborted: Scraper did not produce an output file.")
        return

    print(f"Scraper finished. Output saved to: {output_file}")
    
    # --- FLOW A: Regex Email Filter (Existing) ---
    print("\n==================================================")
    print("  FLOW A: Regex Email Filter & Notification       ")
    print("==================================================")
    flow_a_urls = set()  # Track URLs already notified in Flow A
    filtered_file = process_posts(output_file)
    if filtered_file and os.path.exists(filtered_file):
        print("Sending Flow A email notification...")
        send_notification(filtered_file)
        # Collect the URLs of posts that were emailed in Flow A for dedup in Flow B
        try:
            import json
            with open(filtered_file, 'r', encoding='utf-8') as _f:
                flow_a_posts = json.load(_f)
            flow_a_urls = {p.get('url', '') for p in flow_a_posts if p.get('url')}
            print(f"Flow A: {len(flow_a_urls)} post URLs will be excluded from Flow B.")
        except Exception as _e:
            print(f"Flow A: Could not read filtered posts for dedup: {_e}")
    else:
        print("Flow A: No posts containing raw emails were found.")

    # --- FLOW B: Parallel LLM Post Evaluator (New) ---
    print("\n==================================================")
    print("  FLOW B: Parallel LLM Evaluator (Q1/Q2/Q3)       ")
    print("==================================================")
    try:
        llm_curated_file = process_posts_llm(output_file, batch_size=7, exclude_urls=flow_a_urls)
        if llm_curated_file and os.path.exists(llm_curated_file):
            print("Sending Flow B LLM curated job email notification...")
            send_llm_job_notification(llm_curated_file)
        else:
            print("Flow B: No qualified LLM posts found to email.")
    except Exception as e:
        print(f"Flow B LLM Evaluator error: {e}")

    # --- FLOW C: Sync to Supabase ---
    print("\n==================================================")
    print("  FLOW C: Sync Scraped Posts to Supabase          ")
    print("==================================================")
    try:
        sync_to_supabase()
    except Exception as e:
        print(f"Failed to sync to Supabase: {e}")

    print("\n==================================================")
    print("--- LinkedIn Monitoring Pipeline Completed! ---")
    print("==================================================")

if __name__ == "__main__":
    run_pipeline()
