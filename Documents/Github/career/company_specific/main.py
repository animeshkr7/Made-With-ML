import json
import importlib
import logging
import argparse
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def load_registry(registry_path="registry.json"):
    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)

def filter_and_save_jobs(company_info, jobs, timeframe):
    now = datetime.now(timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if timeframe == "day":
        start_bound = start_of_today - timedelta(days=1)
        end_bound = start_of_today
        timeframe_label = "Yesterday"
    elif timeframe == "week":
        start_bound = start_of_today - timedelta(days=7)
        end_bound = now
        timeframe_label = "Last Week"
    else: # month
        start_bound = start_of_today - timedelta(days=30)
        end_bound = now
        timeframe_label = "Last Month"
    
    filtered_jobs = []
    
    for job in jobs:
        raw_date = job.get("published_at") 
        if raw_date:
            try:
                posted_at = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
                if posted_at.tzinfo is None:
                    posted_at = posted_at.replace(tzinfo=timezone.utc)
                
                if start_bound <= posted_at < end_bound:
                    filtered_jobs.append({
                        "title": job.get("title", "N/A"),
                        "location": job.get("location", "N/A"),
                        "url": job.get("url", company_info["career_url"]), 
                        "posted_at": posted_at
                    })
            except Exception as e:
                logging.error(f"Could not parse date {raw_date}: {e}")
                
    if filtered_jobs:
        md_file = os.path.join("outputs", f"{company_info['id']}_{timeframe}_jobs.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"# {company_info['name']} Job Postings ({timeframe_label})\n\n")
            f.write("| Company | Job Title | Location | Posted At (UTC) | Link |\n")
            f.write("|---|---|---|---|---|\n")
            
            for job in filtered_jobs:
                title = str(job["title"]).replace('|', '-')
                location = str(job["location"]).replace('|', '-')
                posted_at_str = job["posted_at"].strftime('%Y-%m-%d %H:%M:%S')
                
                f.write(f"| **{company_info['name']}** | {title} | {location} | {posted_at_str} | [Apply]({job['url']}) |\n")
                
        logging.info(f"[SUCCESS] Successfully wrote {len(filtered_jobs)} jobs to {md_file}")
    else:
        logging.info(f"[INFO] No jobs were posted in the {timeframe_label.lower()} by {company_info['name']}")
        
    return filtered_jobs

if __name__ == "__main__":
    default_tf = os.getenv("DEFAULT_TIMEFRAME", "day")
    
    parser = argparse.ArgumentParser(description="Scrape ATS jobs for all registered companies.")
    parser.add_argument("--timeframe", choices=["day", "week", "month"], default=default_tf, help=f"Timeframe to filter jobs by (day, week, month). Default from .env: {default_tf}")
    args = parser.parse_args()
    
    # 1. Ensure outputs directory exists
    os.makedirs("outputs", exist_ok=True)
    
    # 2. Load registry
    registry = load_registry()
    
    all_combined_jobs = []
    
    # 3. Iterate through companies and run their scrapers
    for company in registry.get("companies", []):
        logging.info(f"--- Starting scrape for {company['name']} ---")
        module_name = company["scraper_module"]
        
        try:
            # Dynamically import the scraper module for this company
            scraper_module = importlib.import_module(module_name)
            
            # Execute its scrape() function
            jobs = scraper_module.scrape()
            
            # Filter and output to markdown
            company_filtered_jobs = filter_and_save_jobs(company, jobs, args.timeframe)
            
            # Add company identifier to JSON payload
            for c_job in company_filtered_jobs:
                c_job["company_id"] = company["id"]
                c_job["company_name"] = company["name"]
                # Convert datetime to ISO string for JSON serialization
                c_job["posted_at"] = c_job["posted_at"].isoformat()
            
            all_combined_jobs.extend(company_filtered_jobs)
            
        except ImportError as e:
            logging.error(f"Could not import scraper module {module_name}: {e}")
        except AttributeError as e:
            logging.error(f"Scraper module {module_name} does not have a scrape() function: {e}")
        except Exception as e:
            logging.error(f"Error scraping {company['name']}: {e}")

    # 4. Save Combined JSON
    combined_json_path = os.path.join("outputs", f"combined_{args.timeframe}_jobs.json")
    with open(combined_json_path, "w", encoding="utf-8") as f:
        json.dump(all_combined_jobs, f, indent=4)
        
    logging.info(f"[SUCCESS] Wrote combined JSON with {len(all_combined_jobs)} total jobs to {combined_json_path}")
