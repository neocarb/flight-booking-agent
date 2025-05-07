from langgraph.graph import StateGraph, START
from wwc.workers.email_agent.utils.state import EmailManagerState
from wwc.workers.email_agent.utils.nodes import email_manager_node, email_human_node

email_agent_builder = StateGraph(EmailManagerState)
email_agent_builder.add_node("email_manager_node", email_manager_node)
email_agent_builder.add_node("email_human_node", email_human_node)
email_agent_builder.add_edge(START, "email_manager_node")

# checkpointer = MemorySaver()
email_agent = email_agent_builder.compile(name="email_agent")