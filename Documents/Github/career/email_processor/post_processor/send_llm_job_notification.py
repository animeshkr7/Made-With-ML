import os
import json
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, '.env'))

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "animeshkr7@gmail.com")
APP_PASSWORD = os.getenv("APP_PASSWORD")

def send_llm_job_notification(filepath: str) -> bool:
    """
    Reads LLM curated posts from filepath and sends a separate email notification to animeshkr7@gmail.com.
    """
    print("\n--- Sending LLM Curated Job Notification Email ---")
    if not os.path.exists(filepath):
        print(f"Error: Notification file {filepath} not found.")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    if not posts:
        print("No qualified LLM posts found to email.")
        return False

    if not APP_PASSWORD:
        print("Warning: APP_PASSWORD is not set in .env. Cannot send email notification.")
        return False

    subject = f"[AI/ML Job Alert] Curated LinkedIn Hiring Posts ({len(posts)} Qualified)"

    body_lines = [
        "Hi Animesh,\n",
        f"Here are {len(posts)} curated AI/ML hiring posts evaluated and qualified by Groq LLM (Remote/India hiring for AI/ML/Data Science/MLOps roles):\n",
        "=" * 60
    ]

    for idx, post in enumerate(posts, 1):
        author = post.get("author", "Unknown")
        url = post.get("url", "Unknown URL")
        text = post.get("text", "").strip()
        scraped_at = post.get("scraped_at", "")[:19].replace("T", " ")

        body_lines.append(f"\n[{idx}] AUTHOR: {author}")
        body_lines.append(f"POST URL: {url}")
        body_lines.append(f"SCRAPED AT: {scraped_at}")
        body_lines.append("POST CONTENT:")
        body_lines.append(text)
        body_lines.append("-" * 60)

    body_lines.append("\nHappy Job Hunting!\nLinkedIn Monitor Automation")

    email_body = "\n".join(body_lines)

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = LINKEDIN_EMAIL
    msg['To'] = LINKEDIN_EMAIL
    msg.set_content(email_body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(LINKEDIN_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        print(f"-> Separate LLM Curated Job Notification email sent successfully to {LINKEDIN_EMAIL}!")
        return True
    except Exception as e:
        print(f"-> Failed to send LLM email notification: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        send_llm_job_notification(sys.argv[1])
