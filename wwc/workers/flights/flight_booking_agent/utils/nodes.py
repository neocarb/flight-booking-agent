from langchain_openai import ChatOpenAI
from flight_booking_agent.utils.state import FlightBookingState
from langgraph.types import interrupt
from langgraph.prebuilt import create_react_agent
from flight_booking_agent.utils.tools import search_offers, confirm_offer
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage,ToolMessage

llm = ChatOpenAI(model="gpt-4o")

def human_node(state: FlightBookingState):
    # get user input
    user_input = interrupt("Enter your input: ")


def search_flight_offers_node(state: FlightBookingState):
    search_flight_offers_instruction = """
    You are a helpful and knowledgeable flight booking assistant. Your goal is to help the user search for flights and select a final option based on their travel preferences.
    Follow these rules strictly:
    1. Use the prefix `INPUT:` when asking the user for missing information or confirming preferences.
    - Examples:  
        INPUT: What is your destination city?  
        INPUT: Do you have a preferred time or airline?
    2. After collecting all preferences, provide suitable flight options. Assist the user in comparing and selecting one.
    3. Once the user confirms their choice, finalize the conversation using the prefix `FINAL:` followed by the selected flight ID in this format: FINAL: FLIGHT ID: <id>
    4. You can use 'FINAL' if the user wants to exit the conversation.
    5. Do not use `INPUT:` after you've already issued a `FINAL:` response.
    Keep your tone helpful, professional, and concise. If any information is ambiguous, ask clarifying questions. Ensure the final response is uses the given format.
    """
    search_flight_offers_agent = create_react_agent(
        llm,
        tools=[search_offers],
        prompt=search_flight_offers_instruction
    )
    
    result = search_flight_offers_agent.invoke(state)
    ai_message = AIMessage(content=result["messages"][-1], name="flight_search_agent")
    state['messages'].append(ai_message)
    return state


# make this node more deterministic gradually
def confirm_flight_offer_node(state: FlightBookingState):
    # This node is responsible for confirming the flight offer selected by the user.
    # It will extract the flight ID from the user's response and update the state accordingly.
    
    # Extracting the flight ID from the user's response
    # add message by AI asking for users preference of offet to book
    # Redirect to human_node
    # process the user response to get the selected offer id - LLM
    # verify the offer
    # return the offer and ask for confirmation
    
    confirm_flight_offer_instruction = """
    You goal is to get the user to confirm their selected flight offer.
    1. If the user has already provided a offer ID, confirm it using the confirm_order tool. If any of the details of the offer has changed, inform the user and ask them to confirm the new offer.
    2. If the user has not provided a offer ID, ask them to choose a flight offer to proceed with.
    """
    
    confirm_flight_offer_agent = create_react_agent(
        llm,
        tools=[confirm_offer],
        prompt=confirm_flight_offer_instruction
    )
    
    result = confirm_flight_offer_agent.invoke(state)
    ai_message = AIMessage(content=result["messages"][-1], name="flight_confirm_agent")
    state['messages'].append(ai_message)
    return state
    
        

    
    
    
    
    
    
