from typing import Literal
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt

from email_management_agent.utils.state import EmailManagerState
from email_management_agent.utils.tools import tools

llm = ChatOpenAI(model="gpt-4o")

# human node
def email_human_node(state: EmailManagerState) -> Command[Literal["email_manager_node"]]:
    # get user input
    user_input = interrupt("Enter your input: ")
    # return user input
    return Command(update={"messages": [HumanMessage(content=user_input)]}, goto="email_manager_node")

def email_manager_node(state: EmailManagerState) -> Command[Literal["__end__", "email_human_node"]]:
    email_manager_instruction = """
    You are an expert email manager. Your task is to help the user manage their email.
    1. If you need any additional information to proceed with the tool use, prefix your message with `INPUT:` and ask the user.
    - Example:  
        INPUT: Please provide the subject of the email
    Be professional, concise, and user-friendly. Ensure your final response follows the exact format for automated parsing.
    """
    email_manager_agent = create_react_agent(
        llm,
        tools=[tools[1], tools[2], tools[3]],
        prompt=email_manager_instruction
    )
    
    result = email_manager_agent.invoke({"messages": state['messages']})
    llm_message = result["messages"][-1]
    
    if "INPUT" in llm_message.content:
            command = Command(update={"messages": [llm_message]}, goto="email_human_node")
            return command
        
    return Command(update={"messages": result["messages"]}, goto="__end__")