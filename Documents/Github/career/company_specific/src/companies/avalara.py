from src.base_ats.careerpuck import fetch_careerpuck_jobs

def scrape():
    """
    Entry point for scraping Avalara.
    Avalara uses Careerpuck. The board identifier is 'avalara'.
    """
    return fetch_careerpuck_jobs("avalara")
