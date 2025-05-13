from typing import Literal
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt

from wwc.workers.email_agent.utils.state import EmailManagerState
from wwc.workers.email_agent.utils.tools import tools
from wwc.workers.email_agent.utils.tools import get_user_input

llm = ChatOpenAI(model="gpt-4o")

# # human node
def human_node(state: EmailManagerState) -> Command[Literal["email_agent_node"]]:
    # get user input
    user_input = interrupt("Enter your input: ")
    # return user input
    return Command(update={"messages": [HumanMessage(content=user_input)]}, goto="email_agent_node")

def email_agent_node(state: EmailManagerState):
    email_manager_instruction = """
    You are an expert email manager. Your task is to help the user manage their email, inlcuding searching and sending emails.
    You will ask the user for all the necessary information to search for emails or send emails.
    Be professional, concise, and user-friendly. Ensure your final response follows the exact format for automated parsing.
    """
    email_manager_agent = create_react_agent(
        llm,
        tools=tools,
        prompt=email_manager_instruction,
    )
    
    print("state['messages']: ", state['messages'])
    result = email_manager_agent.invoke(state)
    
    # check for tool calls, if tool call, then goto end else goto human node
    llm_message = result["messages"][-1]
    if isinstance(llm_message, ToolMessage):
        return Command(update={"messages": result["messages"]}, goto="__end__")
    else:
        return Command(update={"messages": result["messages"]}, goto="human_node")
    

    