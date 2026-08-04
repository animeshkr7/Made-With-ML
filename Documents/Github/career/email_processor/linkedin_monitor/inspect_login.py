import os
import time
from playwright.sync_api import sync_playwright

def inspect_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("Navigating to LinkedIn login page...")
        page.goto("https://www.linkedin.com/login")
        html = page.evaluate("() => document.body.innerHTML")
        with open("login_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved login page HTML to login_page.html")
            
        browser.close()

if __name__ == "__main__":
    inspect_login()
