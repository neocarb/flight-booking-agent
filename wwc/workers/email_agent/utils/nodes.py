from typing import Literal
import logging
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt

from wwc.workers.email_agent.utils.state import EmailManagerState
from wwc.workers.email_agent.utils.tools import tools
from wwc.workers.email_agent.utils.tools import get_user_input

llm = ChatOpenAI(model="gpt-4o")
logger = logging.getLogger(__name__)

# # human node
def human_node(state: EmailManagerState) -> Command[Literal["email_agent_node"]]:
    logger.info("in human_node")
    user_input = interrupt("Enter your input: ")
    logger.info("user_input: %s", user_input)
    human_message = HumanMessage(content=user_input)
    return Command(update={"messages": [human_message]}, goto="email_agent_node")

def email_agent_node(state: EmailManagerState) -> Command[Literal["__end__", "human_node"]]:
    logger.info("in email_agent_node")
    email_manager_instruction = """
    You are an expert email manager. Your task is to help the user manage their email, including searching and sending emails.
    You will ask the user for all the necessary information to search for emails or send emails.
    Be professional, concise, and user-friendly. Ensure your final response follows the exact format for automated parsing.
    """
    email_manager_agent = create_react_agent(
        llm,
        tools=tools,
        prompt=email_manager_instruction,
    )
    
    logger.info("state['messages']: %s ", state['messages'])
    result = email_manager_agent.invoke(state)
    
    # check for tool calls by email agent, if tool call, then goto end else goto human node
    tool_message = next((msg for msg in result['messages'] if isinstance(msg, ToolMessage) and "mail" in msg.name), None)
    logger.info("tool_message: %s", tool_message)  
    if tool_message:
        return Command(update={"messages": result["messages"]}, goto="__end__")
    else:
        return Command(update={"messages": result["messages"]}, goto="human_node")
    

    