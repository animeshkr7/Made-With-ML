import urllib.parse
import logging
from bs4 import BeautifulSoup
import requests
from job_scanner import config

# Set up logger
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self._selenium_driver = None

    def _get_selenium_driver(self):
        """
        Lazily initializes the headless Selenium Chrome driver.
        """
        if self._selenium_driver is not None:
            return self._selenium_driver

        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager

            chrome_options = Options()
            if config.SELENIUM_HEADLESS:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")

            # Silence logs
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

            service = Service(ChromeDriverManager().install())
            self._selenium_driver = webdriver.Chrome(service=service, options=chrome_options)
            return self._selenium_driver
        except Exception as e:
            logger.error(f"Failed to initialize Selenium webdriver: {e}")
            return None

    def close(self):
        """Closes the Selenium browser if open."""
        if self._selenium_driver:
            try:
                self._selenium_driver.quit()
                logger.info("Headless Selenium browser session closed.")
            except Exception as e:
                logger.error(f"Error closing Selenium browser: {e}")
            finally:
                self._selenium_driver = None

    def fetch_page_static(self, url: str) -> str:
        """
        Fetches the HTML source using a static HTTP request.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Static fetch failed for {url} with status code: {response.status_code}")
                return ""
        except Exception as e:
            logger.warning(f"Static fetch failed for {url} due to error: {e}")
            return ""

    def fetch_page_dynamic(self, url: str) -> str:
        """
        Fetches the HTML source using headless Selenium.
        """
        driver = self._get_selenium_driver()
        if not driver:
            logger.error("Selenium is not available. Cannot fetch dynamically.")
            return ""

        try:
            logger.info(f"Opening dynamic session for {url}...")
            driver.get(url)
            
            # Simple progressive wait for JS elements to render
            import time
            time.sleep(3.5)
            
            # Scroll down to trigger any infinite scrolls or lazy loads
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(1.5)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.0)
            
            return driver.page_source
        except Exception as e:
            logger.error(f"Dynamic Selenium fetch failed for {url}: {e}")
            return ""

    def fetch_url(self, url: str) -> str:
        """
        Resiliently fetches page contents. First tries static requests, then falls back to Selenium.
        """
        # 1. Try static fetch first
        html = self.fetch_page_static(url)
        
        # 2. Check if static fetch retrieved valid content or if it looks empty/rendered
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a")
        
        # If static fetch returned very sparse text content, it's likely a JS loading screen, so we fallback to Selenium
        page_text = soup.get_text().strip()
        if not html or len(page_text) < 300:
            logger.info(f"Static fetch returned sparse text ({len(page_text)} chars). Falling back to headless Selenium...")
            html = self.fetch_page_dynamic(url)
            
        return html

    def extract_job_links(self, html: str, base_url: str) -> list[dict]:
        """
        Extracts all probable job posting links from a career board HTML page.
        Uses BeautifulSoup + heuristic filtering. No LLM needed.

        Returns a list of dicts: [{"title": str, "url": str}, ...]
        """
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Strip heavy, non-content tags
        for element in soup(["script", "style", "noscript", "svg", "path", "iframe", "img"]):
            element.decompose()

        job_links = []
        seen_urls = set()

        # Blacklist for navigation / non-job anchor text
        text_blacklist = [
            "privacy", "terms", "cookie", "contact", "about", "sign in", "login",
            "register", "blog", "news", "press", "event", "support", "help", "faq",
            "customer", "newsletter", "feedback", "social", "home", "careers",
            "culture", "benefits", "diversity", "life at", "teams", "departments",
            "all openings", "search", "subscribe", "community", "legal", "powered by",
            "job seeker", "apply now"
        ]
        url_blacklist = [
            "twitter", "linkedin", "facebook", "instagram", "youtube",
            "github", "mailto:", "javascript:", "#"
        ]

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            absolute_url = urllib.parse.urljoin(base_url, href)
            text = " ".join(a_tag.get_text().split()).strip()

            # Skip self-reference, empty, too short
            if absolute_url.rstrip('/') == base_url.rstrip('/'):
                continue
            if not text or len(text) < 5:
                continue
            if absolute_url in seen_urls:
                continue

            text_lower = text.lower()
            url_lower = absolute_url.lower()

            # Drop blacklisted anchors and URLs
            if any(x in text_lower for x in text_blacklist):
                continue
            if any(x in url_lower for x in url_blacklist):
                continue

            seen_urls.add(absolute_url)
            job_links.append({"title": text, "url": absolute_url})

        logger.info(f"Extracted {len(job_links)} job-like links from career page.")
        return job_links

    def extract_body_text(self, html: str) -> str:
        """
        Strips HTML structural tags and extracts clean text blocks for detail pages.
        """
        if not html:
            return ""

        soup = BeautifulSoup(html, "html.parser")
        
        # Remove scripts, styles, etc.
        for element in soup(["script", "style", "noscript", "svg", "path", "iframe", "header", "footer", "nav"]):
            element.decompose()

        # Extract text blocks
        text_blocks = []
        for p in soup.find_all(["p", "h1", "h2", "h3", "h4", "li", "span", "div"]):
            block_text = " ".join(p.get_text().split()).strip()
            if block_text and len(block_text) > 15:  # Skip tiny fragments
                text_blocks.append(block_text)

        # Remove duplicate adjacent blocks
        deduped = []
        for block in text_blocks:
            if not deduped or deduped[-1] != block:
                deduped.append(block)

        # Return a summarized version (up to 3000 words) to save tokens
        return "\n".join(deduped[:120])
