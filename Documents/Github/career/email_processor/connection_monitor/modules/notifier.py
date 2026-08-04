import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

def send_connection_accepted_email(person_name: str, profile_url: str, company_name: str, draft_message: str) -> bool:
    """
    Sends an email alert informing the user that a LinkedIn connection has been accepted,
    including the profile URL and ready-to-send draft message.
    """
    load_dotenv()
    email_to = os.getenv("LINKEDIN_EMAIL", "animeshkr7@gmail.com")
    app_pwd = os.getenv("APP_PASSWORD")

    if not app_pwd:
        print("Warning: APP_PASSWORD is not set in .env. Skipping email notification.")
        return False

    subject = f"🎉 Connection Accepted: {person_name} ({company_name})"

    clean_draft_message = draft_message.replace("\\n", "\n") if draft_message else ""

    email_body = f"""Hi Animesh,

Great news! {person_name} at {company_name} has accepted your LinkedIn connection request!

--------------------------------------------------
PERSON DETAILS
--------------------------------------------------
Name: {person_name}
Company: {company_name}
Profile URL: {profile_url}

--------------------------------------------------
RECOMMENDED DRAFT MESSAGE TO SEND ON LINKEDIN
--------------------------------------------------
{clean_draft_message}

--------------------------------------------------
Direct Profile Link: {profile_url}
"""

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = email_to
    msg['To'] = email_to
    msg.set_content(email_body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_to, app_pwd)
            server.send_message(msg)
        print(f" -> Sent connection acceptance email for {person_name} to {email_to}!")
        return True
    except Exception as e:
        print(f" -> Failed to send connection acceptance email: {e}")
        return False
