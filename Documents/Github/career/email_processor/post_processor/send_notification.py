import os
import sys
import json
import argparse
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SENDER_EMAIL = os.getenv("LINKEDIN_EMAIL", "animeshkr7@gmail.com")
APP_PASSWORD = os.getenv("APP_PASSWORD")

def send_notification(input_file, recipient_email=None):
    if not recipient_email:
        recipient_email = SENDER_EMAIL
        
    if not APP_PASSWORD:
        print("Error: APP_PASSWORD is not set in the .env file. Cannot send email.")
        return False

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return False
        
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return False

    import sys
    base_dir_monitor = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "linkedin_monitor")
    if base_dir_monitor not in sys.path:
        sys.path.append(base_dir_monitor)
    from filter_utils import load_config, should_exclude_post
    config = load_config()

    data = []
    for post in raw_data:
        text = post.get('text', '')
        is_excluded, reason = should_exclude_post(text, config)
        if not is_excluded:
            data.append(post)
            
    if not data:
        print("All posts were filtered out. No email notification sent.")
        return False

    # Format data into a readable email body instead of raw JSON
    body = f"Found {len(data)} LinkedIn 'hiring ml engineer' posts with contact emails:\n\n"
    for i, post in enumerate(data, 1):
        emails = post.get('extracted_emails', [])
        author = post.get('author', 'Unknown')
        url = post.get('url', 'No URL')
        text = post.get('text', '')[:300]
        
        body += f"--- Post {i} ---\n"
        body += f"Author: {author}\n"
        body += f"Contact Emails: {', '.join(emails)}\n"
        body += f"URL: {url}\n"
        body += f"Preview: {text}...\n\n"
    
    msg = EmailMessage()
    msg['Subject'] = f"LinkedIn Monitor: {len(data)} Hiring Posts with Contact Emails"
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    
    msg.set_content(body)

    try:
        print(f"Sending notification to {recipient_email}...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send filtered LinkedIn posts as an email body.")
    parser.add_argument("input_file", help="Path to the JSON file to send")
    parser.add_argument("-r", "--recipient", help="Recipient email address. Defaults to your own email.", default=None)
    
    args = parser.parse_args()
    send_notification(args.input_file, args.recipient)
