from src.base_ats.smartrecruiters import fetch_smartrecruiters_jobs

def scrape():
    """
    Entry point for scraping Arista Networks.
    Arista Networks uses SmartRecruiters. The board identifier is 'aristanetworks'.
    """
    return fetch_smartrecruiters_jobs("aristanetworks")
