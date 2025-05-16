from langchain_core.messages import BaseMessage
import logging

from typing import List, Optional, Literal
from langchain_core.language_models.chat_models import BaseChatModel

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, trim_messages, AIMessage
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from wwc.workers.email_agent.agent import email_agent
from wwc.workers.flight_agents.flight_booking_agent.agent import flight_booking_agent

logger = logging.getLogger(__name__)

class State(MessagesState):
    next: str

def make_supervisor_node(llm: BaseChatModel, members: list[str]) -> str:
    options = ["FINISH"] + members
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        f" following workers: {members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
    )

    class Router(TypedDict):
        """Worker to route to next. If no workers needed, route to FINISH."""

        next: Literal[*options]

    def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
        """An LLM-based router."""
        messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
        response = llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            goto = END

        return Command(goto=goto, update={"next": goto})

    return supervisor_node

llm = ChatOpenAI(model="gpt-4o")
teams_supervisor_node = make_supervisor_node(llm, ["email_team", "flight_booking_team"])

def call_email_team(state: State) -> Command[Literal["supervisor"]]:
    response = email_agent.invoke({"messages": state["messages"][-1]})
    logger.info("response: %s", response)
    return Command(
        update={
            "messages": [response["messages"]]
        },
        goto="supervisor",
    )

def call_flight_booking_team(state: State) -> Command[Literal["supervisor"]]:
    response = flight_booking_agent.invoke({"messages": state["messages"][-1]})
    return Command(
        update={
            "messages": [
                AIMessage(
                    content=response["messages"][-1].content, name="flight_booking_team"
                )
            ]
        },
        goto="supervisor",
    )


# Define the graph.
super_builder = StateGraph(State)
super_builder.add_node("supervisor", teams_supervisor_node)
super_builder.add_node("email_team", call_email_team)
super_builder.add_node("flight_booking_team", call_flight_booking_team)

super_builder.add_edge(START, "supervisor")
supervisor_agent_v3 = super_builder.compile(name="supervisor_agent_v3")