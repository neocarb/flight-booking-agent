import os
from langgraph.types import interrupt

from langchain_google_community import GmailToolkit
from langchain_core.tools import tool
from langchain_google_community.gmail.utils import (
    build_resource_service,
    get_gmail_credentials,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
credentials_path = os.path.join(BASE_DIR, "credentials.json")
token_path = os.path.join(BASE_DIR, "token.json")

credentials = get_gmail_credentials(
    token_file=token_path,
    scopes=["https://mail.google.com/"],
    client_secrets_file=credentials_path
)
api_resource = build_resource_service(credentials=credentials)
email_toolkit = GmailToolkit(api_resource=api_resource)
tools = email_toolkit.get_tools()

@tool
def get_user_input(question: str) -> str:
    """
    Get user input from the command line.
    """
    user_input = interrupt(question)
    return user_input