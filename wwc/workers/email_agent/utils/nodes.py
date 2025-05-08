from typing import Literal
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt

from wwc.workers.email_agent.utils.state import EmailManagerState
from wwc.workers.email_agent.utils.tools import tools
from wwc.workers.email_agent.utils.tools import get_user_input

llm = ChatOpenAI(model="gpt-4o")

# # human node
# def email_human_node(state: EmailManagerState) -> Command[Literal["email_manager_node"]]:
#     # get user input
#     user_input = interrupt("Enter your input: ")
#     # return user input
#     return Command(update={"messages": [HumanMessage(content=user_input)]}, goto="email_manager_node")

def email_agent_node(state: EmailManagerState):
    email_manager_instruction = """
    You are an expert email manager. Your task is to help the user manage their email.
    1. If you need any additional information to follow the instructioins, use the get_user_input tool to ask the user.
    Be professional, concise, and user-friendly. Ensure your final response follows the exact format for automated parsing.
    """
    email_manager_agent = create_react_agent(
        llm,
        tools=tools + [get_user_input],
        prompt=email_manager_instruction,
    )
    
    print("state['messages']: ", state['messages'])
    result = email_manager_agent.invoke({"messages": state['messages']})
    print("result: ", result)
    return Command(update={"messages": result["messages"]}, goto="__end__")