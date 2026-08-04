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

def sync_to_supabase(target_file=None):
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
    
    if not target_file:
        output_dir = os.path.join(base_dir, "email_processor", "linkedin_monitor", "output")
        target_file = get_latest_file(output_dir, "*_with_emails.json")
    
    if not target_file or not os.path.exists(target_file):
        print("No recent *_with_emails.json files found.")
        return
        
    print(f"Syncing from file: {target_file}")
    
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            posts = json.load(f)
    except Exception as e:
        print(f"Failed to load json file: {e}")
        return
        
    if not posts:
        print("No posts to sync.")
        return
        
    synced_count = 0
    # Use DD-MM-YY to match existing API formats
    date_str = datetime.now().strftime("%d-%m-%y")
    
    for post in posts:
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
                "date": date_str
            }).execute()
            synced_count += 1
            print(f"Synced post {post_id} to Supabase.")
        except Exception as e:
            print(f"Failed to sync post {post_id}: {e}")
            
    print(f"Sync complete! {synced_count} new posts added.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        sync_to_supabase(sys.argv[1])
    else:
        sync_to_supabase()
