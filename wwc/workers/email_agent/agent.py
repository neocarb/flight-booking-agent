from langgraph.graph import StateGraph, START, END
from wwc.workers.email_agent.utils.state import EmailManagerState
from wwc.workers.email_agent.utils.nodes import email_agent_node
from langgraph.checkpoint.memory import MemorySaver

email_agent_builder = StateGraph(EmailManagerState)
email_agent_builder.add_node("email_agent_node", email_agent_node)
email_agent_builder.add_edge(START, "email_agent_node")
email_agent_builder.add_edge("email_agent_node", END)

checkpointer = MemorySaver()
email_agent = email_agent_builder.compile(checkpointer=checkpointer, name="email_agent")