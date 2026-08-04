import smtplib
from email.message import EmailMessage
import os
import glob
from datetime import datetime
from dotenv import load_dotenv

# Try loading from the current directory, if not try the email_drafting folder where we know a .env exists
if not load_dotenv():
    load_dotenv(os.path.join(os.path.dirname(__file__), 'email_drafting', '.env'))

# --- CONFIGURATION ---
SENDER_EMAIL = "animeshkr7@gmail.com"
APP_PASSWORD = os.getenv("APP_PASSWORD") 
RECEIVER_EMAIL = "animeshkr7@gmail.com"
# ---------------------

def send_email():
    msg = EmailMessage()
    msg['Subject'] = f"✅ Daily Email Drafting Run Success - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    
    body = "The daily automated email drafting process has finished running. Please find the logs and fetched data attached."
    msg.set_content(body)

    # Attach Log File
    log_file = "drafting_log.txt"
    if os.path.exists(log_file):
        with open(log_file, 'rb') as f:
            msg.add_attachment(f.read(), maintype='text', subtype='plain', filename=log_file)
            
    # Attach Data Report (Finds the most recent JSON file in the data folder)
    data_dir = "data"
    if os.path.exists(data_dir):
        files = glob.glob(os.path.join(data_dir, "*.json"))
        if files:
            latest_file = max(files, key=os.path.getmtime)
            with open(latest_file, 'rb') as f:
                msg.add_attachment(f.read(), maintype='application', subtype='json', filename=os.path.basename(latest_file))

    # Send the email
    try:
        if not APP_PASSWORD:
            print("Error: APP_PASSWORD is not set. Make sure it's exported in your environment or .env file.")
            return
            
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        print("Email notification sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    send_email()
