import os.path
import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

def authenticate_gmail():
    """Shows basic usage of the Gmail API.
    Authenticates and returns credentials.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        
        if not creds or not creds.valid:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError(
                    "credentials.json not found! Please download it from Google Cloud Console "
                    "and place it in this directory."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            # This opens a browser window for user authentication
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            
    return creds

def create_draft(target_email: str, subject: str, body_text: str, attachment_path: str = None, html_body: str = None):
    """Create and insert a draft email.
       Returns: Draft object, including draft id and message meta data.
    """
    try:
        creds = authenticate_gmail()
        service = build("gmail", "v1", credentials=creds)

        message = EmailMessage()
        message.set_content(body_text)
        if html_body:
            message.add_alternative(html_body, subtype='html')
            
        message["To"] = target_email
        message["From"] = "me"
        message["Subject"] = subject
        
        if attachment_path and os.path.exists(attachment_path):
            import mimetypes
            with open(attachment_path, "rb") as f:
                file_data = f.read()
            file_name = os.path.basename(attachment_path)
            
            # Guess the mimetype
            mime_type, _ = mimetypes.guess_type(attachment_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            maintype, subtype = mime_type.split('/', 1)
            
            message.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"message": {"raw": encoded_message}}

        draft = (
            service.users()
            .drafts()
            .create(userId="me", body=create_message)
            .execute()
        )
        print(f"Draft created successfully. Draft ID: {draft['id']}")
        return draft

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
