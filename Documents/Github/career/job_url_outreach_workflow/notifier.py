import smtplib
from email.message import EmailMessage
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))
load_dotenv(os.path.join(BASE_DIR, 'email_processor', '.env'))
load_dotenv(os.path.join(BASE_DIR, 'email_processor', 'linkedin_message_request', '.env'))

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "animeshkr7@gmail.com")
APP_PASSWORD = os.getenv("APP_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "animeshkr7@gmail.com")

def send_job_outreach_notification(job_url: str, company_name: str, job_title: str, connections_data: list) -> bool:
    """
    Sends an email notification summarizing the LinkedIn outreach and drafted messages for a job link.
    """
    if not APP_PASSWORD:
        print("⚠️ Warning: APP_PASSWORD is missing in .env. Skipping email notification.")
        return False

    msg = EmailMessage()
    subject_date = datetime.now().strftime('%d-%m-%Y %H:%M')
    msg['Subject'] = f"🚀 [LinkedIn Outreach] Processed: {company_name} - {job_title} ({subject_date})"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    # Build plain text body — 1st degree connections first, then 2nd/3rd
    # Separate them for clarity
    first_degree = [item for item in connections_data if item.get('is_1st_degree')]
    non_first_degree = [item for item in connections_data if not item.get('is_1st_degree')]

    text_lines = [
        f"LinkedIn Outreach Workflow Completed!",
        f"----------------------------------------",
        f"Job Title:    {job_title}",
        f"Company:      {company_name}",
        f"Job URL:      {job_url}",
        f"Processed At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"1st Degree Connections: {len(first_degree)}",
        f"New Connections (2nd/3rd): {len(non_first_degree)}",
        f"Total: {len(connections_data)}",
        f"----------------------------------------\n"
    ]

    # Show 1st degree connections first
    if first_degree:
        text_lines.append("=== 1ST DEGREE CONNECTIONS (Direct Message Available) ===\n")
        for idx, item in enumerate(first_degree, 1):
            text_lines.append(f"Connection #{idx}: {item.get('name', 'N/A')}")
            text_lines.append(f"Profile:    {item.get('profile_url', 'N/A')}")
            text_lines.append(f"")
            text_lines.append(f"1st Degree: Yes (Direct Message Available)")
            text_lines.append(f"")
            text_lines.append(f"--- Draft Message ---")
            text_lines.append(item.get('draft_message', 'No message generated.'))
            text_lines.append(f"")
            text_lines.append("=" * 40 + "\n")

    # Then show 2nd/3rd degree connections
    if non_first_degree:
        text_lines.append("=== NEW CONNECTIONS (2nd/3rd Degree - Connect Requests) ===\n")
        for idx, item in enumerate(non_first_degree, 1):
            text_lines.append(f"Connection #{idx}: {item.get('name', 'N/A')}")
            text_lines.append(f"Profile:    {item.get('profile_url', 'N/A')}")
            text_lines.append(f"")
            text_lines.append(f"1st Degree: No (Connect Request Needed)")
            text_lines.append(f"Connect Sent: {'YES (Sent on LinkedIn)' if item.get('request_sent') else 'FAILED / Already Pending'}")
            text_lines.append(f"")
            text_lines.append(f"--- Draft Message ---")
            text_lines.append(item.get('draft_message', 'No message generated.'))
            text_lines.append(f"")
            text_lines.append("=" * 40 + "\n")


    msg.set_content("\n".join(text_lines))

    # Send via Gmail SMTP SSL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        print(f"[SUCCESS] Email notification sent to {RECEIVER_EMAIL} for {company_name}!")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email notification: {e}")
        return False


if __name__ == "__main__":
    # Test notification structure
    test_connections = [
        {
            "name": "Jane Doe",
            "profile_url": "https://www.linkedin.com/in/janedoe",
            "is_1st_degree": True,
            "draft_message": "Hi Jane,\n\nI found ACME Corp is hiring and my profile matches.\nJob Link: https://careers.acme.com/job/1"
        }
    ]
    send_job_outreach_notification("https://careers.acme.com/job/1", "ACME Corp", "Senior ML Engineer", test_connections)
