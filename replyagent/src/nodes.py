import os
import time
from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.tools.gmail.search import GmailSearch

class Nodes:
    def __init__(self):
        self.gmail = GmailToolkit()

    def check_email(self, state):
        print("# Checking for new unread emails")
        search = GmailSearch(api_resource=self.gmail.api_resource)
        # Update the search query to include only unread emails
        emails = search('is:unread')
        checked_emails = state.get('checked_emails_ids', [])
        if checked_emails is None:
            checked_emails = []
        new_emails = []

        for email in emails:
            if (email['id'] not in checked_emails) and (os.environ['MY_EMAIL'] not in email.get('sender', '')):
                new_emails.append(
                    {
                        "id": email['id'],
                        "threadId": email['threadId'],
                        "snippet": email['snippet'],
                        "sender": email["sender"],
                    }
                )
                print(f"Email ID: {email['id']}, Thread ID: {email['threadId']}, Sender: {email['sender']}, Snippet: {email['snippet']}")
        checked_emails.extend([email['id'] for email in emails])

        return {
            **state,
            "emails": new_emails,
            "checked_emails_ids": checked_emails
        }

    def wait_next_run(self, state):
        print("## Waiting for 10 seconds")
        time.sleep(10)
        return state

    def new_emails(self, state):
        if len(state['emails']) == 0:
            print("## No new emails")
            return "end"
        else:
            print("## New emails")
            return "continue"
