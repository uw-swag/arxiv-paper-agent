from .base import BaseExporter
import base64
import os

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
        token_path = os.path.join(os.path.dirname(__file__), 'token.json')
        credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)

    async def export(self, content: str, destination: str, format: str = "html") -> dict:
        """
        Export results via email.

        Args:
            content: The content to export
            destination: Email address to send to
            format: Output format - "html" or "markdown" (html recommended for email)

        Returns:
            Dict with status and message
        """
        try:
            service = self.get_gmail_service()

            message = EmailMessage()
            message.set_content("This email requires an HTML compatible viewer.")

            # Format content based on preference
            if format == "html":
                message.add_alternative(content, subtype='html')
            else:
                # For markdown, convert to plain text for email
                message.set_content(content)

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
