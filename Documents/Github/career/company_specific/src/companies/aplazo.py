from src.base_ats.ashby import fetch_ashby_jobs

def scrape():
    """
    Entry point for scraping Aplazo.
    Aplazo uses Ashby. We already know the board identifier is 'aplazo'.
    """
    return fetch_ashby_jobs("aplazo")
