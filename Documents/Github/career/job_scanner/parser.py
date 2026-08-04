import logging
import re
from datetime import date, timedelta
from job_scanner import config
from job_scanner.llm_client import LLMClient

logger = logging.getLogger(__name__)

class JobParser:
    def __init__(self):
        self.llm = LLMClient()

    def extract_posting_date(self, detail_text: str, reference_date: str) -> str:
        """
        Regex-based date extraction from job detail text. Zero LLM cost.
        Returns an ISO date string (YYYY-MM-DD) or 'N/A' if no date pattern found.
        """
        ref = date.fromisoformat(reference_date)
        text_lower = detail_text.lower()

        # Pattern: "posted today", "today", "just now", "X hours ago", "X minutes ago"
        if re.search(r"(posted\s+)?today|just\s+now|\d+\s*(hour|minute|min|sec)s?\s*ago", text_lower):
            return ref.isoformat()

        # Pattern: "yesterday", "1 day ago"
        if re.search(r"yesterday|1\s*day\s*ago", text_lower):
            return (ref - timedelta(days=1)).isoformat()

        # Pattern: "X days ago"
        m = re.search(r"(\d+)\s*days?\s*ago", text_lower)
        if m:
            return (ref - timedelta(days=int(m.group(1)))).isoformat()

        # Pattern: "Posted on May 24, 2026" or "May 24, 2026"
        months = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }
        m = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2}),?\s*(\d{4})", text_lower)
        if m:
            try:
                month = months[m.group(1)[:3]]
                day = int(m.group(2))
                year = int(m.group(3))
                return date(year, month, day).isoformat()
            except (ValueError, KeyError):
                pass

        # Pattern: ISO date "2026-05-24"
        m = re.search(r"(\d{4}-\d{2}-\d{2})", detail_text)
        if m:
            try:
                date.fromisoformat(m.group(1))  # Validate
                return m.group(1)
            except ValueError:
                pass

        return "N/A"

    def classify_ml_job(self, detail_text: str) -> dict:
        """
        LLM call to classify whether a job posting is an ML Engineer role.
        This is the ONLY place the LLM is used in the entire pipeline.
        Called only for recent jobs that passed the date + keyword filters.
        """
        system_prompt = (
            "You are an elite Tech Recruiter and AI Specialist.\n"
            "Your task is to classify whether a job posting is a dedicated Machine Learning Engineer role.\n\n"
            "CLASSIFICATION RULES:\n"
            "- Set 'is_ml_engineer' to true ONLY if the role is dedicated to ML/DL development.\n"
            "  Examples: training models, fine-tuning LLMs, building ML pipelines, RL, NLP, Computer Vision, AI Research.\n"
            "- Set 'is_ml_engineer' to false for:\n"
            "  * General Software Engineers who just consume ML API endpoints\n"
            "  * Frontend/Backend developers, Product Managers, QA\n"
            "  * Standard Data Analysts, Business Intelligence roles\n"
            "  * DevOps/Infra roles that only deploy ML models but don't build them\n\n"
            "Return STRICTLY a JSON object:\n"
            "{\n"
            "  \"title_verified\": \"Official title of the job as found in the text\",\n"
            "  \"is_ml_engineer\": true or false,\n"
            "  \"confidence_score\": 0.0 to 1.0,\n"
            "  \"reasoning\": \"Professional explanation of your classification\"\n"
            "}"
        )

        user_prompt = (
            f"Classify this job posting:\n\n"
            f"=== JOB DESCRIPTION START ===\n"
            f"{detail_text}\n"
            f"=== JOB DESCRIPTION END ===\n"
        )

        try:
            result = self.llm.parse_json_completion(system_prompt, user_prompt, model=config.FAST_MODEL)
            # Validate required keys
            for key, default in [("title_verified", "N/A"), ("is_ml_engineer", False),
                                 ("confidence_score", 0.0), ("reasoning", "N/A")]:
                if key not in result:
                    result[key] = default
            return result
        except Exception as e:
            logger.error(f"Error in classify_ml_job: {e}")
            return {
                "title_verified": "Error",
                "is_ml_engineer": False,
                "confidence_score": 0.0,
                "reasoning": f"Parsing error occurred: {e}"
            }
