import re
import time
import datetime
import logging
from job_scanner import config
from job_scanner.scraper import JobScraper
from job_scanner.parser import JobParser

logger = logging.getLogger(__name__)

class CareerScanner:
    def __init__(self):
        self.scraper = JobScraper()
        self.parser = JobParser()

    def is_title_ml_related(self, title: str) -> bool:
        """
        Free Python keyword gate. Returns true if the title matches any ML keyword.
        """
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in config.ML_KEYWORDS)

    def verify_recency(self, extracted_date: str, reference_date_str: str) -> tuple:
        """
        Checks if the extracted date falls within the allowed DAYS_LIMIT window.
        Returns (is_recent: bool, status_label: str).
        """
        if not extracted_date or extracted_date == "N/A":
            # No date found — treat as potentially recent (we don't want to miss new postings)
            return True, "Date Unspecified"

        try:
            ref_date = datetime.date.fromisoformat(reference_date_str)
            job_date = datetime.date.fromisoformat(extracted_date)
            delta = (ref_date - job_date).days

            if delta < 0:
                return True, "Today"
            elif delta == 0:
                return True, "Today"
            elif delta <= config.DAYS_LIMIT:
                return True, f"{delta} day(s) ago"
            else:
                return False, f"Old ({delta} days ago)"
        except Exception as e:
            logger.warning(f"Error parsing date comparison for {extracted_date}: {e}")
            return True, "Date Parse Error"

    def scan_site(self, url: str, company_name: str) -> dict:
        """
        Efficient date-first scanning pipeline.

        Pipeline:
        1. Scrape career page with BeautifulSoup -> extract all job links (no LLM)
        2. ML keyword gate on titles (free Python filter — cuts 115 -> ~10-15)
        3. Fetch detail pages for ML candidates only -> regex date extraction (no LLM)
        4. Date recency filter
        5. LLM classifies ONLY the handful of recent ML-keyword matches
        """
        reference_date = datetime.date.today().isoformat()
        logger.info(f"Starting scan for {company_name} | Reference Date: {reference_date}")

        results = {
            "company": company_name,
            "url": url,
            "scan_time": datetime.datetime.now().isoformat(),
            "discovered_total": 0,
            "recent_count": 0,
            "ml_candidates_count": 0,
            "matching_ml_jobs": [],
            "discarded_jobs": []
        }

        # ===========================================
        # STEP 1: SCRAPE — extract job links (no LLM)
        # ===========================================
        html = self.scraper.fetch_url(url)
        if not html:
            logger.error(f"Failed to fetch career page for {company_name}")
            return results

        job_links = self.scraper.extract_job_links(html, url)
        results["discovered_total"] = len(job_links)
        logger.info(f"Step 1: Extracted {len(job_links)} job links from {company_name} board.")

        if not job_links:
            return results

        # =================================================
        # STEP 2: ML KEYWORD GATE on titles (free, instant)
        # This cuts 100+ links down to ~10-15 ML candidates
        # so we only fetch detail pages for those.
        # =================================================
        ml_candidates = []
        for job in job_links:
            title = job["title"]
            if self.is_title_ml_related(title):
                ml_candidates.append(job)
                logger.info(f"  [ML Title] {title}")

        results["ml_candidates_count"] = len(ml_candidates)
        logger.info(f"Step 2: {len(ml_candidates)} ML-keyword matches (out of {len(job_links)} total).")

        if not ml_candidates:
            logger.info(f"No ML-related titles found on {company_name}. Skipping deep scan.")
            return results

        # ========================================================
        # STEP 3: FETCH DETAIL PAGES + DATE EXTRACTION (regex only)
        # Only for the small set of ML keyword matches.
        # ========================================================
        recent_ml_jobs = []  # (job, extracted_date, status_label, detail_text)

        for index, job in enumerate(ml_candidates):
            title = job["title"]
            job_url = job["url"]

            logger.info(f"  Step 3 [{index+1}/{len(ml_candidates)}]: Fetching detail for: {title}")

            detail_html = self.scraper.fetch_url(job_url)
            if not detail_html:
                logger.warning(f"    Failed to fetch detail page for: {title}")
                results["discarded_jobs"].append({
                    "title": title, "url": job_url,
                    "reason": "Failed to fetch detail page"
                })
                continue

            detail_text = self.scraper.extract_body_text(detail_html)

            # Extract date via regex (free, instant, no LLM)
            extracted_date = self.parser.extract_posting_date(detail_text, reference_date)

            # Check recency
            is_recent, status_label = self.verify_recency(extracted_date, reference_date)

            if is_recent:
                recent_ml_jobs.append((job, extracted_date, status_label, detail_text))
                logger.info(f"    [Recent] {status_label} ({extracted_date})")
            else:
                logger.info(f"    [Old] {status_label} — skipping")
                results["discarded_jobs"].append({
                    "title": title, "url": job_url,
                    "reason": f"Too old: {status_label} (Date: {extracted_date})"
                })

        results["recent_count"] = len(recent_ml_jobs)
        logger.info(f"Step 3: {len(recent_ml_jobs)} recent ML candidates remain.")

        # =======================================================
        # STEP 4: LLM CLASSIFICATION (the ONLY LLM usage)
        # Classify only the recent ML-keyword candidates.
        # =======================================================
        for index, (job, extracted_date, status_label, detail_text) in enumerate(recent_ml_jobs):
            title = job["title"]
            job_url = job["url"]

            logger.info(f"  Step 4 [{index+1}/{len(recent_ml_jobs)}]: LLM classifying: {title}")

            classification = self.parser.classify_ml_job(detail_text)
            time.sleep(1.5)  # Rate limit pause between LLM calls

            is_ml = classification.get("is_ml_engineer", False)
            confidence = classification.get("confidence_score", 0.0)
            reasoning = classification.get("reasoning", "")

            if is_ml:
                logger.info(f"    [MATCH] {title} | Confidence: {confidence:.0%}")
                results["matching_ml_jobs"].append({
                    "title": classification.get("title_verified", title),
                    "url": job_url,
                    "location": "N/A",
                    "extracted_date": extracted_date,
                    "date_status": status_label,
                    "reasoning": reasoning,
                    "confidence_score": confidence
                })
            else:
                logger.info(f"    [X] Not ML: {title} | {reasoning}")
                results["discarded_jobs"].append({
                    "title": title, "url": job_url,
                    "reason": f"LLM classified as non-ML: {reasoning}"
                })

        return results

    def close_all(self):
        """Cleans up browser threads."""
        self.scraper.close()
