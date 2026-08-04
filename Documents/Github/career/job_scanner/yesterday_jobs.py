import sys
import os
from datetime import datetime, timedelta, timezone

# Add ats-scrapers to python path if needed (assuming it's installed in the venv)
try:
    from jobhive.scrapers import get_scraper
except ImportError:
    print("Error: 'jobhive' not found. Make sure you are running this from your ats-scrapers virtual environment.")
    sys.exit(1)

def scrape_yesterdays_jobs(ats_name: str, company_slug: str):
    print(f"Fetching jobs for {company_slug} on {ats_name}...")
    
    # Initialize the scraper for the specific company
    scraper = get_scraper(ats_name, company_slug)
    jobs = scraper.fetch()
    
    # Calculate exact bounds for "yesterday" in UTC
    now = datetime.now(timezone.utc)
    
    # Start of today (midnight)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Start of yesterday
    start_of_yesterday = start_of_today - timedelta(days=1)
    
    print(f"Filtering for jobs posted strictly between:")
    print(f"  {start_of_yesterday} and {start_of_today}")
    
    # Filter logic
    yesterdays_jobs = []
    for job in jobs:
        # Check if the job has a posted_at date
        if job.posted_at:
            posted_at = job.posted_at
            # Make offset-naive datetimes timezone-aware
            if posted_at.tzinfo is None:
                posted_at = posted_at.replace(tzinfo=timezone.utc)
            
            # Check if it was posted >= start of yesterday AND < start of today
            if start_of_yesterday <= posted_at < start_of_today:
                yesterdays_jobs.append(job)

    print(f"Found {len(yesterdays_jobs)} jobs posted yesterday out of {len(jobs)} total jobs.")
    return yesterdays_jobs

if __name__ == "__main__":
    targets = [
    ("ashby", "aplazo"), # Recovered: Aplazo-
    ("workday", "https://arcticwolf.wd1.myworkdayjobs.com/external"), # Recovered: Artic wolf
    ("smartrecruiters", "deutschebank"), # Recovered: Deustshe Bank
    ("smartrecruiters", "deutschebank"), # Recovered: Duetsche Bank
    ("ashby", "elevenlabs"), # Recovered: Eleven labs

        ("ashby", "apple-roofing"),
        ("ashby", "ontic"),
        ("ashby", "plane"),
        ("ashby", "snowflake"),
        ("ashby", "the-flex"),
        ("avature", "harmanglobal"),
        ("bamboohr", "amd"),
        ("bamboohr", "seagate"),
        ("breezy", "degree-dash"),
        ("breezy", "google"),
        ("eightfold", "amdocs"),
        ("eightfold", "citi"),
        ("eightfold", "deere"),
        ("eightfold", "microsoft"),
        ("eightfold", "nvidia"),
        ("eightfold", "slb"),
        ("greenhouse", "6sense"),
        ("greenhouse", "baincapitalventures"),
        ("greenhouse", "byd"),
        ("greenhouse", "capco"),
        ("greenhouse", "crunchyroll"),
        ("greenhouse", "doordashaustralia"),
        ("greenhouse", "druva"),
        ("greenhouse", "elastic"),
        ("greenhouse", "kellerpostman"),
        ("greenhouse", "modulrfinance"),
        ("greenhouse", "nice"),
        ("greenhouse", "nimblegravity"),
        ("greenhouse", "pubmatic"),
        ("greenhouse", "razorpaysoftwareprivatelimited"),
        ("greenhouse", "siei"),
        ("greenhouse", "thousandeyes"),
        ("greenhouse", "zscaler"),
        ("icims", "cvent"),
        ("jazzhr", "eci"),
        ("join_com", "lg"),
        ("join_com", "onspire"),
        ("join_com", "urologie11"),
        ("lever", "aeratechnology"),
        ("lever", "amberelectric"),
        ("lever", "hotstar"),
        ("lever", "paytm"),
        ("lever", "payugpo"),
        ("lever", "rivr"),
        ("lever", "veritasinv"),
        ("lever", "zeta"),
        ("oracle", "hdjd"),
        ("recruiterbox", "helpshift"),
        ("smartrecruiters", "adobe1"),
        ("smartrecruiters", "aristanetworks"),
        ("smartrecruiters", "hitachisolutions"),
        ("smartrecruiters", "honeywell"),
        ("smartrecruiters", "icertis"),
        ("smartrecruiters", "mastercard"),
        ("smartrecruiters", "oracle"),
        ("smartrecruiters", "persistentsystems"),
        ("smartrecruiters", "servicenow"),
        ("smartrecruiters", "teamviewer1"),
        ("smartrecruiters", "virtusapolaris"),
        ("smartrecruiters", "zendesk"),
        ("successfactors", "jobs"),
        ("teamtailor", "atlassian"),
        ("workable", "dyson-farming"),
        ("workable", "nestle-waters-north-america"),
        ("workday", "https://allstate.wd5.myworkdayjobs.com/allstate_careers"),
        ("workday", "https://altera.wd1.myworkdayjobs.com/altera"),
        ("workday", "https://barclays.wd3.myworkdayjobs.com/external_career_site_barclays"),
        ("workday", "https://broadcom.wd1.myworkdayjobs.com/external_career"),
        ("workday", "https://copart.wd12.myworkdayjobs.com/copart"),
        ("workday", "https://crowdstrike.wd5.myworkdayjobs.com/crowdstrikecareers"),
        ("workday", "https://equifax.wd5.myworkdayjobs.com/campus"),
        ("workday", "https://fis.wd5.myworkdayjobs.com/searchjobs"),
        ("workday", "https://lseg.wd3.myworkdayjobs.com/careers"),
        ("workday", "https://rakuten.wd1.myworkdayjobs.com/kobo"),
        ("workday", "https://redhat.wd5.myworkdayjobs.com/jobs"),
        ("workday", "https://salesforce.wd12.myworkdayjobs.com/external_career_site"),
        ("workday", "https://salesforce.wd12.myworkdayjobs.com/slack"),
        ("workday", "https://synechron.wd1.myworkdayjobs.com/synechroncareers"),
        ("workday", "https://tiaa.wd1.myworkdayjobs.com/search"),
        ("workday", "https://walmart.wd5.myworkdayjobs.com/walmartexternal"),
        ("workday", "https://zelis.wd1.myworkdayjobs.com/zeliscareers"),
    ]

    results = {}
    for ats_name, company_slug in targets:
        try:
            jobs = scrape_yesterdays_jobs(ats_name, company_slug)
            if jobs:
                results[company_slug] = jobs
        except Exception as e:
            print(f"Error scraping {company_slug} on {ats_name}: {e}")
            print("-" * 50)

    # Write to Markdown
    if results:
        md_file = "yesterday_jobs_report.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write("# Yesterday's Job Postings\n\n")
            f.write("| Company | Job Title | Location | Posted At (UTC) | Link |\n")
            f.write("|---|---|---|---|---|\n")
            
            for company_slug, jobs in results.items():
                for job in jobs:
                    title = job.title.replace('|', '-') if job.title else 'N/A'
                    location = job.location.replace('|', '-') if job.location else 'N/A'
                    posted_at = job.posted_at.strftime('%Y-%m-%d %H:%M:%S') if job.posted_at else 'N/A'
                    
                    f.write(f"| **{company_slug}** | {title} | {location} | {posted_at} | [Apply]({job.url}) |\n")
        
        total_jobs = sum(len(j) for j in results.values())
        print(f"\n✅ Successfully wrote {total_jobs} jobs from {len(results)} companies to {md_file}")
    else:
        print("\n❌ No jobs were posted yesterday by any of the targeted companies.")

