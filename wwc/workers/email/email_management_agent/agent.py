from typing import TypedDict, Literal

from langgraph.graph import StateGraph, START, END
from email_management_agent.utils.state import EmailManagerState
from email_management_agent.utils.nodes import email_manager_node, email_human_node

email_manager_builder = StateGraph(EmailManagerState)
email_manager_builder.add_node("email_manager_node", email_manager_node)
email_manager_builder.add_node("email_human_node", email_human_node)
email_manager_builder.add_edge(START, "email_manager_node")

# checkpointer = MemorySaver()
graph = email_manager_builder.compile()