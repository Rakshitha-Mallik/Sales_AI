from crewai import Task
from textwrap import dedent
from .tools import CustomGmailTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.gmail.get_message import GmailGetMessage
import os
import re

class EmailResponseTasks:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", verbose=True, temperature=0.9, google_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.gmail_tool = CustomGmailTool()
        self.gmail_get_message = GmailGetMessage(api_resource=self.gmail_tool.service)
        self.product_info = self.load_product_info()

    def load_product_info(self):
        with open("D:\\TP\\module3\\replyagent\\product.md", "r") as file:
            return file.read()

    def respond_to_email_task(self, agent, email):
        summary = self._generate_summary(email)
        name = self._extract_name(email)
        is_follow_up = self._is_follow_up(email)
        response = self._generate_response(email, name, is_follow_up)
        self._send_email_response(email, response)

        return Task(
            description=dedent(f"""\
                Analyze the email thread and generate a conversational response about our product.
                Ensure the response is tailored to address the specific needs and context of the email and HTML-formatted.

                PRODUCT INFO
                ------------
                {self.product_info}

                EMAIL DETAILS
                -------------
                ID: {email['id']}
                Thread ID: {email['threadId']}
                Snippet: {email['snippet']}
                Sender: {email['sender']}
                
                Your final answer MUST include:
                - A summary of the email thread
                - The response message to be sent
                
                SUMMARY
                -------
                {summary}
                
                RESPONSE
                --------
                {response}
                """),
            agent=agent,
        )

    def _generate_summary(self, email):
        prompt = f"Summarize the following email thread content:\n\nSnippet: {email['snippet']}\n"
        summary_response = self.llm.invoke(prompt)
        summary = summary_response.content
        return summary

    def _generate_response(self, email, name, is_follow_up):
        prompt = (f"Generate a friendly and conversational email response about our product for the following email content:\n\n"
                  f"Snippet: {email['snippet']}\n"
                  f"Make sure to reply in a friendly tone and address the sender by their name, {name}, if mentioned.\n\n"
                  f"PRODUCT INFO:\n{self.product_info}")
        response_response = self.llm.invoke(prompt)
        response = response_response.content

        # Replace markdown asterisks with HTML bold tags
        response = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', response)

        # Check if the email content includes a request for a meeting
        if re.search(r'\b(meet|meeting|schedule|appointment|call)\b', email['snippet'], re.IGNORECASE):
            calendly_link = '<br><br>You can schedule a meeting with me using this link: <a href="https://calendly.com/">https://calendly.com/</a>'
            response = calendly_link

        # Ensure greeting and introduction are added only for the initial response
        if is_follow_up:
            html_response = "<html><body><p>{}</p></body></html>".format(response.replace('\n', '<br>'))
        else:
            html_response = "<html><body><p>Hi {},<br><br>{}</p></body></html>".format(name, response.replace('\n', '<br>'))

        return html_response

    def _extract_name(self, email):
        # Attempt to extract the name from the email sender field
        match = re.search(r'(?<=\").+?(?=\\")', email['sender'])
        if not match:
            match = re.search(r'^[^@]+', email['sender'])
        name = match.group(0).split()[0].capitalize() if match else "there"
        return name

    def _is_follow_up(self, email):
        # Check if the email is a follow-up in an existing thread
        return email.get('threadId') is not None

    def _send_email_response(self, email, response):
        message_id = self._get_message_id(email['id'])
        # Retrieve the original email's subject, thread ID, and message ID
        subject, thread_id, original_message_id = self.gmail_tool.get_email_subject_and_thread_id(message_id)
        if not subject:
            subject = f"Re: {email['snippet']}"  # Fallback subject in case of failure
        if not thread_id:
            thread_id = email['threadId']  # Fallback thread ID in case of failure
        
        result = self.gmail_tool.send_email(email['sender'], subject, response, thread_id, original_message_id, original_message_id)
        print(result)

    def _get_message_id(self, email_id):
        message = self.gmail_get_message(email_id)
        return message['id']
