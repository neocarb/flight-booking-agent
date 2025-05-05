from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor

model = ChatOpenAI(model="gpt-4o")
# Create supervisor workflow
workflow = create_supervisor(
    model=model,
    prompt=(
        "You are a team supervisor managing a flight_booking_graph and email_manager_graph as tools"
        "For anything related to flight booking, use flight_booking_graph tool"
        "For anything related to email, use email_management_graph tool"
    ),
    output_mode="full_history"
)

# Compile and run
supervisor_graph = workflow.compile(name="supervisor_graph")