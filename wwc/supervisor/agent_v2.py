from typing import Annotated
from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from wwc.workers.email_agent.agent import email_agent
from wwc.workers.flight_agents.flight_booking_agent.agent import flight_booking_agent
from langchain_core.tools import tool
from langgraph.graph import MessagesState
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from langgraph.types import Send
import logging

logger = logging.getLogger(__name__)
METADATA_KEY_HANDOFF_DESTINATION = "__handoff_destination"

# define custom handoff tool
def create_task_description_handoff_tool(
    *, agent_name: str, description: str | None = None
):
    name = f"transfer_to_{agent_name}"
    description = description or f"Ask {agent_name} for help."

    @tool(name, description=description)
    def handoff_tool(
        # this is populated by the supervisor LLM
        task_description: Annotated[
            str,
            "Description of what the next agent should do, including all of the relevant context.",
        ],
        # these parameters are ignored by the LLM
        state: Annotated[MessagesState, InjectedState],
    ) -> Command:
        task_description_message = {"role": "user", "content": task_description}
        agent_input = {**state, "messages": [task_description_message]}
        logger.info("agent_input: %s", agent_input)
        return Command(
            goto=[Send(agent_name, agent_input)],
            graph=Command.PARENT,
        )
    
    handoff_tool.metadata = {METADATA_KEY_HANDOFF_DESTINATION: agent_name}
    return handoff_tool


model = ChatOpenAI(model="gpt-4o")
# Create supervisor workflow
workflow_v2 = create_supervisor(
    agents=[email_agent, flight_booking_agent],
    tools=[
        create_task_description_handoff_tool(agent_name="email_agent"), 
        create_task_description_handoff_tool(agent_name="flight_booking_agent")
        ],
    model=model,
    prompt=(
        "You are a team supervisor managing a flight_booking_graph and email_manager_graph as tools"
        "For anything related to flight booking, use flight_booking_agent tool"
        "For anything related to email, use email_agent tool"
    ),
    output_mode="full_history"
)

# Compile and run
supervisor_agent_v2 = workflow_v2.compile(name="supervisor_agent_v2")