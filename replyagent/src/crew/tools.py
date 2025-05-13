import base64
from googleapiclient.discovery import build
import google_auth_oauthlib.flow
import os

class CustomGmailTool:
    def __init__(self):
        self.service = self.get_gmail_service()

    def get_gmail_service(self):
        SCOPES = ['https://mail.google.com/']
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            r'D:\\TP\\module3\\replyagent\\credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        service = build('gmail', 'v1', credentials=creds)
        return service

    def get_email_subject_and_thread_id(self, message_id):
        """
        Retrieves the subject and thread ID of an email using its message ID.

        Parameters:
        message_id (str): The message ID of the email.

        Returns:
        tuple: The subject and thread ID of the email.
        """
        try:
            message = self.service.users().messages().get(userId="me", id=message_id, format="metadata", metadataHeaders=['Subject', 'Message-ID']).execute()
            headers = message.get('payload', {}).get('headers', [])
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), None)
            thread_id = message.get('threadId', None)
            message_id = next((header['value'] for header in headers if header['name'] == 'Message-ID'), None)
            return subject, thread_id, message_id
        except Exception as error:
            print(f"An error occurred while getting the email subject and thread ID: {error}")
            return None, None, None

    def send_email(self, recipient, subject, message, thread_id, in_reply_to, references):
        """
        Sends an email within the same thread.

        Parameters:
        recipient (str): The recipient's email address.
        subject (str): The subject of the recipient email.
        message (str): The body of the email.
        thread_id (str): The thread ID of the recipient mail.
        in_reply_to (str): The Message-ID of the email being replied to.
        references (str): The Message-ID of the email being replied to.
        """
        email_message = (
            f"To: {recipient}\r\n"
            f"Subject: {subject}\r\n"
            f"In-Reply-To: {in_reply_to}\r\n"
            f"References: {references}\r\n"
            f"Content-Type: text/html; charset=\"UTF-8\"\r\n"
            f"\r\n{message}"
        )
        raw = base64.urlsafe_b64encode(email_message.encode("utf-8")).decode("utf-8")
        body = {
            'raw': raw,
            'threadId': thread_id
        }
        
        try:
            sent_message = self.service.users().messages().send(userId="me", body=body).execute()
            return sent_message
        except Exception as error:
            print(f"An error occurred: {error}")
            return None
