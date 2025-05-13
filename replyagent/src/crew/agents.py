from google.auth.transport.requests import Request
from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.tools.gmail.get_thread import GmailGetThread
from langchain_community.tools.gmail.send_message import GmailSendMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from textwrap import dedent
from crewai import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json

SCOPES = ['https://mail.google.com/']

def get_gmail_service():
    creds = None
    if os.path.exists('D:\\TP\\replyagent\\token.json'):
        creds = Credentials.from_authorized_user_file('D:\\TP\\module3\\replyagent\\token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('D:\\TP\\module3\\replyagent\\credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('D:\\TP\\module3\\replyagent\\token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

class EmailResponseAgent:
    def __init__(self):
        self.gmail = GmailToolkit()
        self.gmail_service = get_gmail_service()
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", verbose=True, temperature=0.9, google_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.product_info = self.load_product_info()

    def load_product_info(self):
        with open("D:\\TP\\module3\\replyagent\\product.md", "r") as file:
            return file.read()

    def email_response_agent(self):
        return Agent(
            role='Conversational Email Responder',
            goal='Send conversational responses to action-required emails',
            backstory=dedent(f"""\
                You are a skilled conversationalist, adept at maintaining engaging email conversations about our product.
                Your strength lies in your ability to craft responses that prompt further interaction about our product,
                ensuring ongoing engagement with the email sender.
                PRODUCT INFO: {self.product_info}
            """),
            tools=[
                TavilySearchResults(),
                GmailGetThread(api_resource=self.gmail.api_resource),
                GmailSendMessage(service=self.gmail_service),
            ],
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )
