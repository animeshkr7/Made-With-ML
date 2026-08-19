import os
import glob
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

def get_latest_file(directory: str, pattern: str) -> str:
    files = glob.glob(os.path.join(directory, pattern))
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def get_time_slot() -> str:
    hour = datetime.now().hour
    if hour < 10:
        return "Morning"
    elif hour < 13:
        return "Noon"
    elif hour < 16:
        return "Evening"
    else:
        return "Night"

def _get_filter():
    """Lazily import filter_utils from linkedin_monitor."""
    import sys
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    monitor_dir = os.path.join(base_dir, "email_processor", "linkedin_monitor")
    if monitor_dir not in sys.path:
        sys.path.append(monitor_dir)
    try:
        from filter_utils import load_config, should_exclude_post
        config = load_config()
        return config, should_exclude_post
    except Exception as e:
        print(f"Warning: Could not load filter_utils: {e}. Uploading all posts unfiltered.")
        return None, None

def _upload_posts(supabase: Client, posts: list, is_ai: bool = False):
    """Insert posts into Supabase, skipping already-existing ones by URL."""
    config, should_exclude_post = _get_filter()
    
    synced_count = 0
    skipped_count = 0
    date_str = datetime.now().strftime("%d-%m-%y")
    source_label = "llm" if is_ai else "email"

    for post in posts:
        # Apply the same keyword filter used by the notification pipeline
        if config and should_exclude_post:
            text = post.get('text', '')
            is_excluded, reason = should_exclude_post(text, config)
            if is_excluded:
                skipped_count += 1
                continue

        post_id = str(post.get('id', ''))
        url = post.get('url', '')

        # Check if already exists based on URL
        try:
            response = supabase.table('scraped_posts').select("id").eq("url", url).execute()
            if response.data:
                print(f"Post {post_id} already exists in Supabase. Skipping.")
                continue
        except Exception as e:
            print(f"Warning: Could not check if post exists (is the table created?): {e}")
            break

        # Insert new
        try:
            supabase.table('scraped_posts').insert({
                "post_id": post_id,
                "author": post.get("author", "Unknown"),
                "text": post.get("text", ""),
                "url": url,
                "emails": post.get("extracted_emails", []),
                "date": date_str,
                "slot": get_time_slot(),
                "is_ai": is_ai,
                "source": source_label,
                "llm_evaluation": post.get("llm_evaluation", None),
            }).execute()
            synced_count += 1
            print(f"Synced post {post_id} ({source_label}) to Supabase.")
        except Exception as e:
            print(f"Failed to sync post {post_id}: {e}")

    print(f"  -> {synced_count} new posts added, {skipped_count} skipped by keyword filter.")
    return synced_count

def sync_to_supabase(target_file=None, llm_file=None):
    print("\n--- Starting Supabase Sync ---")
    # Load environment variables
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(base_dir, '.env'))
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Missing Supabase credentials in .env")
        return
        
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    output_dir = os.path.join(base_dir, "email_processor", "linkedin_monitor", "output")
    
    # --- Sync regex-email posts (is_ai=False) ---
    if not target_file:
        target_file = get_latest_file(output_dir, "*_with_emails.json")
    
    if target_file and os.path.exists(target_file):
        print(f"\n[Flow A] Syncing email posts from: {target_file}")
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                posts = json.load(f)
            _upload_posts(supabase, posts, is_ai=False)
        except Exception as e:
            print(f"Failed to load json file: {e}")
    else:
        print("[Flow A] No recent *_with_emails.json files found.")
    
    # --- Sync LLM-curated posts (is_ai=True) ---
    if not llm_file:
        llm_file = get_latest_file(output_dir, "*_llm_curated.json")
    
    if llm_file and os.path.exists(llm_file):
        print(f"\n[Flow B] Syncing LLM curated posts from: {llm_file}")
        try:
            with open(llm_file, 'r', encoding='utf-8') as f:
                llm_posts = json.load(f)
            _upload_posts(supabase, llm_posts, is_ai=True)
        except Exception as e:
            print(f"Failed to load LLM curated json file: {e}")
    else:
        print("[Flow B] No recent *_llm_curated.json files found.")

    print(f"\nSync complete!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        sync_to_supabase(sys.argv[1])
    else:
        sync_to_supabase()
