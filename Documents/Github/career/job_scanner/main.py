import os
import sys
import json
import argparse
import datetime
from job_scanner import config
from job_scanner.scanner import CareerScanner

# ANSI Escape Codes for stunning terminal aesthetics
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
WHITE = "\033[37m"
MAGENTA = "\033[35m"

def print_header():
    print(f"\n{BOLD}{MAGENTA}============================================================{RESET}")
    print(f"{BOLD}{CYAN}      INTELLIGENT ADAPTIVE CAREER PAGE JOB SCANNER          {RESET}")
    print(f"{BOLD}{MAGENTA}============================================================{RESET}")
    print(f"{WHITE}  * Pipeline:      {YELLOW}Date-First Filtering Architecture{RESET}")
    print(f"{WHITE}  * Intelligence:  {YELLOW}Groq LLM (Regex + LLM Hybrid){RESET}")
    print(f"{WHITE}  * Target Match:  {GREEN}Machine Learning Engineer Roles{RESET}")
    print(f"{BOLD}{MAGENTA}============================================================{RESET}\n")

def write_reports(scan_results: list, reference_date: str) -> tuple[str, str]:
    """
    Creates a stunning Markdown report and a JSON database record in job_scanner/reports/
    """
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    md_filename = f"ml_jobs_{reference_date}.md"
    json_filename = f"ml_jobs_{reference_date}.json"

    md_path = os.path.join(reports_dir, md_filename)
    json_path = os.path.join(reports_dir, json_filename)

    # 1. Gather stats
    total_scanned = len(scan_results)
    total_discovered = sum(r["discovered_total"] for r in scan_results)
    total_recent = sum(r.get("recent_count", 0) for r in scan_results)
    total_ml_candidates = sum(r.get("ml_candidates_count", 0) for r in scan_results)
    all_matches = []
    for r in scan_results:
        for job in r["matching_ml_jobs"]:
            # Inject company name
            job["company"] = r["company"]
            all_matches.append(job)

    # 2. Write Markdown Report
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# 🎯 New Machine Learning Engineer Openings - {reference_date}\n\n")
        f.write("This report compiles recently posted Machine Learning Engineering roles across monitored company boards. "
                "Each posting is processed by an LLM to verify technical fit and normalize posting dates.\n\n")
        
        f.write("## 📊 Scan Metrics Summary\n")
        f.write("| Metric | Value |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| **Date of Scan** | {reference_date} |\n")
        f.write(f"| **Companies Scanned** | {total_scanned} |\n")
        f.write(f"| **Total Links Discovered** | {total_discovered} |\n")
        f.write(f"| **Recent Posts (within {config.DAYS_LIMIT}d)** | {total_recent} |\n")
        f.write(f"| **ML Keyword Candidates** | {total_ml_candidates} |\n")
        f.write(f"| **Verified ML Matches** | **{len(all_matches)}** |\n\n")

        f.write("## 🚀 Verified Active Matches\n")
        if not all_matches:
            f.write("> **No new Machine Learning Engineer jobs posted today or yesterday.**\n\n")
        else:
            f.write("| Job Title | Company | Location | Date Posted | Link |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for job in all_matches:
                f.write(f"| **{job['title']}** | {job['company']} | {job['location']} | `{job['date_status']}` | [Apply ↗]({job['url']}) |\n")
            f.write("\n\n---\n\n")
            
            f.write("## 🔍 Deep Match Details\n")
            for idx, job in enumerate(all_matches):
                f.write(f"### {idx+1}. {job['title']} @ {job['company']}\n")
                f.write(f"- **URL**: {job['url']}\n")
                f.write(f"- **Location**: {job['location']}\n")
                f.write(f"- **Calculated Date**: `{job['extracted_date']}` ({job['date_status']})\n")
                f.write(f"- **Confidence Score**: `{job['confidence_score']*100:.1f}%` fit\n\n")
                
                f.write("> #### 🧠 Recruitment LLM Analysis:\n")
                f.write(f"> {job['reasoning']}\n\n")
                f.write("---\n\n")

        f.write("## 🗄️ Scan Trace & Discarded Postings\n")
        f.write("Detailed trace logging of postings that did not meet ML validation or recency constraints:\n\n")
        for r in scan_results:
            f.write(f"<details>\n<summary><b>{r['company']} Scans</b> ({len(r['discarded_jobs'])} items discarded)</summary>\n\n")
            f.write("| Title / URL | Rejection Reason |\n")
            f.write("| :--- | :--- |\n")
            for discarded in r["discarded_jobs"]:
                f.write(f"| [{discarded['title']}]({discarded['url']}) | {discarded['reason']} |\n")
            f.write("</details>\n\n")

    # 3. Write JSON data
    json_data = {
        "scan_date": reference_date,
        "metrics": {
            "companies_scanned": total_scanned,
            "total_discovered": total_discovered,
            "total_recent": total_recent,
            "total_ml_candidates": total_ml_candidates,
            "matches_found": len(all_matches)
        },
        "matches": all_matches,
        "raw_results": scan_results
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    return md_path, json_path

def main():
    print_header()

    parser = argparse.ArgumentParser(description="Adaptive Job Board Scanner and ML Classifier.")
    parser.add_argument("-u", "--url", type=str, help="Single career page URL to scan")
    parser.add_argument("-c", "--company", type=str, help="Company name for the custom URL")
    parser.add_argument("-d", "--days", type=int, help="Override recency day limit (0=today strictly, 1=today/yesterday, etc.)")

    args = parser.parse_args()

    # Dynamic date override
    if args.days is not None:
        config.DAYS_LIMIT = args.days
        print(f"{CYAN}[Config] Recency filter overridden to: {YELLOW}last {config.DAYS_LIMIT} days.{RESET}")

    targets = []
    if args.url:
        company = args.company or "Custom Target"
        targets.append({"name": company, "url": args.url})
        print(f"{CYAN}[Start] Running custom scan on: {BOLD}{company}{RESET} ({args.url})")
    else:
        targets = config.DEFAULT_TARGET_SITES
        print(f"{CYAN}[Start] Running batch scan for default sites: {BOLD}{', '.join(t['name'] for t in targets)}{RESET}")

    reference_date = datetime.date.today().isoformat()
    scan_results = []
    scanner = CareerScanner()

    try:
        for idx, target in enumerate(targets):
            print(f"\n{BOLD}{CYAN}------------------------------------------------------------{RESET}")
            print(f"{BOLD}{WHITE}[{idx+1}/{len(targets)}] Processing {target['name']} Career Board{RESET}")
            print(f"{CYAN}URL: {target['url']}{RESET}")
            print(f"{BOLD}{CYAN}------------------------------------------------------------{RESET}\n")

            try:
                res = scanner.scan_site(target["url"], target["name"])
                scan_results.append(res)
            except Exception as e:
                print(f"{RED}[Error] Scan failed for {target['name']}: {e}{RESET}")
                # Save empty stub
                scan_results.append({
                    "company": target["name"],
                    "url": target["url"],
                    "discovered_total": 0,
                    "recent_count": 0,
                    "ml_candidates_count": 0,
                    "matching_ml_jobs": [],
                    "discarded_jobs": [{"title": "Scanner Error", "url": target["url"], "reason": str(e)}]
                })

        # Generate Reports
        md_path, json_path = write_reports(scan_results, reference_date)

        # Print Final Summary Board
        print(f"\n{BOLD}{GREEN}============================================================{RESET}")
        print(f"{BOLD}{GREEN}                      SCAN COMPLETION                       {RESET}")
        print(f"{BOLD}{GREEN}============================================================{RESET}")
        
        all_matches = []
        for r in scan_results:
            for job in r["matching_ml_jobs"]:
                all_matches.append((r["company"], job))

        print(f"{WHITE}Total Sites Scanned:      {BOLD}{len(targets)}{RESET}")
        print(f"{WHITE}Total Postings Found:     {BOLD}{sum(r['discovered_total'] for r in scan_results)}{RESET}")
        print(f"{WHITE}Recent (within {config.DAYS_LIMIT}d):    {BOLD}{sum(r.get('recent_count', 0) for r in scan_results)}{RESET}")
        print(f"{WHITE}ML Keyword Candidates:    {BOLD}{sum(r.get('ml_candidates_count', 0) for r in scan_results)}{RESET}")
        print(f"{WHITE}Verified ML Matches:      {BOLD}{GREEN}{len(all_matches)}{RESET}")
        print(f"{BOLD}{GREEN}============================================================{RESET}")

        if all_matches:
            print(f"\n{BOLD}{WHITE}[MATCHES] VERIFIED NEW ML POSTINGS:{RESET}")
            for idx, (company, job) in enumerate(all_matches):
                print(f" {idx+1}. [{BOLD}{GREEN}{company}{RESET}] {BOLD}{job['title']}{RESET}")
                print(f"    * Location: {job['location']}")
                print(f"    * Recency:  {YELLOW}{job['date_status']}{RESET} (Parsed: {job['extracted_date']})")
                print(f"    * Apply:    {job['url']}")
                print(f"    * Fit:      {job['reasoning'][:120]}...")
                print()
        else:
            print(f"\n{BOLD}{YELLOW}[INFO] No new Machine Learning postings detected in the recency window.{RESET}")

        print(f"\n{CYAN}[Report] Beautiful Markdown report saved to: {RESET}")
        print(f"  {BOLD}{md_path}{RESET}")
        print(f"{CYAN}[Database] Structured JSON database record saved to: {RESET}")
        print(f"  {BOLD}{json_path}{RESET}\n")

    finally:
        # Clean up driver resources
        scanner.close_all()

if __name__ == "__main__":
    main()
