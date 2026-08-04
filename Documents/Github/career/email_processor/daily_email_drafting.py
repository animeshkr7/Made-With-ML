import os
import json
import urllib.request
from datetime import datetime, timedelta

# Import our batch processor
import batch_draft

def run_daily_drafting():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # 1. Calculate yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime("%d-%m-%y")
    print(f"Starting daily drafting task for date: {date_str}")

    # 2. Fetch data from Render API
    url = f"https://email-creator-api.onrender.com/fetch_by_date?date={date_str}"
    output_file = os.path.join(data_dir, f"fetched_data_{date_str}.json")
    
    print(f"Fetching data from {url}...")
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                # Save to file
                with open(output_file, 'w', encoding='utf-8-sig') as f:
                    json.dump(data, f, indent=4)
                print(f"Successfully saved data to {output_file}")
            else:
                print(f"Failed to fetch data. HTTP Status: {response.status}")
                return
    except Exception as e:
        print(f"Error fetching data from API: {e}")
        return

    # 3. Process the batch
    print("Initiating batch processing...")
    batch_draft.process_batch(output_file)
    print("Daily drafting task completed successfully.")

if __name__ == "__main__":
    run_daily_drafting()
