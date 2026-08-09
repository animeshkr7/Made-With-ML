# LinkedIn Playwright Monitor

This folder contains an automated Playwright workflow to search LinkedIn for "ML Engineer" posts and sort them by the latest date.

## Why this approach?
LinkedIn actively bans accounts that use raw scripts (username/password logins). To protect your account, this monitor uses a **session state** (saving your browser cookies) so that the automated script behaves like a returning, already-logged-in user.

## Files
- `setup_auth.py`: A helper script that opens a visible browser and asks you to log in manually. Once you log in, it saves your session cookies into a `state.json` file.
- `linkedin_scraper.py`: The main automated script. It silently uses the `state.json` file to navigate LinkedIn search and extract the latest "ML Engineer" posts into a JSON file inside the `output` folder.

## Email OTP Bypass (Anti-Bot Protection)
If LinkedIn detects the scraper and throws a security checkpoint asking for an email OTP (One-Time Password), the scraper handles it automatically:
1. It uses your Gmail SMTP credentials to send you an email titled "ACTION REQUIRED: LinkedIn OTP Pin".
2. It polls your inbox via IMAP waiting for a reply.
3. You simply reply to that email with the OTP digits.
4. The scraper reads your reply, inputs the OTP into the LinkedIn security check, and resumes scraping without crashing!

## Prerequisites & Setup

You must create a `.env` file in the root directory (above this folder) with your email credentials to enable the OTP bypass feature:
```env
LINKEDIN_EMAIL=your.email@gmail.com
LINKEDIN_PASSWORD=your_linkedin_password
APP_PASSWORD=your_gmail_app_password
```
*(Note: `APP_PASSWORD` is a 16-character Google App Password, required since standard passwords don't work for SMTP/IMAP anymore).*

## How to use:

### Step 1: Set up Authentication
Run the authentication script first:
```powershell
python setup_auth.py
```
A Chromium window will open. Log into LinkedIn manually. Once you can see your feed, return to the terminal and press **ENTER**. This will generate a `state.json` file.

### Step 2: Run the Scraper
Once authenticated, you can run the scraper:
```powershell
python linkedin_scraper.py
```
This script will open a browser, navigate to the search page, extract the latest posts, and save the data in the `output/` directory as a JSON file.

### Note on Headless Mode
By default, the `linkedin_scraper.py` is configured to run in **headed** mode (visible) right now so you can watch it and verify it's working without getting blocked. Once you are confident it works, you can open `linkedin_scraper.py` and change `run_scraper(headless=False)` at the bottom to `run_scraper(headless=True)` to make it completely invisible in the background.
