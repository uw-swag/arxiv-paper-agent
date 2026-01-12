from .base import BaseExporter
import base64
import os
from ..formatters.html_formatter import format_as_html
from email.message import EmailMessage
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class EmailSchema(BaseModel):
    email_address: str
    html: str

class EmailExporter(BaseExporter):

    def get_gmail_service(self):
        creds = None
        if os.path.exists(os.path.join(os.path.dirname(__file__), 'token.json')):
            creds = Credentials.from_authorized_user_file(os.path.join(os.path.dirname(__file__), 'token.json'), SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(os.path.join(os.path.dirname(__file__), 'credentials.json'), SCOPES)
                creds = flow.run_local_server(port=0)
            with open(os.path.join(os.path.dirname(__file__), 'token.json'), 'w') as token:
                token.write(creds.to_json())
        
        return build('gmail', 'v1', credentials=creds)

    # Email: arxivpaperagent@gmail.com
    # Password: ArxivPaperAgent_123
    async def export(self, result: dict, destination: str) -> dict:
        try: 
            service = self.get_gmail_service()

            message = EmailMessage()
            message.set_content("This email requires an HTML compatible viewer.")
            
            message.add_alternative(format_as_html(result), subtype='html')

            message['To'] = destination
            message['From'] = "me"
            message['Subject'] = "arXiv Paper Weekly Update"

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {'raw': encoded_message}

            service.users().messages().send(userId="me", body=create_message).execute()

            return {"status": "success", "message": f"Email sent to {destination}"}
        
        except Exception as e:
            print(f"Failed to send email: {e}")
            return {"status": "error", "message": str(e)}