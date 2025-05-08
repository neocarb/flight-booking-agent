from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from wwc.workers.email_agent.agent import email_agent
from wwc.workers.flight_agents.flight_booking_agent.agent import flight_booking_agent

model = ChatOpenAI(model="gpt-4o")
# Create supervisor workflow
workflow = create_supervisor(
    agents=[email_agent, flight_booking_agent],
    model=model,
    prompt=(
        "You are a team supervisor managing a flight_booking_graph and email_manager_graph as tools"
        "For anything related to flight booking, use flight_booking_agent tool"
        "For anything related to email, use email_agent tool"
    ),
    output_mode="last_message"
)

# Compile and run
supervisor_agent = workflow.compile(name="supervisor_agent")